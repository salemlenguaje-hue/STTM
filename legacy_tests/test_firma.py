# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_firma.py — Tests unitarios del adaptador de firma (API v2).

Migrado tras el incidente 001: firma.py renombro sus funciones a nombres
canonicos. Estos tests verifican la API v2 y fijan dos reglas de oro:
  1. El hash de contenido NO cubre el campo 'firma'.
  2. Una firma NUNCA se cubre a si misma (entrada_firmable excluye 'firma').
"""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import firma


def entrada_base(**overrides):
    """Entrada mínima con los campos canónicos del schema."""
    e = {
        "n": 1,
        "ts": "2026-09-23T00:00:00Z",
        "titulo": "Test",
        "detalle": "Detalle de prueba",
        "archivos": [],
        "commit_ref": None,
        "firma_tipo": "hash",
        "firma": None,
        "hash_prev": "0" * 64,
    }
    e.update(overrides)
    return e


class TestHash(unittest.TestCase):
    def test_hash_contenido_es_sha256_hex(self):
        h = firma.hash_contenido(entrada_base())
        self.assertEqual(len(h), 64)
        int(h, 16)  # debe ser hexadecimal válido

    def test_hash_no_cubre_el_campo_firma(self):
        """Regla de oro 1: cambiar 'firma' no debe cambiar el hash."""
        e1 = entrada_base()
        e2 = entrada_base(firma="aaaa")
        self.assertEqual(firma.hash_contenido(e1), firma.hash_contenido(e2))

    def test_hash_cubre_el_contenido(self):
        e1 = entrada_base()
        e2 = entrada_base(titulo="Otro titulo")
        self.assertNotEqual(firma.hash_contenido(e1), firma.hash_contenido(e2))

    def test_schema_v1_difiere_de_v2(self):
        """Por qué el verificador necesita aceptar dos schemas:
        con firma=None, v1 y v2 dan hashes distintos."""
        e = entrada_base()
        self.assertNotEqual(firma.hash_contenido(e), firma.hash_contenido_v1(e))


class TestHMAC(unittest.TestCase):
    def test_hmac_consistente(self):
        e = entrada_base()
        self.assertEqual(firma.hmac_firma(e, "clave"), firma.hmac_firma(e, "clave"))

    def test_hmac_diferente_clave(self):
        e = entrada_base()
        self.assertNotEqual(firma.hmac_firma(e, "clave1"), firma.hmac_firma(e, "clave2"))

    def test_hmac_no_se_cubre_a_si_misma(self):
        """Regla de oro 2: el HMAC canónico no cambia aunque el campo
        'firma' ya tenga otro valor, porque se firma sin ese campo."""
        e1 = entrada_base(firma_tipo="hmac")
        e1["hash"] = firma.hash_contenido(e1)
        f1 = firma.hmac_firma(e1, "clave")
        e2 = dict(e1, firma="valor_previo")
        self.assertEqual(f1, firma.hmac_firma(e2, "clave"))

    def test_legacy_difiere_de_canonica(self):
        """La fórmula buggy del incidente 001 debe ser distinguible."""
        e = entrada_base(firma_tipo="hmac")
        e["hash"] = firma.hash_contenido(e)
        self.assertNotEqual(firma.hmac_firma(e, "clave"),
                            firma.hmac_firma_legacy(e, "clave"))


class TestEd25519(unittest.TestCase):
    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_ceremonia_genera_pem_validos(self):
        priv, pub = firma.generar_claves_ed25519()
        self.assertIn(b"PRIVATE KEY", priv)
        self.assertIn(b"PUBLIC KEY", pub)

    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_firmar_y_verificar(self):
        priv, pub = firma.generar_claves_ed25519()
        e = entrada_base(firma_tipo="ed25519")
        e["hash"] = firma.hash_contenido(e)
        firma_bytes = firma.ed25519_firmar(e, priv)
        self.assertTrue(firma.ed25519_verificar(e, firma_bytes.hex(), pub))

    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_datos_alterados_no_verifican(self):
        priv, pub = firma.generar_claves_ed25519()
        e = entrada_base(firma_tipo="ed25519")
        e["hash"] = firma.hash_contenido(e)
        firma_bytes = firma.ed25519_firmar(e, priv)
        e_alterada = dict(e, detalle="Detalle alterado")
        self.assertFalse(firma.ed25519_verificar(e_alterada, firma_bytes.hex(), pub))

    @unittest.skipUnless(firma.ED25519_DISPONIBLE, "Ed25519 no disponible")
    def test_clave_equivocada_no_verifica(self):
        priv, _ = firma.generar_claves_ed25519()
        _, pub_otra = firma.generar_claves_ed25519()
        e = entrada_base(firma_tipo="ed25519")
        e["hash"] = firma.hash_contenido(e)
        firma_bytes = firma.ed25519_firmar(e, priv)
        self.assertFalse(firma.ed25519_verificar(e, firma_bytes.hex(), pub_otra))


if __name__ == "__main__":
    unittest.main(verbosity=2)
