# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_convencion_cabeceras.py — Convención de autoría (K-008).

Todo archivo de código del repo viaja con su procedencia: una cabecera
con el nombre del autor. Cuando un archivo sale del repo (un reporte,
un anexo, un fork), el ledger no viaja con él pero la cabecera sí.
El test recorre el repo y falla si algún archivo de código nace sin ella.
"""
import pathlib
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MARCA = "Creado por Martín José Dalberto"
EXT = {".py", ".js", ".css", ".html"}


class TestCabeceras(unittest.TestCase):
    def archivos_de_codigo(self):
        for ruta in sorted(RAIZ.rglob("*")):
            if not ruta.is_file() or ruta.suffix not in EXT:
                continue
            if ".git" in ruta.parts:
                continue
            yield ruta

    def test_todo_codigo_tiene_cabecera_de_autoria(self):
        faltantes = []
        for ruta in self.archivos_de_codigo():
            head = ruta.read_text(encoding="utf-8", errors="replace").splitlines()[:6]
            if not any(MARCA in linea for linea in head):
                faltantes.append(str(ruta.relative_to(RAIZ)))
        self.assertEqual(faltantes, [], f"Sin cabecera de autoría: {faltantes}")

    def test_cabecera_python_no_rompe_shebang_ni_docstring(self):
        for ruta in sorted((RAIZ / "scripts").rglob("*.py")):
            lineas = ruta.read_text(encoding="utf-8").splitlines()
            if lineas and lineas[0].startswith("#!"):
                self.assertIn(MARCA, lineas[1], f"{ruta.name}: la cabecera va justo después del shebang")
            else:
                self.assertIn(MARCA, lineas[0], f"{ruta.name}: la cabecera es la primera línea")


if __name__ == "__main__":
    unittest.main(verbosity=2)
