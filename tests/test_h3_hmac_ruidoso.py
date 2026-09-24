# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_h3_hmac_ruidoso.py — HMAC sin variable de entorno debe fallar.

Si STTM_HMAC_KEY no está seteada, registrar.py firma con una clave por
defecto escrita en el código, y nadie avisa. Eso miente sobre la fuerza
de la firma. El fix hace que falle ruidosamente.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


class TestHmacRuidoso(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_h3_"))
        (self.tmp / "scripts").mkdir()
        (self.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (self.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "STTM", "titulo": "T",
                        "descripcion": "d", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "simple", "nivel_actual": "simple",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")
        (self.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "firma.py"]:
            shutil.copy(SCRIPTS_DIR / s, self.tmp / "scripts" / s)
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = str(self.tmp)
        # Asegurar que STTM_HMAC_KEY no esté seteada
        self.env.pop("STTM_HMAC_KEY", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hmac_sin_variable_de_entorno_falla_ruidosamente(self):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "registrar.py"),
             "Título", "Detalle", "--modo-firma", "hmac"],
            capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hmac", r.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
