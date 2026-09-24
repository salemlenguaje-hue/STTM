# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_cache_estaticos.py — PC-013: estáticos sin caché.

El navegador móvil servía app.js viejo tras un deploy y la UI nueva
parecía rota sin errores. El servidor debe decirle al navegador que
no cachee html, css ni js.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestCacheEstaticos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_cache_"))
        for c in ["scripts", "web", "auditorias", "data/proyectos/1-STTM"]:
            (cls.tmp / c).mkdir(parents=True)
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "web" / "app.js").write_text("// js", encoding="utf-8")
        (cls.tmp / "web" / "style.css").write_text("/* css */", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text("", encoding="utf-8")
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
        ultimo = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(cls.base + "/index.html", timeout=2):
                    return
            except Exception as e:
                ultimo = e
                time.sleep(0.25)
        cls.proc.terminate()
        cls._logfh.close()
        texto = cls.log.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(f"servidor no arranco: {ultimo!r}\n{texto[-2000:]}")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except Exception:
            cls.proc.kill()
        cls._logfh.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def cabecera(self, ruta):
        with urllib.request.urlopen(self.base + ruta, timeout=10) as r:
            self.assertEqual(r.status, 200)
            return r.headers.get("Cache-Control")

    def test_js_sin_cache(self):
        self.assertEqual(self.cabecera("/app.js"), "no-store")

    def test_css_sin_cache(self):
        self.assertEqual(self.cabecera("/style.css"), "no-store")

    def test_html_sin_cache(self):
        self.assertEqual(self.cabecera("/index.html"), "no-store")


if __name__ == "__main__":
    unittest.main(verbosity=2)
