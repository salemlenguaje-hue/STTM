"""
tests/test_servidor.py — Tests de endpoints del servidor STTM (ADR-002).

Levanta un servidor REAL en un sandbox (STTM_ROOT temporal + puerto libre)
y verifica los endpoints de lectura y escritura con urllib.
Nace de una deuda declarada: la capa API/UI se había validado solo a mano.
No toca el servidor vivo del autor: otro puerto, otra raíz.
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


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_srv_test_"))
        for carpeta in ["scripts", "web", "auditorias", "data", "docs"]:
            (cls.tmp / carpeta).mkdir()
        (cls.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True, exist_ok=True)
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "TEST", "titulo": "Proyecto test",
                        "descripcion": "sandbox", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "continuidad", "nivel_actual": "continuidad",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "verificar.py", "auditar.py", "firma.py",
                  "proyectos.py", "auditoria_meta.py", "servidor.py"]:
            shutil.copy(SCRIPTS_DIR / s, cls.tmp / "scripts" / s)
        cls.port = puerto_libre()
        env = os.environ.copy()
        env["STTM_ROOT"] = str(cls.tmp)
        env["STTM_PORT"] = str(cls.port)
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.base = f"http://127.0.0.1:{cls.port}"
        ultimo_error = None
        for _ in range(40):
            try:
                cls.get(cls, "/api/proyecto")
                return
            except Exception as e:
                ultimo_error = e
                time.sleep(0.25)
        cls.proc.terminate()
        raise RuntimeError(f"el servidor no arranco: {ultimo_error}")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---------- helpers ----------
    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return r.status, r.read().decode("utf-8")

    def post(self, path, datos):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(datos).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def get_json(self, path):
        status, cuerpo = self.get(path)
        self.assertEqual(status, 200, cuerpo)
        return json.loads(cuerpo)

    def post_json(self, path, datos):
        status, cuerpo = self.post(path, datos)
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
        status, res = self.post_json("/api/registrar", {"titulo": "", "detalle": ""})
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
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self.get("/api/documento?ruta=" + urllib.parse.quote(mala))
            self.assertIn(ctx.exception.code, (400, 404), mala)

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
        status, res = self.post_json("/api/no-existe", {})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
