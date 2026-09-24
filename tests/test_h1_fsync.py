# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_h1_fsync.py — El registro debe ser durable ante cortes.

Después de escribir, registrar.py debe hacer flush() + os.fsync() para
que la línea esté en disco antes de que el proceso termine. Sin fsync,
un kill del sistema puede dejar la línea truncada.
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


class TestFsync(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_h1_"))
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

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_registro_durable_inmediatamente(self):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "registrar.py"),
             "Título", "Detalle", "--modo-firma", "hash"],
            capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # Verificar inmediatamente (sin esperar flush del OS)
        bit = self.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        lineas = bit.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 1)
        entrada = json.loads(lineas[0])
        self.assertEqual(entrada["n"], 1)
        self.assertEqual(entrada["titulo"], "Título")


if __name__ == "__main__":
    unittest.main(verbosity=2)
