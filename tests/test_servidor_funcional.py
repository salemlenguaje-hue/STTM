# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_servidor_funcional.py — Endpoints funcionales del servidor STTM v0.4.

Port de legacy_tests/test_servidor.py a la API con login: el servidor real
corre en un sandbox (STTM_ROOT temporal, puerto libre) y cada petición lleva
un token de sesión obtenido por /api/login. Los roles de prueba son:
  - admin1: puede todo (crear proyecto, modo, auditar, registrar, documentos).
  - lec1:   solo lectura; las escrituras deben devolver 403.
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
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

PASS_ADMIN = "clave-admin-123456"
PASS_LECTOR = "clave-lector-123456"


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestServidorFuncional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_srv_fun_"))
        # El servidor lanza scripts/ como subprocesos: el sandbox replica el
        # árbol completo de scripts, igual que test_servidor_integracion.
        shutil.copytree(SCRIPTS_DIR, cls.tmp / "scripts")
        (cls.tmp / "web").mkdir()
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "auditorias").mkdir()
        (cls.tmp / "docs").mkdir()
        (cls.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            "", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "TEST", "titulo": "Proyecto test",
                        "descripcion": "sandbox", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "continuidad", "nivel_actual": "continuidad",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")

        # Usuarios de prueba, creados con el mismo módulo que usa el servidor.
        env_prev = os.environ.get("STTM_ROOT")
        os.environ["STTM_ROOT"] = str(cls.tmp)
        sys.path.insert(0, str(cls.tmp / "scripts"))
        sys.modules.pop("identidad", None)
        import identidad
        identidad.crear_usuario("admin1", PASS_ADMIN, "admin")
        identidad.crear_usuario("lec1", PASS_LECTOR, "lector")
        sys.path.remove(str(cls.tmp / "scripts"))
        if env_prev is None:
            os.environ.pop("STTM_ROOT", None)
        else:
            os.environ["STTM_ROOT"] = env_prev

        env = os.environ.copy()
        env["STTM_ROOT"] = str(cls.tmp)
        cls.port = puerto_libre()
        env["STTM_PORT"] = str(cls.port)
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Esperar a que responda. Un 401 también cuenta: el servidor está arriba.
        for _ in range(60):
            try:
                urllib.request.urlopen(f"{cls.base}/api/proyecto", timeout=1)
                break
            except urllib.error.HTTPError as e:
                e.close()
                break
            except Exception:
                time.sleep(0.25)
        else:
            cls.proc.terminate()
            raise RuntimeError("el servidor no arrancó")

        cls.token_admin = cls._login("admin1", PASS_ADMIN)
        cls.token_lector = cls._login("lec1", PASS_LECTOR)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---------- helpers ----------
    @classmethod
    def _pedir(cls, metodo, path, datos=None, token=None):
        headers = {}
        data = None
        if datos is not None:
            data = json.dumps(datos).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(cls.base + path, data=data, method=metodo, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read().decode("utf-8")

    @classmethod
    def _login(cls, usuario, password):
        status, cuerpo = cls._pedir("POST", "/api/login",
                                    {"usuario": usuario, "password": password})
        assert status == 200, cuerpo
        return json.loads(cuerpo)["token"]

    def get(self, path, token=None):
        return self._pedir("GET", path, token=self.token_admin if token is None else token)

    def post(self, path, datos, token=None):
        return self._pedir("POST", path, datos, token=self.token_admin if token is None else token)

    def get_json(self, path, token=None):
        status, cuerpo = self.get(path, token)
        self.assertEqual(status, 200, cuerpo)
        return json.loads(cuerpo)

    def post_json(self, path, datos, token=None):
        status, cuerpo = self.post(path, datos, token)
        return status, (json.loads(cuerpo) if cuerpo.strip() else {})

    # ---------- tests ----------
    def test_a_proyecto(self):
        data = self.get_json("/api/proyecto")
        self.assertEqual(data["proyecto"]["n"], 1)
        self.assertEqual(data["proyecto"]["nivel_actual"], "continuidad")

    def test_b_registro_y_bitacora(self):
        antes = self.get_json("/api/bitacora")
        status, res = self.post_json("/api/registrar", {
            "titulo": "Entrada de prueba", "detalle": "detalle de prueba",
            "modo_firma": "hash"})
        self.assertEqual(status, 200, res)
        self.assertTrue(res["ok"], res)
        despues = self.get_json("/api/bitacora")
        self.assertEqual(len(despues), len(antes) + 1)

    def test_c_registro_requiere_campos(self):
        status, _ = self.post_json("/api/registrar", {"titulo": "", "detalle": ""})
        self.assertEqual(status, 400)

    def test_d_modo_cambia_y_queda_en_catalogo(self):
        status, res = self.post_json("/api/modo", {"n": 1, "nivel": "salem"})
        self.assertEqual(status, 200, res)
        self.assertTrue(res["ok"], res)
        data = self.get_json("/api/proyecto")
        self.assertEqual(data["proyecto"]["nivel_actual"], "salem")

    def test_e_documento_crear_y_leer(self):
        status, res = self.post_json("/api/documento", {
            "tipo": "otro", "titulo": "Nota de prueba",
            "cuerpo": "# Nota\ncontenido de prueba"})
        self.assertEqual(status, 200, res)
        self.assertTrue(res["creada"], res)
        status, texto = self.get("/api/documento?ruta=" + urllib.parse.quote(res["ruta"]))
        self.assertEqual(status, 200)
        self.assertIn("contenido de prueba", texto)

    def test_f_rutas_prohibidas(self):
        for mala in ["../BITACORA.jsonl", "docs/../../BITACORA.jsonl",
                     "data/proyectos.jsonl", "docs/nota.txt"]:
            status, _ = self.get("/api/documento?ruta=" + urllib.parse.quote(mala))
            self.assertIn(status, (400, 404), mala)

    def test_g_auditoria_genera_los_tres_artefactos(self):
        status, res = self.post_json("/api/auditar", {"motivo": "test", "tipo": "rapida"})
        self.assertEqual(status, 200, res)
        self.assertTrue(res["carpeta"], res)
        d = self.tmp / "auditorias" / res["carpeta"]
        self.assertTrue((d / "reporte.md").exists())
        self.assertTrue((d / "meta.json").exists())
        self.assertTrue((d / "manifiesto.json").exists())
        auds = self.get_json("/api/auditorias")
        self.assertTrue(any(a["carpeta"] == res["carpeta"] for a in auds))

    def test_h_verificar_paquete(self):
        status, res = self.post_json("/api/auditar", {"motivo": "test 2", "tipo": "rapida"})
        self.assertEqual(status, 200, res)
        verif = self.get_json("/api/verificar-paquete?carpeta=" + res["carpeta"])
        self.assertTrue(verif["cadena"]["integra"])
        self.assertTrue(verif["manifiesto"]["ok"])

    def test_i_endpoint_desconocido(self):
        status, _ = self.post_json("/api/no-existe", {})
        self.assertEqual(status, 404)

    # ---------- casos nuevos de v0.4: autenticación y roles ----------
    def test_j_sin_token_no_lee(self):
        status, _ = self.get("/api/bitacora", token="")
        self.assertEqual(status, 401)

    def test_k_lector_puede_leer(self):
        status, _ = self.get("/api/bitacora", token=self.token_lector)
        self.assertEqual(status, 200)

    def test_l_lector_no_puede_escribir(self):
        status, res = self.post_json("/api/modo", {"n": 1, "nivel": "continuidad"},
                                     token=self.token_lector)
        self.assertEqual(status, 403, res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
