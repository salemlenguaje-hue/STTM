# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_servidor_limites.py — Límites y sanitización del servidor STTM v0.4.

Port de legacy_tests/test_servidor_limites.py a la API con login.
Cubre: límite de JSON (10 MB), límite de documento (5 MB), timeout de
scripts (H5) y sanitización de paths en stderr (H4). Usa un puerto libre
y un sandbox propio, sin tocar el servidor real del autor.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
PASS_ADMIN = "clave-admin-123456"


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestLimites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_srv_limites_"))
        shutil.copytree(SCRIPTS_DIR, cls.tmp / "scripts")
        (cls.tmp / "web").mkdir()
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "auditorias").mkdir()
        (cls.tmp / "docs").mkdir()
        (cls.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            "", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "TEST", "titulo": "T",
                        "descripcion": "d", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "simple", "nivel_actual": "simple",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")

        # Usuario admin de prueba, creado con el módulo identidad del sandbox.
        env_prev = os.environ.get("STTM_ROOT")
        os.environ["STTM_ROOT"] = str(cls.tmp)
        sys.path.insert(0, str(cls.tmp / "scripts"))
        sys.modules.pop("identidad", None)
        import identidad
        identidad.crear_usuario("admin1", PASS_ADMIN, "admin")
        sys.path.remove(str(cls.tmp / "scripts"))
        if env_prev is None:
            os.environ.pop("STTM_ROOT", None)
        else:
            os.environ["STTM_ROOT"] = env_prev

        env = os.environ.copy()
        env["STTM_ROOT"] = str(cls.tmp)
        cls.port = puerto_libre()
        env["STTM_PORT"] = str(cls.port)
        # H5: timeout corto para que el test de script colgado sea viable.
        env["STTM_SCRIPT_TIMEOUT"] = "2"
        cls.url = f"http://127.0.0.1:{cls.port}"
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for _ in range(60):
            try:
                urllib.request.urlopen(f"{cls.url}/api/proyecto", timeout=1)
                break
            except urllib.error.HTTPError as e:
                e.close()
                break
            except Exception:
                time.sleep(0.25)
        else:
            cls.proc.terminate()
            raise RuntimeError("el servidor no arrancó")

        cls.token = cls._login()

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        cls.proc.stdout.close()
        cls.proc.stderr.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def _login(cls):
        req = urllib.request.Request(
            f"{cls.url}/api/login",
            data=json.dumps({"usuario": "admin1", "password": PASS_ADMIN}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))["token"]

    def _post(self, path, payload_bytes, timeout=8):
        req = urllib.request.Request(
            f"{self.url}{path}", data=payload_bytes,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.token}"},
            method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))

    def test_json_mayor_a_10mb_devuelve_413(self):
        """POST con JSON > 10 MB debe devolver 413 o cerrar la conexión.

        El servidor puede rechazar antes de leer el payload completo, lo
        que produce BrokenPipe/ConnectionReset en el cliente. Ambos
        comportamientos son correctos: el payload gigante fue rechazado.
        """
        payload = json.dumps({"titulo": "x" * (10 * 1024 * 1024 + 1)}).encode("utf-8")
        try:
            self._post("/api/registrar", payload)
            self.fail("Debería haber fallado con 413 o cierre de conexión")
        except urllib.error.HTTPError as e:
            with e:
                self.assertEqual(e.code, 413)
                self.assertIn("demasiado grande", e.read().decode("utf-8").lower())
        except urllib.error.URLError as e:
            razon = str(getattr(e, "reason", e))
            self.assertTrue(
                any(s in razon for s in ("Broken pipe", "Connection reset",
                                         "Errno 32", "Errno 104")),
                f"URLError inesperado: {razon}")

    def test_413_es_una_sola_respuesta_http(self):
        """Regresión: antes del fix, do_POST enviaba un segundo 400 tras el 413.

        Se leen los bytes crudos del socket y se cuenta cuántas líneas de
        estado HTTP llegan. Debe haber exactamente una.
        """
        import socket as _s
        cuerpo = json.dumps({"titulo": "x" * (10 * 1024 * 1024 + 1)}).encode("utf-8")
        cabeceras = (f"POST /api/registrar HTTP/1.0\r\n"
                     f"Host: 127.0.0.1\r\n"
                     f"Authorization: Bearer {self.token}\r\n"
                     f"Content-Type: application/json\r\n"
                     f"Content-Length: {len(cuerpo)}\r\n\r\n").encode("utf-8")
        with _s.create_connection(("127.0.0.1", self.port), timeout=15) as sock:
            try:
                sock.sendall(cabeceras)
                sock.sendall(cuerpo)
            except (BrokenPipeError, ConnectionResetError):
                pass  # el servidor cerró temprano: también es un rechazo válido
            datos = b""
            try:
                while True:
                    bloque = sock.recv(65536)
                    if not bloque:
                        break
                    datos += bloque
            except (ConnectionResetError, _s.timeout):
                pass
        # La segunda respuesta del bug llega pegada al cuerpo de la primera
        # (sin \r\n previo), así que se cuentan apariciones, no líneas.
        apariciones = datos.count(b"HTTP/1.")
        self.assertEqual(apariciones, 1, datos[:300])
        self.assertTrue(datos.startswith(b"HTTP/1.0 413"), datos[:80])

    def test_documento_mayor_a_5mb_devuelve_413(self):
        """POST /api/documento con cuerpo > 5 MB debe devolver 413."""
        payload = json.dumps({"tipo": "otro", "titulo": "Doc gigante",
                              "cuerpo": "x" * (5 * 1024 * 1024 + 1)}).encode("utf-8")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._post("/api/documento", payload)
        with cm.exception as e:
            self.assertEqual(e.code, 413)
            self.assertIn("demasiado grande", e.read().decode("utf-8").lower())

    def test_script_colgado_devuelve_error_de_timeout(self):
        """H5: un script que cuelga no debe congelar el servidor.

        Se reemplaza registrar.py por un script que duerme 10 s. Con
        STTM_SCRIPT_TIMEOUT=2 el servidor lo corta y responde ok:false
        con mensaje de timeout.
        """
        registrador = self.tmp / "scripts" / "registrar.py"
        original = registrador.read_text(encoding="utf-8")
        try:
            registrador.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
            payload = json.dumps({"titulo": "t", "detalle": "d"}).encode("utf-8")
            _, datos = self._post("/api/registrar", payload, timeout=8)
            self.assertFalse(datos["ok"])
            self.assertIn("timeout", datos["stderr"].lower())
        finally:
            registrador.write_text(original, encoding="utf-8")

    def test_stderr_no_filtra_paths_absolutos(self):
        """H4: los paths absolutos del sistema no deben llegar al cliente.

        registrar.py escribe un path absoluto a stderr; el servidor debe
        reemplazarlo antes de devolverlo al cliente.
        """
        registrador = self.tmp / "scripts" / "registrar.py"
        original = registrador.read_text(encoding="utf-8")
        try:
            registrador.write_text(
                "import sys\n"
                "print('Error en /data/data/com.termux/files/home/sttm/secreto.py: linea 42', file=sys.stderr)\n"
                "sys.exit(1)\n",
                encoding="utf-8")
            payload = json.dumps({"titulo": "t", "detalle": "d"}).encode("utf-8")
            _, datos = self._post("/api/registrar", payload)
            self.assertFalse(datos["ok"])
            self.assertNotIn("/data/data", datos["stderr"])
            self.assertIn("linea 42", datos["stderr"])
        finally:
            registrador.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
