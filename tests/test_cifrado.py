import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import cifrado  # noqa: E402


class TestCifrado(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta_claves = Path(self._tmp.name) / "claves" / "entradas"

    def tearDown(self):
        self._tmp.cleanup()

    def test_cifrar_y_descifrar_roundtrip(self):
        original = "Juan Pérez, DNI 12.345.678, reportó un bug"
        r = cifrado.cifrar_detalle(self.carpeta_claves, 1, original)
        self.assertNotIn("Juan Pérez", r["detalle_cifrado"])
        recuperado = cifrado.descifrar_detalle(self.carpeta_claves, 1, r["detalle_cifrado"])
        self.assertEqual(recuperado, original)

    def test_hash_permite_verificar_integridad_sin_ver_contenido(self):
        import hashlib
        original = "contenido sensible"
        r = cifrado.cifrar_detalle(self.carpeta_claves, 1, original)
        self.assertEqual(r["detalle_hash"],
                          hashlib.sha256(original.encode("utf-8")).hexdigest())

    def test_no_sobreescribe_clave_existente(self):
        cifrado.cifrar_detalle(self.carpeta_claves, 1, "primero")
        with self.assertRaises(cifrado.ErrorCifrado):
            cifrado.cifrar_detalle(self.carpeta_claves, 1, "segundo")

    def test_triturar_hace_irrecuperable_el_contenido(self):
        r = cifrado.cifrar_detalle(self.carpeta_claves, 5, "dato personal")
        self.assertTrue(cifrado.triturar(self.carpeta_claves, 5))
        with self.assertRaises(cifrado.ErrorCifrado):
            cifrado.descifrar_detalle(self.carpeta_claves, 5, r["detalle_cifrado"])

    def test_triturar_es_idempotente(self):
        cifrado.cifrar_detalle(self.carpeta_claves, 2, "algo")
        self.assertTrue(cifrado.triturar(self.carpeta_claves, 2))
        self.assertFalse(cifrado.triturar(self.carpeta_claves, 2))  # ya no había nada

    def test_esta_triturada(self):
        cifrado.cifrar_detalle(self.carpeta_claves, 3, "algo")
        self.assertFalse(cifrado.esta_triturada(self.carpeta_claves, 3))
        cifrado.triturar(self.carpeta_claves, 3)
        self.assertTrue(cifrado.esta_triturada(self.carpeta_claves, 3))
        # Una entrada que nunca existió también cuenta como "triturada"
        # (no hay clave = no hay acceso, sea cual sea la razón).
        self.assertTrue(cifrado.esta_triturada(self.carpeta_claves, 999))

    def test_permisos_de_archivo_de_clave(self):
        cifrado.cifrar_detalle(self.carpeta_claves, 1, "algo")
        ruta = self.carpeta_claves / "1.key"
        modo = oct(os.stat(ruta).st_mode)[-3:]
        self.assertEqual(modo, "600")

    def test_registrar_triturado_deja_constancia(self):
        cifrado.cifrar_detalle(self.carpeta_claves, 7, "algo")
        cifrado.triturar(self.carpeta_claves, 7)
        ruta = cifrado.registrar_triturado_en_manifiesto(
            self.carpeta_claves, 7, "solicitud de baja del titular")
        self.assertTrue(ruta.exists())
        contenido = ruta.read_text(encoding="utf-8")
        self.assertIn('"n": 7', contenido)
        self.assertIn("solicitud de baja", contenido)

    def test_dos_entradas_no_comparten_clave(self):
        r1 = cifrado.cifrar_detalle(self.carpeta_claves, 1, "texto A")
        r2 = cifrado.cifrar_detalle(self.carpeta_claves, 2, "texto B")
        cifrado.triturar(self.carpeta_claves, 1)
        # Triturar la 1 no debe afectar la 2.
        recuperado2 = cifrado.descifrar_detalle(self.carpeta_claves, 2, r2["detalle_cifrado"])
        self.assertEqual(recuperado2, "texto B")


if __name__ == "__main__":
    unittest.main()
