"""
tests/test_integracion_firma.py — Circuito completo registrar -> verificar.
Nació del incidente 001: los tests unitarios no detectaban bugs de
integración (schema cambiado, firma autorreferencial).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import firma


class TestIntegracion(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="sttm_int_")
        self.raiz = Path(self.tmpdir)
        (self.raiz / "scripts").mkdir()
        (self.raiz / "data" / "claves").mkdir(parents=True)
        (self.raiz / "data" / "proyectos" / "1-STTM").mkdir(parents=True, exist_ok=True)
        (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text("", encoding="utf-8")
        for s in ["rutas.py", "registrar.py", "verificar.py", "firma.py"]:
            (self.raiz / "scripts" / s).write_text(
                (SCRIPTS_DIR / s).read_text(encoding="utf-8"), encoding="utf-8")
        self.entorno = os.environ.copy()
        self.entorno["STTM_ROOT"] = str(self.raiz)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def correr(self, nombre, *args):
        return subprocess.run(
            [sys.executable, str(self.raiz / "scripts" / nombre), *args],
            capture_output=True, text=True, env=self.entorno)

    def leer_entradas(self):
        return [json.loads(l) for l in
                (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").read_text().splitlines() if l.strip()]

    def test_roundtrip_hash(self):
        self.correr("registrar.py", "A", "detalle")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_roundtrip_hmac(self):
        """Incidente 001 caso 2: HMAC debe verificar tras registrar."""
        self.correr("registrar.py", "A", "detalle", "--modo-firma", "hmac")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("inválida", r.stdout)

    def test_hmac_legacy_se_reconoce(self):
        """Incidente 001: entradas firmadas con la fórmula buggy
        deben pasar como aviso legacy, no como error."""
        e = {"n": 1, "ts": "2026-01-01T00:00:00Z", "titulo": "Legacy",
             "detalle": "x", "archivos": [], "commit_ref": None,
             "firma_tipo": "hmac", "firma": None, "hash_prev": "0" * 64}
        e["hash"] = firma.hash_contenido(e)
        e["firma"] = firma.hmac_firma_legacy(e, "clave_secreta_temporal")
        (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            json.dumps(e, ensure_ascii=False) + "\n", encoding="utf-8")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("legacy", r.stdout)

    def test_schema_v1_se_acepta(self):
        """Entradas históricas v1 deben verificar sin errores."""
        e = {"n": 1, "ts": "2026-01-01T00:00:00Z", "titulo": "V1",
             "detalle": "x", "archivos": [], "commit_ref": None,
             "firma_tipo": "hash", "firma": None, "hash_prev": "0" * 64}
        e["hash"] = firma.hash_contenido_v1(e)
        (self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            json.dumps(e, ensure_ascii=False) + "\n", encoding="utf-8")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("v1=1", r.stdout)

    def test_alteracion_se_detecta(self):
        self.correr("registrar.py", "A", "detalle original", "--modo-firma", "hmac")
        b = self.raiz / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl"
        b.write_text(b.read_text().replace("original", "tocado"))
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("alterado", r.stdout)

    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_roundtrip_ed25519(self):
        self.correr("firma.py", "ceremonia")
        self.correr("registrar.py", "A", "detalle", "--modo-firma", "ed25519")
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("inválida", r.stdout)

    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_ed25519_clave_equivocada_falla(self):
        self.correr("firma.py", "ceremonia")
        self.correr("registrar.py", "A", "detalle", "--modo-firma", "ed25519")
        # Reemplazamos la clave pública por otra: la firma debe caer.
        priv, pub = firma.generar_claves_ed25519()
        (self.raiz / "data" / "claves" / "sofia_publica.pem").write_bytes(pub)
        r = self.correr("verificar.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Ed25519 inválida", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
