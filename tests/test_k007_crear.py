"""
tests/test_k007_crear.py — Creación de proyectos desde API (K-007).

Contrato (coherente con /api/registrar y test_servidor):
  - éxito            -> 200 con {"ok": true}
  - validación fallida -> 4xx con {"error": ...}
Cubre: creación correcta + presencia en catálogo, ref duplicada (409),
ref inválida (400), título vacío (400), y asiento en bitácora.
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


class TestCrearProyecto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_k007_"))
        for c in ["scripts", "web", "auditorias", "data/proyectos/1-STTM"]:
            (cls.tmp / c).mkdir(parents=True)
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps(proyecto(1, "STTM", "Uno")) + "\n", encoding="utf-8")
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
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
        deadline = time.time() + 30
        while time.time() < deadline:
            if cls.proc.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=1):
                    break
            except OSError:
                time.sleep(0.25)
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

    def get_json(self, path):
        with urllib.request.urlopen(self.base + path, timeout=30) as r:
            self.assertEqual(r.status, 200)
            return json.loads(r.read().decode("utf-8"))

    def post(self, path, datos):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(datos).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def test_creacion_correcta_y_catalogo(self):
        status, res = self.post("/api/proyecto/crear", {
            "titulo": "Proyecto dos", "ref": "DOS", "nivel": "simple",
            "descripcion": "segundo proyecto"})
        self.assertEqual(status, 200, res)
        self.assertTrue(res["ok"], res)
        # Independiente del orden: busco la ref en la lista de activos,
        # no por n fijo (otro test puede haber creado proyectos antes).
        data = self.get_json("/api/proyecto")
        refs = [pr["ref_interna"] for pr in data["activos"]]
        self.assertIn("DOS", refs)

    def test_ref_duplicada_409(self):
        status, _ = self.post("/api/proyecto/crear", {"titulo": "Tres", "ref": "TRES"})
        self.assertEqual(status, 200)
        status, res = self.post("/api/proyecto/crear", {"titulo": "Tres dup", "ref": "TRES"})
        self.assertEqual(status, 409, res)
        self.assertIn("ya existe", res["error"])

    def test_ref_invalida_400(self):
        status, res = self.post("/api/proyecto/crear", {"titulo": "Malo", "ref": "con-espacio"})
        self.assertEqual(status, 400, res)
        self.assertIn("invalida", res["error"])

    def test_titulo_vacio_400(self):
        status, res = self.post("/api/proyecto/crear", {"titulo": "", "ref": "CUATRO"})
        self.assertEqual(status, 400, res)
        self.assertIn("titulo", res["error"])

    def test_asiento_en_bitacora_tras_creacion(self):
        self.post("/api/proyecto/crear", {
            "titulo": "Proyecto cinco", "ref": "CINCO", "descripcion": "d"})
        entradas = self.get_json("/api/bitacora")
        titulos = [e["titulo"] for e in entradas]
        self.assertTrue(any("Proyecto creado: Proyecto cinco" in t for t in titulos),
                        f"no encuentro el asiento en {titulos}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
