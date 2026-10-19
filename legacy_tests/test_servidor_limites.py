# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_servidor_limites.py — Límites de tamaño en requests POST.

Protege contra DoS por payloads gigantes que saturan memoria o disco.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


class TestLimites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="sttm_srv_limites_"))
        (cls.tmp / "scripts").mkdir()
        (cls.tmp / "web").mkdir()
        (cls.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (cls.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "TEST", "titulo": "T",
                        "descripcion": "d", "creado_utc": "2026-01-01T00:00:00Z",
                        "nivel_inicial": "simple", "nivel_actual": "simple",
                        "primera_auditoria_utc": None, "ultima_auditoria_utc": None,
                        "activo": True}) + "\n", encoding="utf-8")
        (cls.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        
        for s in ["rutas.py", "registrar.py", "firma.py", "verificar.py",
                  "auditar.py", "proyectos.py", "servidor.py"]:
            shutil.copy(SCRIPTS_DIR / s, cls.tmp / "scripts" / s)
        
        (cls.tmp / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        
        cls.env = os.environ.copy()
        cls.env["STTM_ROOT"] = str(cls.tmp)
        cls.env["STTM_PORT"] = "8765"
        # H5: timeout corto para que el test de script colgado sea viable.
        cls.env["STTM_SCRIPT_TIMEOUT"] = "2"
        
        cls.proc = subprocess.Popen(
            [sys.executable, str(cls.tmp / "scripts" / "servidor.py")],
            env=cls.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(1)
        cls.url = "http://127.0.0.1:8765"
    
    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=5)
        # Cerrar los tubos de stdout/stderr para no dejar ResourceWarning.
        cls.proc.stdout.close()
        cls.proc.stderr.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)
    
    def test_json_mayor_a_10mb_devuelve_413(self):
        """POST con JSON > 10MB debe devolver 413 o cerrar la conexión.

        El servidor puede rechazar antes de leer el payload completo,
        lo que causa BrokenPipeError en el cliente. Ambos comportamientos
        son correctos: el payload gigante fue rechazado.
        """
        payload = json.dumps({"titulo": "x" * (10 * 1024 * 1024 + 1)})
        req = Request(
            f"{self.url}/api/registrar",
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            urlopen(req)
            self.fail("Debería haber fallado con 413 o BrokenPipeError")
        except HTTPError as e:
            self.assertEqual(e.code, 413)
            body = e.read().decode("utf-8")
            self.assertIn("demasiado grande", body.lower())
        except URLError as e:
            # El servidor rechazó el payload gigante y cerró la conexión antes
            # de leerlo. urllib envuelve el BrokenPipeError/ConnectionResetError
            # dentro de un URLError. Verificamos que la causa sea esa y no otra.
            razon = str(getattr(e, "reason", e))
            self.assertTrue(
                ("Broken pipe" in razon or "Connection reset" in razon
                 or "Errno 32" in razon or "Errno 104" in razon),
                f"URLError inesperado: {razon}")


    def test_documento_mayor_a_5mb_devuelve_413(self):
        """POST /api/documento con cuerpo > 5MB debe devolver 413."""
        payload = json.dumps({"tipo": "otro", "titulo": "Doc gigante",
                              "cuerpo": "x" * (5 * 1024 * 1024 + 1)})
        req = Request(
            f"{self.url}/api/documento",
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(HTTPError) as cm:
            urlopen(req)
        self.assertEqual(cm.exception.code, 413)
        body = cm.exception.read().decode("utf-8")
        self.assertIn("demasiado grande", body.lower())

    def test_script_colgado_devuelve_error_de_timeout(self):
        """H5: un script que cuelga no debe congelar el servidor.

        Se sobreescribe registrar.py con un script que duerme 10s.
        El servidor (con STTM_SCRIPT_TIMEOUT=2) debe matarlo a los 2s
        y responder ok:false con un mensaje de timeout, en vez de
        dejar el request colgando indefinidamente.
        """
        registrador = self.tmp / "scripts" / "registrar.py"
        original = registrador.read_text(encoding="utf-8")
        try:
            registrador.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
            payload = json.dumps({"titulo": "t", "detalle": "d"})
            req = Request(
                f"{self.url}/api/registrar",
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            resp = urlopen(req, timeout=8)
            datos = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(datos["ok"])
            self.assertIn("timeout", datos["stderr"].lower())
        finally:
            registrador.write_text(original, encoding="utf-8")

    def test_stderr_no_filtra_paths_absolutos(self):
        """H4: los paths absolutos del sistema no deben llegar al cliente.

        Se sobreescribe registrar.py con un script que escribe un path
        absoluto a stderr. El servidor debe sanitizar ese stderr antes
        de devolverlo, reemplazando el path por un placeholder.
        """
        registrador = self.tmp / "scripts" / "registrar.py"
        original = registrador.read_text(encoding="utf-8")
        try:
            registrador.write_text(
                "import sys\n"
                "print('Error en /data/data/com.termux/files/home/sttm/secreto.py: linea 42', file=sys.stderr)\n"
                "sys.exit(1)\n",
                encoding="utf-8")
            payload = json.dumps({"titulo": "t", "detalle": "d"})
            req = Request(
                f"{self.url}/api/registrar",
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            resp = urlopen(req, timeout=8)
            datos = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(datos["ok"])
            # El path absoluto NO debe aparecer en la respuesta.
            self.assertNotIn("/data/data", datos["stderr"])
            # Pero el mensaje útil (sin el path) sí debe estar.
            self.assertIn("linea 42", datos["stderr"])
        finally:
            registrador.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
