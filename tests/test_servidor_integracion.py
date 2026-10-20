import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _puerto_libre():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


def _pedir(metodo, url, token=None, cuerpo=None):
    headers = {}
    data = None
    if cuerpo is not None:
        data = json.dumps(cuerpo).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=metodo, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}


class TestServidorIntegracion(unittest.TestCase):
    """Levanta el servidor real (subprocess) y lo golpea por HTTP de
    verdad — no es un mock. Esto es lo que realmente importa probar:
    STTM v0.4 promete auth + roles a nivel API, no solo a nivel de
    funciones internas."""

    @classmethod
    def setUpClass(cls):
        import shutil
        import tempfile
        cls.tmp = tempfile.mkdtemp()
        # El servidor resuelve SCRIPTS = STTM_ROOT/scripts para lanzar
        # registrar.py/auditar.py/proyectos.py como subprocesos: el
        # directorio de datos y el de código son el mismo en una
        # instalación real, así que el sandbox de test tiene que
        # replicar eso (copiar scripts/, no solo apuntar a un tmpdir vacío).
        shutil.copytree(SCRIPTS, Path(cls.tmp) / "scripts")
        cls.env = os.environ.copy()
        cls.env["STTM_ROOT"] = cls.tmp
        cls.puerto = _puerto_libre()
        cls.env["STTM_PORT"] = str(cls.puerto)
        cls.base = f"http://127.0.0.1:{cls.puerto}"

        sys.path.insert(0, str(SCRIPTS))
        os.environ["STTM_ROOT"] = cls.tmp
        for mod in ("identidad",):
            sys.modules.pop(mod, None)
        import identidad
        identidad.crear_usuario("admin1", "clave-admin-123456", "admin")
        identidad.crear_usuario("audi1", "clave-audi-1234567", "auditor")
        identidad.crear_usuario("lec1", "clave-lector-123456", "lector")
        os.environ.pop("STTM_ROOT", None)

        cls.proc = subprocess.Popen(
            [sys.executable, str(Path(cls.tmp) / "scripts" / "servidor.py")],
            env=cls.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Esperar a que el puerto responda (hasta 5s).
        for _ in range(50):
            try:
                urllib.request.urlopen(f"{cls.base}/", timeout=0.5)
                break
            except Exception:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
        # Cerrar los pipes para no dejar ResourceWarning.
        for tubo in (cls.proc.stdout, cls.proc.stderr):
            if tubo:
                tubo.close()
        __import__("shutil").rmtree(cls.tmp, ignore_errors=True)

    def _login(self, usuario, password):
        status, cuerpo = _pedir("POST", f"{self.base}/api/login",
                                 cuerpo={"usuario": usuario, "password": password})
        return status, cuerpo

    def test_endpoint_sin_token_devuelve_401(self):
        status, cuerpo = _pedir("GET", f"{self.base}/api/bitacora")
        self.assertEqual(status, 401)

    def test_login_correcto_da_token(self):
        status, cuerpo = self._login("admin1", "clave-admin-123456")
        self.assertEqual(status, 200)
        self.assertIn("token", cuerpo)
        self.assertEqual(cuerpo["rol"], "admin")

    def test_login_incorrecto_401(self):
        status, cuerpo = self._login("admin1", "password-mala")
        self.assertEqual(status, 401)

    def test_token_valido_permite_leer_bitacora(self):
        _, sesion = self._login("lec1", "clave-lector-123456")
        status, cuerpo = _pedir("GET", f"{self.base}/api/bitacora", token=sesion["token"])
        self.assertEqual(status, 200)
        self.assertIsInstance(cuerpo, list)

    def test_lector_no_puede_registrar(self):
        _, sesion = self._login("lec1", "clave-lector-123456")
        status, cuerpo = _pedir(
            "POST", f"{self.base}/api/registrar", token=sesion["token"],
            cuerpo={"titulo": "intento de lector", "detalle": "no debería poder"})
        self.assertEqual(status, 403)

    def test_auditor_puede_registrar_y_queda_atribuido(self):
        _, sesion = self._login("audi1", "clave-audi-1234567")
        status, cuerpo = _pedir(
            "POST", f"{self.base}/api/registrar", token=sesion["token"],
            cuerpo={"titulo": "Entrada vía API", "detalle": "creada por audi1"})
        self.assertEqual(status, 200)
        self.assertTrue(cuerpo["ok"], msg=cuerpo)

        _, admin_sesion = self._login("admin1", "clave-admin-123456")
        status, entradas = _pedir("GET", f"{self.base}/api/bitacora", token=admin_sesion["token"])
        self.assertEqual(entradas[0]["actor"], "audi1")
        self.assertEqual(entradas[0]["firma_tipo"], "ed25519_actor")

    def test_solo_admin_ve_usuarios(self):
        _, audi_sesion = self._login("audi1", "clave-audi-1234567")
        status, _ = _pedir("GET", f"{self.base}/api/usuarios", token=audi_sesion["token"])
        self.assertEqual(status, 403)

        _, admin_sesion = self._login("admin1", "clave-admin-123456")
        status, usuarios = _pedir("GET", f"{self.base}/api/usuarios", token=admin_sesion["token"])
        self.assertEqual(status, 200)
        nombres = {u["nombre_usuario"] for u in usuarios}
        self.assertIn("admin1", nombres)
        self.assertIn("lec1", nombres)

    def test_buscar_encuentra_entrada_recien_creada(self):
        _, sesion = self._login("audi1", "clave-audi-1234567")
        _pedir("POST", f"{self.base}/api/registrar", token=sesion["token"],
               cuerpo={"titulo": "Palabra-clave-unica-xyz", "detalle": "para buscar"})
        status, resultado = _pedir(
            "GET", f"{self.base}/api/buscar?q=Palabra-clave-unica-xyz", token=sesion["token"])
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(resultado["resultados"]), 1)

    def test_logout_invalida_el_token(self):
        _, sesion = self._login("lec1", "clave-lector-123456")
        status, _ = _pedir("POST", f"{self.base}/api/logout", token=sesion["token"])
        self.assertEqual(status, 200)
        status, _ = _pedir("GET", f"{self.base}/api/bitacora", token=sesion["token"])
        self.assertEqual(status, 401)

    def test_rate_limit_de_login_bloquea_tras_varios_fallos(self):
        # Usuario dedicado a este test: si usáramos admin1, lo dejaríamos
        # bloqueado para el resto de los tests de esta clase (el bloqueo
        # es por (ip, usuario), así que afecta a esa cuenta puntual).
        for _ in range(6):
            status, _ = self._login("cuenta-inexistente-rate-test", "lo-que-sea")
        status, cuerpo = self._login("cuenta-inexistente-rate-test", "lo-que-sea")
        self.assertEqual(status, 429)


if __name__ == "__main__":
    unittest.main()
