# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_auditar_main_proyecto.py — A1 parte 2: main() usa la bitácora correcta.

Verifica que al ejecutar auditar.py --proyecto N, el manifiesto refleje
la bitácora del proyecto N, no la del proyecto 1 (que es el default al importar).
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
_TMP_ROOT = tempfile.mkdtemp(prefix="sttm_a1_main_")
os.environ["STTM_ROOT"] = _TMP_ROOT
os.environ["STTM_PROYECTO"] = "1"  # default al importar

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Importar auditar después de setear STTM_ROOT
import auditar
import rutas


class TestMainProyecto(unittest.TestCase):
    def setUp(self):
        self.raiz = Path(_TMP_ROOT)
        # Crear catálogo con dos proyectos
        cat = self.raiz / "data" / "proyectos.jsonl"
        cat.parent.mkdir(parents=True, exist_ok=True)
        cat.write_text(
            json.dumps({"n": 1, "ref_interna": "STTM", "accion": "crear"}) + "\n"
            + json.dumps({"n": 2, "ref_interna": "DEMO", "accion": "crear"}) + "\n",
            encoding="utf-8"
        )
        # Crear carpetas de proyecto con bitácoras distintas
        self.bit1 = rutas.bitacora_de(1)
        self.bit2 = rutas.bitacora_de(2)
        self.bit1.parent.mkdir(parents=True, exist_ok=True)
        self.bit2.parent.mkdir(parents=True, exist_ok=True)
        self.bit1.write_text("contenido proyecto 1", encoding="utf-8")
        self.bit2.write_text("contenido proyecto 2", encoding="utf-8")
        # Crear auditorias/
        (self.raiz / "auditorias").mkdir(exist_ok=True)

    def tearDown(self):
        # Limpiar las carpetas de proyecto pero no el tmp root
        for n in [1, 2]:
            carp = rutas.carpeta_de(n)
            if carp.exists():
                shutil.rmtree(carp)
        for carp in (self.raiz / "auditorias").iterdir():
            if carp.is_dir():
                shutil.rmtree(carp)

    def test_main_usa_bitacora_del_proyecto_solicitado(self):
        """main() con --proyecto 2 debe hashear la bitácora del proyecto 2."""
        # Ejecutar main() con args parseados
        sys.argv = ["auditar.py", "--proyecto", "2", "--tipo", "rapida"]
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--proyecto", type=int, default=1)
        parser.add_argument("--motivo", default="Test")
        parser.add_argument("--tipo", choices=("rapida", "estandar", "profunda"), default="rapida")
        args = parser.parse_args(sys.argv[1:])

        # Llamar main() con args (simulando la ejecución)
        # Pero main() parsea sys.argv de nuevo, así que lo llamamos directamente
        # con el parser ya parseado. Alternativa: ejecutar como subprocess.
        # Más simple: llamar main() y dejar que parsee sys.argv.
        rc = auditar.main()
        # El return code puede ser 0 o 1 (depende de si hay rojos), no importa.

        # Encontrar la carpeta de auditoría creada
        auds = sorted((self.raiz / "auditorias").iterdir(), reverse=True)
        self.assertTrue(auds, "Debe haberse creado al menos una carpeta de auditoría")
        carpeta = auds[0]

        # Leer el manifiesto y verificar el hash de la bitácora
        man = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
        hash_esperado = hashlib.sha256(b"contenido proyecto 2").hexdigest()
        self.assertEqual(man["bitacora_sha256"], hash_esperado,
                         "El manifiesto debe reflejar la bitácora del proyecto 2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
