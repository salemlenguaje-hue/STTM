import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _correr(env, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / args[0]), *args[1:]],
        capture_output=True, text=True, env=env)


class TestRegistroV3Integracion(unittest.TestCase):
    """Prueba el flujo completo tal como lo usaría el servidor: crear un
    usuario real, registrar una entrada firmada con SU clave, y verificar
    que la cadena resultante sea íntegra y que la firma se atribuya
    correctamente a ese actor (y a ningún otro)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = self._tmp.name
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = self.raiz
        self.env["PYTHONPATH"] = str(SCRIPTS)
        # Crear dos usuarios directamente vía la API de identidad.py
        # (sin pasar por el CLI interactivo de getpass).
        sys.path.insert(0, str(SCRIPTS))
        for mod in ("identidad", "firma", "canon", "rutas", "registrar", "verificar"):
            sys.modules.pop(mod, None)
        os.environ["STTM_ROOT"] = self.raiz
        import identidad
        identidad.crear_usuario("ana", "clave-de-ana-123456", "auditor", "Ana Auditor")
        identidad.crear_usuario("beto", "clave-de-beto-123456", "auditor", "Beto Auditor")

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop("STTM_ROOT", None)
        for mod in ("identidad", "firma", "canon", "rutas", "registrar", "verificar"):
            sys.modules.pop(mod, None)

    def test_registro_v3_queda_integro_y_atribuido(self):
        r = _correr(self.env, "registrar.py", "Primer registro", "detalle de prueba",
                    "--actor", "ana")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("✅", r.stdout)

        bitacora = Path(self.raiz) / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        self.assertTrue(bitacora.exists())
        entrada = json.loads(bitacora.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(entrada["actor"], "ana")
        self.assertEqual(entrada["firma_tipo"], "ed25519_actor")

        v = _correr(self.env, "verificar.py", str(bitacora))
        self.assertEqual(v.returncode, 0, msg=v.stdout + v.stderr)
        self.assertIn("v3=1", v.stdout)
        self.assertIn("Cadena íntegra", v.stdout)

    def test_dos_actores_encadenan_correctamente(self):
        _correr(self.env, "registrar.py", "Entrada de Ana", "detalle 1", "--actor", "ana")
        r2 = _correr(self.env, "registrar.py", "Entrada de Beto", "detalle 2", "--actor", "beto")
        self.assertEqual(r2.returncode, 0, msg=r2.stdout + r2.stderr)

        bitacora = Path(self.raiz) / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        v = _correr(self.env, "verificar.py", str(bitacora))
        self.assertIn("v3=2", v.stdout)
        self.assertIn("Cadena íntegra", v.stdout)

    def test_entrada_alterada_se_detecta(self):
        _correr(self.env, "registrar.py", "Título original", "detalle original", "--actor", "ana")
        bitacora = Path(self.raiz) / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        entrada = json.loads(bitacora.read_text(encoding="utf-8").splitlines()[0])
        entrada["detalle"] = "detalle MODIFICADO después de firmar"
        bitacora.write_text(json.dumps(entrada, ensure_ascii=False) + "\n", encoding="utf-8")

        v = _correr(self.env, "verificar.py", str(bitacora))
        self.assertNotEqual(v.returncode, 0)
        self.assertIn("problema", v.stdout.lower())

    def test_no_se_puede_registrar_sin_actor_en_modo_v3(self):
        r = _correr(self.env, "registrar.py", "Sin actor", "detalle",
                    "--modo-firma", "ed25519_actor")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
