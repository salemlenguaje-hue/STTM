import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import testigo_rfc3161 as t  # noqa: E402


class TestDERCodec(unittest.TestCase):
    """Estos tests NO requieren red: prueban que el codificador es
    internamente consistente y que coincide con vectores DER conocidos
    y públicamente documentados (no inventados por este proyecto)."""

    def test_entero_cero(self):
        self.assertEqual(t.codificar_entero(0), b"\x02\x01\x00")

    def test_entero_pequeno_positivo(self):
        # INTEGER 1 en DER: tag 02, largo 01, valor 01.
        self.assertEqual(t.codificar_entero(1), b"\x02\x01\x01")

    def test_entero_necesita_byte_de_signo(self):
        # 128 = 0x80: el bit alto está seteado, así que DER antepone 0x00
        # para que no se lea como número negativo.
        self.assertEqual(t.codificar_entero(128), b"\x02\x02\x00\x80")

    def test_oid_sha256_vector_conocido(self):
        # 2.16.840.1.101.3.4.2.1 (id-sha256) — bytes de referencia
        # ampliamente documentados en implementaciones X.509/PKCS.
        esperado = bytes.fromhex("06 09 60 86 48 01 65 03 04 02 01".replace(" ", ""))
        self.assertEqual(t.codificar_oid(t.OID_SHA256), esperado)

    def test_booleano(self):
        self.assertEqual(t.codificar_booleano(True), b"\x01\x01\xff")
        self.assertEqual(t.codificar_booleano(False), b"\x01\x01\x00")

    def test_null(self):
        self.assertEqual(t.codificar_null(), b"\x05\x00")

    def test_longitud_larga_mas_de_127_bytes(self):
        contenido = b"\x00" * 200
        codificado = t.codificar_octet_string(contenido)
        # tag(1) + 0x81(indicador 1 byte de longitud) + 0xC8(200) + contenido
        self.assertEqual(codificado[:3], bytes([0x04, 0x81, 200]))
        self.assertEqual(len(codificado), 3 + 200)

    def test_roundtrip_secuencia_simple(self):
        original = t.codificar_secuencia(
            t.codificar_entero(1), t.codificar_octet_string(b"hola"))
        nodo = t.decodificar(original)
        self.assertEqual(nodo.tag, t.TAG_SEQUENCE)
        self.assertEqual(len(nodo.hijos), 2)
        self.assertEqual(t.decodificar_entero(nodo.hijos[0]), 1)
        self.assertEqual(nodo.hijos[1].contenido, b"hola")

    def test_roundtrip_oid(self):
        codificado = t.codificar_oid(t.OID_SHA256)
        nodo = t.decodificar(codificado)
        self.assertEqual(t.decodificar_oid(nodo), t.OID_SHA256)

    def test_decodificar_rechaza_bytes_sobrantes(self):
        original = t.codificar_entero(5) + b"\x00\x00\x00"  # basura al final
        with self.assertRaises(t.ErrorDER):
            t.decodificar(original)


class TestConstruirTSQ(unittest.TestCase):

    def test_estructura_general_es_secuencia(self):
        digest = hashlib.sha256(b"contenido de prueba").digest()
        tsq = t.construir_tsq(digest)
        nodo = t.decodificar(tsq)
        self.assertEqual(nodo.tag, t.TAG_SEQUENCE)
        # version, messageImprint, nonce, certReq → 4 hijos en este orden
        self.assertEqual(len(nodo.hijos), 4)
        self.assertEqual(t.decodificar_entero(nodo.hijos[0]), 1)  # version v1

    def test_message_imprint_contiene_el_digest_exacto(self):
        digest = hashlib.sha256(b"otro contenido distinto").digest()
        tsq = t.construir_tsq(digest)
        nodo = t.decodificar(tsq)
        message_imprint = nodo.hijos[1]
        hashed_message = message_imprint.hijos[1]
        self.assertEqual(hashed_message.contenido, digest)

    def test_message_imprint_usa_oid_sha256(self):
        digest = hashlib.sha256(b"x").digest()
        tsq = t.construir_tsq(digest)
        nodo = t.decodificar(tsq)
        algoritmo = nodo.hijos[1].hijos[0]
        oid_usado = t.decodificar_oid(algoritmo.hijos[0])
        self.assertEqual(oid_usado, t.OID_SHA256)

    def test_rechaza_digest_de_tamano_incorrecto(self):
        with self.assertRaises(t.ErrorDER):
            t.construir_tsq(b"\x00" * 20)  # SHA-1 por error, no SHA-256

    def test_nonce_se_puede_fijar_para_reproducibilidad(self):
        digest = hashlib.sha256(b"y").digest()
        tsq1 = t.construir_tsq(digest, nonce=12345)
        tsq2 = t.construir_tsq(digest, nonce=12345)
        self.assertEqual(tsq1, tsq2)

    def test_nonce_por_defecto_varia_entre_llamadas(self):
        digest = hashlib.sha256(b"z").digest()
        tsq1 = t.construir_tsq(digest)
        tsq2 = t.construir_tsq(digest)
        self.assertNotEqual(tsq1, tsq2)

    def test_cert_req_afecta_la_codificacion(self):
        digest = hashlib.sha256(b"w").digest()
        tsq_con = t.construir_tsq(digest, incluir_certs=True, nonce=1)
        tsq_sin = t.construir_tsq(digest, incluir_certs=False, nonce=1)
        self.assertNotEqual(tsq_con, tsq_sin)


class TestExtraerEstadoRespuesta(unittest.TestCase):
    """Simulamos una TimeStampResp mínima (sin token) para probar el
    parser sin depender de una TSA real."""

    def _respuesta_simulada(self, status: int, con_token: bool = False):
        pki_status_info = t.codificar_secuencia(t.codificar_entero(status))
        partes = [pki_status_info]
        if con_token:
            partes.append(t.codificar_secuencia(t.codificar_entero(0)))
        return t.codificar_secuencia(*partes)

    def test_status_concedido(self):
        resp = self._respuesta_simulada(0, con_token=True)
        estado = t.extraer_estado_respuesta(resp)
        self.assertTrue(estado["concedido"])
        self.assertTrue(estado["tiene_token"])

    def test_status_rechazado(self):
        resp = self._respuesta_simulada(2, con_token=False)
        estado = t.extraer_estado_respuesta(resp)
        self.assertFalse(estado["concedido"])
        self.assertFalse(estado["tiene_token"])

    def test_respuesta_malformada_lanza_error(self):
        with self.assertRaises(t.ErrorDER):
            t.extraer_estado_respuesta(b"\x30\x00")  # SEQUENCE vacía


if __name__ == "__main__":
    unittest.main()
