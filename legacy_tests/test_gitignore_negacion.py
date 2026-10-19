# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_gitignore_negacion.py — A2: gitignore con negación y **

Verifica que cubierto_por_gitignore() maneja correctamente:
- Negación (!): excepciones que des-excluyen archivos
- **: wildcard de múltiples niveles de directorios
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import auditar


class TestGitignoreNegacion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_gitignore_"))
        self._old_root = auditar.RAIZ
        auditar.RAIZ = self.tmp
    
    def tearDown(self):
        auditar.RAIZ = self._old_root
        shutil.rmtree(self.tmp, ignore_errors=True)
    
    def test_negacion_des_excluye_archivo(self):
        """Un patrón con ! des-excluye un archivo previamente excluido."""
        (self.tmp / ".gitignore").write_text(
            "*.key\n"
            "!publica.key\n",
            encoding="utf-8"
        )
        pats = auditar.patrones_gitignore()
        
        # secreta.key está excluida por *.key
        ruta_secreta = self.tmp / "secreta.key"
        self.assertIsNotNone(auditar.cubierto_por_gitignore(ruta_secreta, pats))
        
        # publica.key está des-excluida por !publica.key
        ruta_publica = self.tmp / "publica.key"
        self.assertIsNone(auditar.cubierto_por_gitignore(ruta_publica, pats))
    
    def test_doble_asterisco_matchea_multiples_niveles(self):
        """El patrón ** matchea múltiples niveles de directorios."""
        (self.tmp / ".gitignore").write_text(
            "**/secreto.txt\n",
            encoding="utf-8"
        )
        pats = auditar.patrones_gitignore()
        
        # secreto.txt en raíz
        ruta1 = self.tmp / "secreto.txt"
        self.assertIsNotNone(auditar.cubierto_por_gitignore(ruta1, pats))
        
        # secreto.txt en subdirectorio
        (self.tmp / "docs").mkdir()
        ruta2 = self.tmp / "docs" / "secreto.txt"
        self.assertIsNotNone(auditar.cubierto_por_gitignore(ruta2, pats))
        
        # secreto.txt en sub-subdirectorio
        (self.tmp / "docs" / "profundo").mkdir(parents=True)
        ruta3 = self.tmp / "docs" / "profundo" / "secreto.txt"
        self.assertIsNotNone(auditar.cubierto_por_gitignore(ruta3, pats))


if __name__ == "__main__":
    unittest.main(verbosity=2)
