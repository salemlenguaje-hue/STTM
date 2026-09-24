# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_sttm.py — Suite de tests black-box para STTM.
Aislamiento de entornos temporales para no contaminar la bitácora real.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

class STTMTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sttm_test_")
        self.raiz = Path(self.tmpdir)
        (self.raiz / "scripts").mkdir()
        (self.raiz / "auditorias").mkdir()
        (self.raiz / "data" / "proyectos" / "1-STTM").mkdir(parents=True, exist_ok=True)
        (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        
        for script in ["rutas.py", "registrar.py", "verificar.py", "auditar.py", "firma.py", "proyectos.py", "auditoria_meta.py"]:
            dst = self.raiz / "scripts" / script
            dst.write_text((SCRIPTS_DIR / script).read_text(encoding="utf-8"), encoding="utf-8")
        
        self.entorno = os.environ.copy()
        self.entorno["STTM_ROOT"] = str(self.raiz)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def correr_script(self, nombre, *args):
        script = self.raiz / "scripts" / nombre
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True, text=True, env=self.entorno
        )

class TestRegistrar(STTMTestCase):
    def test_primer_registro(self):
        r = self.correr_script("registrar.py", "Hito 1", "Test")
        self.assertEqual(r.returncode, 0)
        e = json.loads((self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").read_text().splitlines()[0])
        self.assertEqual(e["hash_prev"], "0" * 64)

    def test_encadenamiento(self):
        self.correr_script("registrar.py", "Hito 1", "Test")
        self.correr_script("registrar.py", "Hito 2", "Test")
        lineas = (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").read_text().splitlines()
        e1, e2 = json.loads(lineas[0]), json.loads(lineas[1])
        self.assertEqual(e2["hash_prev"], e1["hash"])

class TestVerificar(STTMTestCase):
    def test_integridad_ok(self):
        self.correr_script("registrar.py", "Hito 1", "Test")
        r = self.correr_script("verificar.py")
        self.assertEqual(r.returncode, 0)
        self.assertIn("íntegra", r.stdout.lower())

    def test_detecta_alteracion(self):
        self.correr_script("registrar.py", "Hito 1", "Original")
        bitacora = self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        bitacora.write_text(bitacora.read_text().replace("Original", "Hackeado"))
        r = self.correr_script("verificar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("alterado", r.stdout.lower())

class TestAuditar(STTMTestCase):
    def test_auditoria_limpia(self):
        self.correr_script("registrar.py", "Hito", "Test")
        r = self.correr_script("auditar.py")
        self.assertEqual(r.returncode, 0)
        self.assertIn("limpio", r.stdout.lower())

    def test_detecta_pem(self):
        self.correr_script("registrar.py", "Hito", "Test")
        (self.raiz / "clave.pem").write_text("basura")
        r = self.correr_script("auditar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ARCHIVO SENSIBLE", r.stdout)

    def test_no_falso_positivo(self):
        """El propio auditar.py no debe flagearse a sí mismo."""
        self.correr_script("registrar.py", "Hito", "Test")
        r = self.correr_script("auditar.py")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("auditar.py", r.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
