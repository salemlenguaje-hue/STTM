# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_proyectos_robustez.py — P1+P2: robustez y durabilidad del catálogo.

P1: una línea corrupta no debe romper todo el catálogo (se saltea con aviso).
P2: agregar() debe forzar a disco (fsync) para durabilidad ante corte de energía.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Fijar STTM_ROOT a un temporal ANTES de importar proyectos.
_TMP_ROOT = tempfile.mkdtemp(prefix="sttm_p12_root_")
os.environ["STTM_ROOT"] = _TMP_ROOT

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import proyectos


class TestCatalogoRobustez(unittest.TestCase):
    def setUp(self):
        if proyectos.CATALOGO.exists():
            proyectos.CATALOGO.unlink()

    def test_linea_corrupta_no_rompe_catalogo(self):
        """P1: una línea JSON inválida se saltea, no rompe la lectura."""
        proyectos.CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        proyectos.CATALOGO.write_text(
            json.dumps({"n": 1, "ref_interna": "A", "titulo": "P1"}) + "\n"
            + "esta línea no es JSON válido\n"
            + json.dumps({"n": 2, "ref_interna": "B", "titulo": "P2"}) + "\n",
            encoding="utf-8"
        )
        lineas = proyectos.leer_lineas()
        self.assertEqual(len(lineas), 2)
        self.assertEqual(lineas[0]["n"], 1)
        self.assertEqual(lineas[1]["n"], 2)

    def test_cargar_estado_con_linea_corrupta(self):
        """P1: cargar_estado funciona aunque haya una línea corrupta."""
        proyectos.CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        proyectos.CATALOGO.write_text(
            json.dumps({"n": 1, "ref_interna": "A", "titulo": "P1"}) + "\n"
            + "{json roto\n"
            + json.dumps({"n": 2, "ref_interna": "B", "titulo": "P2"}) + "\n",
            encoding="utf-8"
        )
        estado = proyectos.cargar_estado()
        self.assertEqual(len(estado), 2)
        self.assertIn(1, estado)
        self.assertIn(2, estado)

    def test_agregar_llama_fsync(self):
        """P2: agregar() debe forzar a disco con fsync."""
        entrada = {"n": 1, "ref_interna": "A", "titulo": "P1"}
        with mock.patch.object(proyectos.os, "fsync") as mock_fsync:
            proyectos.agregar(entrada)
            mock_fsync.assert_called()

    def test_agregar_escribe_y_se_leer(self):
        """P2 (funcional): lo escrito por agregar() se puede leer de nuevo."""
        entrada = {"n": 1, "ref_interna": "A", "titulo": "P1"}
        proyectos.agregar(entrada)
        lineas = proyectos.leer_lineas()
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0]["ref_interna"], "A")


if __name__ == "__main__":
    unittest.main(verbosity=2)
