"""
tests/test_privacidad.py — Regresión del incidente 002.

Cubre las tres clases de bug detectadas en vivo:
1. Prefijo pelado 'ghp_' matcheaba prosa que describe el patrón.
2. Archivo sensible en ubicación declarada y gitignoreada era rojo (leak)
   cuando es ámbar (ubicación controlada).
3. meta.json anunciaba manifiesto.json que no se escribía.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


class TestPrivacidad(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sttm_priv_")
        self.raiz = Path(self.tmpdir)
        (self.raiz / "scripts").mkdir()
        (self.raiz / "auditorias").mkdir()
        (self.raiz / "BITACORA.jsonl").write_text("", encoding="utf-8")
        for s in ["registrar.py", "verificar.py", "auditar.py",
                  "firma.py", "proyectos.py", "auditoria_meta.py"]:
            (self.raiz / "scripts" / s).write_text(
                (SCRIPTS_DIR / s).read_text(encoding="utf-8"), encoding="utf-8")
        self.entorno = os.environ.copy()
        self.entorno["STTM_ROOT"] = str(self.raiz)
        self.correr("registrar.py", "Hito", "Base")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def correr(self, nombre, *args):
        return subprocess.run(
            [sys.executable, str(self.raiz / "scripts" / nombre), *args],
            capture_output=True, text=True, env=self.entorno)

    def test_prosa_con_prefijo_no_es_token(self):
        """Incidente 002 caso 1: documentar el patrón no es tener el secreto."""
        (self.raiz / "docs.md").write_text(
            "El escaner detecta tokens ghp_ y claves .pem segun ADR-003.",
            encoding="utf-8")
        r = self.correr("auditar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("CONTENIDO SENSIBLE", r.stdout)

    def test_token_realista_si_es_rojo(self):
        (self.raiz / "datos.py").write_text(
            'TOKEN = "ghp_1234567890abcdef1234567890abcdef1234"', encoding="utf-8")
        r = self.correr("auditar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("CONTENIDO SENSIBLE", r.stdout)

    def test_sensible_gitignoreado_es_ambar(self):
        """Incidente 002 caso 2: cofre declarado = ámbar, no rojo."""
        (self.raiz / ".gitignore").write_text("*.pem\n", encoding="utf-8")
        (self.raiz / "clave.pem").write_text("cofre declarado", encoding="utf-8")
        r = self.correr("auditar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("UBICACION CONTROLADA", r.stdout)

    def test_sensible_sin_exclusion_es_rojo(self):
        (self.raiz / "clave.pem").write_text("clave tirada", encoding="utf-8")
        r = self.correr("auditar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("SIN EXCLUSION", r.stdout)

    def test_manifiesto_se_escribe(self):
        """Incidente 002 caso 3: lo anunciado debe existir."""
        r = self.correr("auditar.py")
        carpetas = list((self.raiz / "auditorias").iterdir())
        self.assertEqual(len(carpetas), 1)
        self.assertTrue((carpetas[0] / "manifiesto.json").exists())
        self.assertTrue((carpetas[0] / "meta.json").exists())
        self.assertTrue((carpetas[0] / "reporte.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
