# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_proyectos_ref.py — P3+P4: la CLI debe validar la ref como el servidor.

P3: una ref con caracteres de path (../) o inválidos debe rechazarse.
P4: una ref duplicada debe rechazarse (evita colisión de carpetas en rutas.py).
"""
import argparse
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Fijar STTM_ROOT a un temporal ANTES de importar proyectos, para no tocar el repo real.
_TMP_ROOT = tempfile.mkdtemp(prefix="sttm_p34_root_")
os.environ["STTM_ROOT"] = _TMP_ROOT

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import proyectos


def _crear(titulo, ref, nivel="simple"):
    """Helper: ejecuta cmd_crear capturando stdout, devuelve return code."""
    args = argparse.Namespace(titulo=titulo, descripcion="D", ref=ref, nivel=nivel)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = proyectos.cmd_crear(args)
    return rc


class TestCrearRef(unittest.TestCase):
    def setUp(self):
        # Limpiar el catálogo para cada test.
        if proyectos.CATALOGO.exists():
            proyectos.CATALOGO.unlink()

    def test_ref_con_path_traversal_rechazada(self):
        """P3: una ref con ../ debe rechazarse (riesgo de path traversal)."""
        rc = _crear("T", "../../etc")
        self.assertEqual(rc, 1)
        self.assertEqual(proyectos.leer_lineas(), [])

    def test_ref_con_espacios_rechazada(self):
        """P3: una ref con espacios o minúsculas fuera de patrón se rechaza."""
        rc = _crear("T", "con espacios")
        self.assertEqual(rc, 1)
        self.assertEqual(proyectos.leer_lineas(), [])

    def test_ref_demasiado_larga_rechazada(self):
        """P3: una ref de más de 16 caracteres se rechaza."""
        rc = _crear("T", "A" * 17)
        self.assertEqual(rc, 1)
        self.assertEqual(proyectos.leer_lineas(), [])

    def test_ref_valida_aceptada_y_normalizada(self):
        """P3: una ref válida se acepta y se normaliza a mayúsculas."""
        rc = _crear("T", "demo")
        self.assertEqual(rc, 0)
        estado = proyectos.cargar_estado()
        self.assertEqual(len(estado), 1)
        self.assertEqual(list(estado.values())[0]["ref_interna"], "DEMO")

    def test_ref_duplicada_rechazada(self):
        """P4: crear dos proyectos con la misma ref debe fallar el segundo."""
        rc1 = _crear("T1", "DEMO")
        self.assertEqual(rc1, 0)
        rc2 = _crear("T2", "DEMO")
        self.assertEqual(rc2, 1)
        estado = proyectos.cargar_estado()
        self.assertEqual(len(estado), 1)  # solo el primero creado

    def test_ref_none_se_acepta(self):
        """Una ref ausente (None) se acepta, preservando el comportamiento actual."""
        args = argparse.Namespace(titulo="T", descripcion="D", ref=None, nivel="simple")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = proyectos.cmd_crear(args)
        self.assertEqual(rc, 0)
        estado = proyectos.cargar_estado()
        self.assertEqual(len(estado), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
