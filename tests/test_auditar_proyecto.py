# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_auditar_proyecto.py — A1: la auditoría debe reflejar el proyecto solicitado.

Verifica que escribir_manifiesto() use la bitácora explícita que se le pasa,
no la constante importada al arrancar (que podía apuntar a otro proyecto).
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Fijar STTM_ROOT a un temporal ANTES de importar auditar, para que el
# import de rutas no toque el repo real.
_TMP_ROOT = tempfile.mkdtemp(prefix="sttm_a1_root_")
os.environ["STTM_ROOT"] = _TMP_ROOT

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import auditar


class TestManifiestoProyecto(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_a1_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_manifiesto_usa_bitacora_explicita(self):
        """El manifiesto debe hashear la bitácora que se le pasa, no otra."""
        bit1 = self.tmp / "bit1.jsonl"
        bit2 = self.tmp / "bit2.jsonl"
        bit1.write_text("contenido proyecto 1", encoding="utf-8")
        bit2.write_text("contenido proyecto 2", encoding="utf-8")

        carpeta = self.tmp / "auditoria"
        carpeta.mkdir()

        # Se pide auditar la bitácora 2 explícitamente.
        auditar.escribir_manifiesto(carpeta, bit2)

        man = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
        esperado = hashlib.sha256(b"contenido proyecto 2").hexdigest()
        self.assertEqual(man["bitacora_sha256"], esperado)

    def test_manifiesto_bitacora_inexistente_da_none(self):
        """Si la bitácora no existe, el hash queda en None (no explota)."""
        carpeta = self.tmp / "auditoria"
        carpeta.mkdir()
        ruta_inexistente = self.tmp / "no_existe.jsonl"

        auditar.escribir_manifiesto(carpeta, ruta_inexistente)

        man = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
        self.assertIsNone(man["bitacora_sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
