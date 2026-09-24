# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_k001_selector.py — Criterio de aceptación de K-001.

El catálogo con 2+ proyectos sirve bitácoras y auditorías aisladas por
proyecto a través de la API: lo que se registra en uno no aparece en el
otro, y los proyectos inexistentes fallan explícitos.

Arranque auto-diagnosticable: pre-sonda de socket, presupuesto amplio
(el import de cryptography en Termux es lento), y log del servidor
embebido en cualquier fallo de arranque para no volver a adivinar.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def proyecto(n, ref, titulo):
    return {"n": n, "ref_interna": ref, "titulo": titulo, "descripcion": "sandbox",
            "creado_utc": "2026-01-01T00:00:00Z", "nivel_inicial": "simple",
            "nivel_actual": "simple", "primera_auditoria_utc": None,
            "ultima_auditoria_utc": None, "activo": True}


class TestSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_k001_"))
        for c in ["scripts", "web", "auditorias",
                  "data/proyectos/1-STTM", "data/proyectos/2-DEMO"]:
            (cls.tmp / c).mkdir(parents=True)
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps(proyecto(1, "STTM", "Uno")) + "\n" +
            json.dumps(proyecto(2, "DEMO", "Dos")) + "\n", encoding="utf-8")
        for n in ["1-STTM", "2-DEMO"]:
            (cls.tmp / "data" / "proyectos" / n / "BITACORA.jsonl").write_text("", encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "verificar.py", "firma.py",
                  "proyectos.py", "auditoria_meta.py", "auditar.py", "servidor.py"]:
            shutil.copy(SCRIPTS_DIR / s, cls.tmp / "scripts" / s)

        cls.port = puerto_libre()
        env = os.environ.copy()
        env["STTM_ROOT"] = str(cls.tmp)
        env["STTM_PORT"] = str(cls.port)
        cls.log = cls.tmp / "servidor.log"
        cls._logfh = open(cls.log, "wb")
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=env, stdout=cls._logfh, stderr=cls._logfh)
        cls.base = f"http://127.0.0.1:{cls.port}"

        # Pre-sonda: que el puerto acepte conexiones (presupuesto 30 s).
        deadline = time.time() + 30
        while time.time() < deadline:
            if cls.proc.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=1):
                    pass
                break
            except OSError:
                time.sleep(0.25)

        # Sonda HTTP real.
        # Sonda con urlopen directo: a nivel de clase no se pueden usar
        # los helpers de instancia (self.get se mal-ataría al cls).
        ultimo = None
        for _ in range(20):
            try:
                with urllib.request.urlopen(cls.base + "/api/bitacora", timeout=5) as r:
                    json.loads(r.read().decode("utf-8"))
                return
            except Exception as e:
                ultimo = e
                time.sleep(0.25)
        cls._fallo_arranque(ultimo)

    @classmethod
    def _fallo_arranque(cls, ultimo):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except Exception:
            cls.proc.kill()
        cls._logfh.close()
        texto = cls.log.read_text(encoding="utf-8", errors="replace") if cls.log.exists() else ""
        raise RuntimeError(
            f"el servidor no arranco; ultimo error: {ultimo!r}\n"
            f"--- log del servidor ---\n{texto[-3000:]}")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except Exception:
            cls.proc.kill()
        cls._logfh.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---------- helpers ----------
    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=30) as r:
            return r.status, r.read().decode("utf-8")

    def get_json(self, path):
        status, cuerpo = self.get(path)
        self.assertEqual(status, 200, cuerpo)
        return json.loads(cuerpo)

    def post_json(self, path, datos):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(datos).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    # ---------- tests ----------
    def test_bitacoras_aisladas_por_proyecto(self):
        _, r1 = self.post_json("/api/registrar", {
            "proyecto": 1, "titulo": "Solo del uno", "detalle": "d1", "modo_firma": "hash"})
        self.assertTrue(r1["ok"], r1)
        _, r2 = self.post_json("/api/registrar", {
            "proyecto": 2, "titulo": "Solo del dos", "detalle": "d2", "modo_firma": "hash"})
        self.assertTrue(r2["ok"], r2)
        b1 = self.get_json("/api/bitacora?proyecto=1")
        b2 = self.get_json("/api/bitacora?proyecto=2")
        self.assertEqual([e["titulo"] for e in b1], ["Solo del uno"])
        self.assertEqual([e["titulo"] for e in b2], ["Solo del dos"])

    def test_proyecto_inexistente_falla_explicito(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get_json("/api/bitacora?proyecto=99")
        self.assertEqual(ctx.exception.code, 404)

    def test_registro_en_proyecto_inexistente_no_es_ok(self):
        status, res = self.post_json("/api/registrar", {
            "proyecto": 99, "titulo": "fantasma", "detalle": "d", "modo_firma": "hash"})
        self.assertEqual(status, 200)
        self.assertFalse(res["ok"], res)

    def test_auditorias_filtradas_por_proyecto(self):
        status, res = self.post_json("/api/auditar", {
            "proyecto": 2, "motivo": "auditoria del dos", "tipo": "rapida"})
        self.assertEqual(status, 200, res)
        a2 = self.get_json("/api/auditorias?proyecto=2")
        a1 = self.get_json("/api/auditorias?proyecto=1")
        self.assertTrue(any(a["carpeta"] == res["carpeta"] for a in a2))
        self.assertFalse(any(a["carpeta"] == res["carpeta"] for a in a1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
