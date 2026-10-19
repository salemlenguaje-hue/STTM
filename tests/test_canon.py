import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import canon  # noqa: E402


class TestCanonJCS(unittest.TestCase):

    def test_orden_de_claves(self):
        # RFC 8785 exige claves ordenadas; "a" < "b" < "c" en ASCII simple.
        d = {"c": 1, "a": 2, "b": 3}
        self.assertEqual(canon.canonicalizar(d), '{"a":2,"b":3,"c":1}')

    def test_sin_espacios(self):
        d = {"x": [1, 2, 3], "y": "z"}
        salida = canon.canonicalizar(d)
        self.assertNotIn(" ", salida)
        self.assertEqual(salida, '{"x":[1,2,3],"y":"z"}')

    def test_null_true_false(self):
        d = {"a": None, "b": True, "c": False}
        self.assertEqual(canon.canonicalizar(d), '{"a":null,"b":true,"c":false}')

    def test_enteros_negativos_y_cero(self):
        d = {"a": 0, "b": -5, "c": 1000000}
        self.assertEqual(canon.canonicalizar(d), '{"a":0,"b":-5,"c":1000000}')

    def test_escape_comillas_y_backslash(self):
        d = {"a": 'dice "hola" \\ chau'}
        self.assertEqual(canon.canonicalizar(d), '{"a":"dice \\"hola\\" \\\\ chau"}')

    def test_escape_controles_estandar(self):
        d = {"a": "linea1\nlinea2\ttab"}
        self.assertEqual(canon.canonicalizar(d), '{"a":"linea1\\nlinea2\\ttab"}')

    def test_control_no_estandar_usa_uXXXX(self):
        d = {"a": "\x01\x1f"}
        self.assertEqual(canon.canonicalizar(d), '{"a":"\\u0001\\u001f"}')

    def test_unicode_no_ascii_pasa_directo_utf8(self):
        # JCS no escapa no-ASCII: "ñ" y "á" van literales en UTF-8.
        d = {"nombre": "Martín Dalberto — Pozo Azul"}
        salida = canon.canonicalizar_bytes(d)
        self.assertIn("Martín".encode("utf-8"), salida)

    def test_anidado_listas_y_dicts(self):
        d = {"archivos": ["a.md", "b.py"], "meta": {"n": 2, "ok": True}}
        self.assertEqual(
            canon.canonicalizar(d),
            '{"archivos":["a.md","b.py"],"meta":{"n":2,"ok":true}}')

    def test_determinismo_repetido(self):
        d = {"z": 1, "a": {"y": 2, "b": 3}}
        self.assertEqual(canon.canonicalizar(d), canon.canonicalizar(dict(d)))

    def test_float_rechazado_explicitamente(self):
        # Decisión de diseño: no soportar float en silencio (ver docstring).
        with self.assertRaises(TypeError):
            canon.canonicalizar({"a": 1.5})

    def test_tipo_no_soportado_rechazado(self):
        with self.assertRaises(TypeError):
            canon.canonicalizar({"a": object()})


if __name__ == "__main__":
    unittest.main()
