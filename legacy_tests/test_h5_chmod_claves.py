# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_h5_chmod_claves.py — La clave privada debe tener permisos 600.

La ceremonia de claves debe fijar permisos 600 (solo lectura para el dueño)
en la clave privada, no depender del umask del sistema.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


class TestChmodClaves(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_h5_"))
        (self.tmp / "scripts").mkdir()
        for s in ["firma.py"]:
            shutil.copy(SCRIPTS_DIR / s, self.tmp / "scripts" / s)
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = str(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clave_privada_tiene_permisos_600(self):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "firma.py"), "ceremonia"],
            capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ruta_priv = self.tmp / "data" / "claves" / "sofia_privada.pem"
        self.assertTrue(ruta_priv.exists())
        permisos = oct(ruta_priv.stat().st_mode)[-3:]
        self.assertEqual(permisos, "600", f"Permisos {permisos}, esperado 600")


if __name__ == "__main__":
    unittest.main(verbosity=2)
