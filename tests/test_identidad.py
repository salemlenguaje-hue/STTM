import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestIdentidad(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["STTM_ROOT"] = self._tmp.name
        # Reimport limpio: los módulos leen RAIZ al importar.
        for mod in ("identidad",):
            sys.modules.pop(mod, None)
        global identidad
        import identidad  # noqa: E402

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop("STTM_ROOT", None)

    def test_crear_usuario_y_listar(self):
        identidad.crear_usuario("marti", "contraseña-larga-1", "admin", "Martín")
        usuarios = identidad.listar_usuarios()
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0]["nombre_usuario"], "marti")
        self.assertEqual(usuarios[0]["rol"], "admin")
        # Fingerprint de clave propia generado (cryptography está disponible).
        self.assertTrue(usuarios[0]["fingerprint_clave"])

    def test_no_duplica_usuario(self):
        identidad.crear_usuario("marti", "contraseña-larga-1", "admin")
        with self.assertRaises(identidad.ErrorIdentidad):
            identidad.crear_usuario("marti", "otra-contraseña-2", "lector")

    def test_password_corta_rechazada(self):
        with self.assertRaises(identidad.ErrorIdentidad):
            identidad.crear_usuario("marti", "corta", "admin")

    def test_rol_invalido_rechazado(self):
        with self.assertRaises(identidad.ErrorIdentidad):
            identidad.crear_usuario("marti", "contraseña-larga-1", "superadmin")

    def test_autenticar_ok_y_password_incorrecta(self):
        identidad.crear_usuario("ana", "clave-correcta-123", "auditor")
        sesion = identidad.autenticar("ana", "clave-correcta-123")
        self.assertEqual(sesion["usuario"], "ana")
        self.assertEqual(sesion["rol"], "auditor")
        with self.assertRaises(identidad.ErrorIdentidad):
            identidad.autenticar("ana", "clave-incorrecta")

    def test_usuario_inexistente_no_filtra_informacion(self):
        # El mensaje debe ser idéntico al de password incorrecta (no
        # revelar si el usuario existe o no).
        with self.assertRaises(identidad.ErrorIdentidad) as ctx1:
            identidad.autenticar("no_existe", "lo_que_sea_123")
        identidad.crear_usuario("bruno", "clave-correcta-456", "lector")
        with self.assertRaises(identidad.ErrorIdentidad) as ctx2:
            identidad.autenticar("bruno", "clave-incorrecta")
        self.assertEqual(str(ctx1.exception), str(ctx2.exception))

    def test_token_valido_y_expiracion(self):
        identidad.crear_usuario("carla", "clave-correcta-789", "lector")
        sesion = identidad.autenticar("carla", "clave-correcta-789")
        info = identidad.validar_token(sesion["token"])
        self.assertEqual(info["usuario"], "carla")
        self.assertEqual(info["rol"], "lector")
        # Forzar expiración manipulando el TTL a 0 para un token nuevo.
        identidad.TTL_SESION_SEGUNDOS = 0
        sesion2 = identidad.crear_sesion("carla", "lector")
        time.sleep(0.01)
        self.assertIsNone(identidad.validar_token(sesion2["token"]))
        identidad.TTL_SESION_SEGUNDOS = 12 * 3600  # restaurar default

    def test_token_invalido_devuelve_none(self):
        self.assertIsNone(identidad.validar_token("token-que-no-existe"))
        self.assertIsNone(identidad.validar_token(""))

    def test_cerrar_sesion_invalida_token(self):
        identidad.crear_usuario("dario", "clave-correcta-000", "lector")
        sesion = identidad.autenticar("dario", "clave-correcta-000")
        identidad.cerrar_sesion(sesion["token"])
        self.assertIsNone(identidad.validar_token(sesion["token"]))

    def test_jerarquia_de_roles(self):
        self.assertTrue(identidad.rol_alcanza("admin", "lector"))
        self.assertTrue(identidad.rol_alcanza("admin", "auditor"))
        self.assertTrue(identidad.rol_alcanza("auditor", "lector"))
        self.assertFalse(identidad.rol_alcanza("lector", "auditor"))
        self.assertFalse(identidad.rol_alcanza("auditor", "admin"))

    def test_desactivar_usuario_bloquea_login(self):
        identidad.crear_usuario("eva", "clave-correcta-111", "auditor")
        identidad.desactivar_usuario("eva")
        with self.assertRaises(identidad.ErrorIdentidad):
            identidad.autenticar("eva", "clave-correcta-111")

    def test_firma_propia_por_usuario_y_no_cruzada(self):
        identidad.crear_usuario("gaby", "clave-correcta-222", "auditor")
        identidad.crear_usuario("hugo", "clave-correcta-333", "auditor")
        texto = b'{"n":1,"titulo":"prueba"}'
        firma_gaby = identidad.firmar_como("gaby", texto)
        self.assertTrue(identidad.verificar_firma_de("gaby", texto, firma_gaby))
        # La firma de gaby NO debe validar contra la clave pública de hugo.
        self.assertFalse(identidad.verificar_firma_de("hugo", texto, firma_gaby))

    def test_passwords_no_se_guardan_en_claro(self):
        identidad.crear_usuario("ivan", "una-clave-muy-secreta", "lector")
        contenido = identidad.USUARIOS_JSON.read_text(encoding="utf-8")
        self.assertNotIn("una-clave-muy-secreta", contenido)

    def test_permisos_archivo_usuarios_restringidos(self):
        identidad.crear_usuario("juli", "clave-correcta-444", "lector")
        modo = oct(os.stat(identidad.USUARIOS_JSON).st_mode)[-3:]
        self.assertEqual(modo, "600")


if __name__ == "__main__":
    unittest.main()
