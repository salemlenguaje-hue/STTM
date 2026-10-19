# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_salud_input.py — Salud de input del endpoint de registro.

Nace de una prueba manual del autor (2026-09-23): registrar una entrada
copiando el texto de otra entrada, con saltos de línea, comillas y
caracteres especiales. Acá queda automatizado para que nadie tenga que
volver a hacerlo a mano.

Cubre: campos vacíos rechazados, texto hostil con round-trip idéntico
(lo que entra es lo que sale), detalle grande aceptado (sin límite
declarado hoy), y cadena íntegra después de todo eso.
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


class TestSaludInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_input_"))
        for c in ["scripts", "web", "auditorias", "data/proyectos/1-STTM"]:
            (cls.tmp / c).mkdir(parents=True)
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "STTM", "titulo": "Test",
                        "descripcion": "sandbox", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "continuidad", "nivel_actual": "continuidad",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "verificar.py", "firma.py",
                  "proyectos.py", "auditoria_meta.py", "auditar.py", "servidor.py"]:
            shutil.copy(SCRIPTS_DIR / s, cls.tmp / "scripts" / s)
        cls.port = puerto_libre()
        env = os.environ.copy()
        env["STTM_ROOT"] = str(cls.tmp)
        env["STTM_PORT"] = str(cls.port)
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.base = f"http://127.0.0.1:{cls.port}"
        for _ in range(40):
            try:
                cls.get(cls, "/api/bitacora")
                return
            except Exception:
                time.sleep(0.25)
        cls.proc.terminate()
        raise RuntimeError("el servidor no arranco")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return r.status, r.read().decode("utf-8")

    def post(self, datos):
        req = urllib.request.Request(
            self.base + "/api/registrar",
            data=json.dumps(datos).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def registrar(self, titulo, detalle, **extra):
        datos = {"titulo": titulo, "detalle": detalle, "modo_firma": "hash"}
        datos.update(extra)
        return self.post(datos)

    def bitacora(self):
        status, cuerpo = self.get("/api/bitacora")
        self.assertEqual(status, 200)
        return json.loads(cuerpo)

    # --- rechazos ---
    def test_titulo_vacio_rechazado(self):
        status, res = self.registrar("", "detalle")
        self.assertEqual(status, 400, res)

    def test_detalle_vacio_rechazado(self):
        status, res = self.registrar("titulo", "")
        self.assertEqual(status, 400, res)

    def test_titulo_solo_espacios_rechazado(self):
        status, res = self.registrar("   ", "detalle")
        self.assertEqual(status, 400, res)

    def test_modo_firma_invalido_rechazado(self):
        status, res = self.registrar("t", "d", modo_firma="magia")
        self.assertEqual(status, 400, res)

    def test_proyecto_no_numerico_rechazado(self):
        status, res = self.registrar("t", "d", proyecto="abc")
        self.assertEqual(status, 400, res)

    # --- round-trip: lo que entra es lo que sale ---
    def test_texto_hostil_round_trip_identico(self):
        """El caso manual del autor: texto copiado de otra entrada."""
        texto = ('Línea con "comillas dobles", \'simples\', `backticks` y \\ barras.\n'
                 'Segunda línea con emoji 🟡✅ y tab\t separador.\n'
                 'Tercera: hash 0123456789abcdef y fin.')
        status, res = self.registrar("Titulo con \"comillas\" y 'apóstrofe'", texto)
        self.assertEqual(status, 200, res)
        self.assertTrue(res["ok"], res)
        entradas = self.bitacora()
        self.assertEqual(entradas[0]["detalle"], texto)
        self.assertEqual(entradas[0]["titulo"], "Titulo con \"comillas\" y 'apóstrofe'")

    def test_detalle_grande_aceptado_sin_limite_declarado(self):
        grande = "a" * 50000
        status, res = self.registrar("detalle grande", grande)
        self.assertEqual(status, 200, res)
        self.assertTrue(res["ok"], res)
        self.assertEqual(self.bitacora()[0]["detalle"], grande)

    # --- la cadena sobrevive a todo lo anterior ---
    def test_cadena_integra_tras_inputs_hostiles(self):
        # No depende del orden alfabético de los tests: se asegura
        # su propia entrada antes de verificar la cadena.
        status, res = self.registrar("hito de cadena", "detalle para asegurar bitacora")
        self.assertEqual(status, 200, res)
        env = os.environ.copy()
        env["STTM_ROOT"] = str(self.tmp)
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "verificar.py")],
            capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("Cadena íntegra", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
