# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_h4_forma_ultima.py — Última entrada sin forma debe dar mensaje humano.

Si la última entrada de la bitácora es JSON válido pero no tiene los campos
esperados (p.ej. alguien editó a mano), registrar.py debe fallar con un
mensaje claro, no con un traceback de KeyError.
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


class TestFormaUltima(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_h4_"))
        (self.tmp / "scripts").mkdir()
        (self.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (self.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "STTM", "titulo": "T",
                        "descripcion": "d", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "simple", "nivel_actual": "simple",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")
        # Bitácora con última línea JSON válida pero sin campos esperados
        (self.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            '{"esto": "es", "json": "valido", "pero": "no entrada"}\n',
            encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "firma.py"]:
            shutil.copy(SCRIPTS_DIR / s, self.tmp / "scripts" / s)
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = str(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ultima_sin_forma_da_mensaje_humano(self):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "registrar.py"),
             "Título", "Detalle", "--modo-firma", "hash"],
            capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        # Debe contener un mensaje humano, no un traceback crudo
        salida = r.stdout + r.stderr
        self.assertIn("última entrada", salida.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
