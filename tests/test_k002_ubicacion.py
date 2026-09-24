# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_k002_ubicacion.py — Paridad de la migración K-002.

Escrito ANTES de migrar: debe correr en ROJO contra el estado viejo
(bitácora en la raíz) y en VERDE después de la migración a
data/proyectos/1-STTM/BITACORA.jsonl (ADR-003 §3.2), sin tocar este archivo.

Qué verifica:
1. Que ningún script de producción hardcodee la bitácora en la raíz.
2. Que registrar escriba en la carpeta del proyecto y no deje raíz.
3. Que verificar lea desde la carpeta del proyecto.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
RUTA_ESPERADA_REL = Path("data") / "proyectos" / "1-STTM" / "BITACORA.jsonl"


class TestUbicacionBitacora(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_k002_"))
        (self.tmp / "scripts").mkdir()
        (self.tmp / "auditorias").mkdir()
        for s in ["rutas.py", "registrar.py", "verificar.py", "firma.py"]:
            origen = SCRIPTS_DIR / s
            if origen.exists():  # rutas.py no existe antes de la migración
                (self.tmp / "scripts" / s).write_text(
                    origen.read_text(encoding="utf-8"), encoding="utf-8")
        self.entorno = os.environ.copy()
        self.entorno["STTM_ROOT"] = str(self.tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def correr(self, nombre, *args):
        return subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / nombre), *args],
            capture_output=True, text=True, env=self.entorno)

    def test_01_scripts_sin_bitacora_hardcodeada_en_raiz(self):
        for nombre in ["registrar.py", "verificar.py", "servidor.py"]:
            texto = (SCRIPTS_DIR / nombre).read_text(encoding="utf-8")
            self.assertNotIn(
                'BITACORA = RAIZ / "BITACORA.jsonl"', texto,
                f"{nombre} sigue hardcodeando la bitacora en la raiz")

    def test_02_registrar_escribe_en_carpeta_de_proyecto(self):
        r = self.correr("registrar.py", "Hito K-002", "Detalle de prueba",
                        "--modo-firma", "hash")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.tmp / RUTA_ESPERADA_REL).exists(),
                        "la bitacora no quedo en data/proyectos/1-STTM/")
        self.assertFalse((self.tmp / "BITACORA.jsonl").exists(),
                         "queda bitacora en la raiz: debe ser unica en la carpeta del proyecto")

    def test_03_verificar_lee_desde_carpeta_de_proyecto(self):
        (self.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (self.tmp / RUTA_ESPERADA_REL).write_text("", encoding="utf-8")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nada que verificar", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
