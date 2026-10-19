# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_h2_guard_campos.py — Campos nuevos futuros quedan fuera del hash sin avisar.

Si alguien agrega un campo nuevo y olvida actualizar CAMPOS_BASE en firma.py,
ese campo queda mutable sin detección. El guard verifica que la entrada tenga
exactamente las claves esperadas antes de firmar.
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


class TestGuardCampos(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_h2_"))
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
        # Modificar firma.py para agregar un campo nuevo a CAMPOS_BASE
        f = self.tmp / "scripts" / "firma.py"
        t = f.read_text(encoding="utf-8")
        t = t.replace(
            'CAMPOS_BASE = ("n", "ts", "titulo", "detalle", "archivos",\n               "commit_ref", "firma_tipo", "hash_prev")',
            'CAMPOS_BASE = ("n", "ts", "titulo", "detalle", "archivos",\n               "commit_ref", "firma_tipo", "hash_prev", "campo_nuevo")'
        )
        f.write_text(t, encoding="utf-8")
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = str(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_campo_nuevo_sin_actualizar_base_rompe_el_registro(self):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "registrar.py"),
             "Título", "Detalle", "--modo-firma", "hash"],
            capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("campo", r.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
