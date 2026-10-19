#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
testigo_rfc3161.py — Testigo externo automático vía RFC 3161 (ADR-STTM-008).

⚠️ ESTADO DECLARADO: BETA — NO VALIDADO CONTRA UNA TSA REAL.
Este archivo se escribió en un entorno de desarrollo SIN acceso de red
saliente (proxy de egress bloqueado). Se pudo probar:
  - Que el codificador DER es autoconsistente (encode → decode reconstruye
    la misma estructura).
  - Que el OID de SHA-256 codifica byte a byte igual al valor de
    referencia públicamente conocido (60 86 48 01 65 03 04 02 01).
  - Que la forma general de un TimeStampReq (RFC 3161 §2.4.1) tiene la
    estructura SEQUENCE correcta.

NO se pudo probar:
  - Que una Autoridad de Sellado de Tiempo (TSA) real acepte y responda
    a esta petición. Eso requiere una petición HTTP saliente real.

Por la regla de oro #4 de STTM ("lo no implementado se dice 'pendiente',
nunca 'activo'"), este módulo NO debe describirse como "testigo RFC 3161
funcionando" hasta que alguien lo corra con red real y confirme la
respuesta de una TSA (ver INSTALACION.md, sección de validación manual).
Se ofrece igual, completo, porque el trabajo de construir el TSQ
correctamente es la parte que vale la pena tener lista — probarlo contra
un servidor real es un comando de una línea una vez que hay red.

Referencia: RFC 3161 (Time-Stamp Protocol), TSA pública de prueba
sugerida: https://freetsa.org/tsr (gratuita, sin registro, para pruebas).
"""
import os
import secrets
import struct
import urllib.request
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
OID_SHA256 = "2.16.840.1.101.3.4.2.1"

# --- Tags DER relevantes ---
TAG_BOOLEAN = 0x01
TAG_INTEGER = 0x02
TAG_OCTET_STRING = 0x04
TAG_NULL = 0x05
TAG_OID = 0x06
TAG_SEQUENCE = 0x30  # constructed


class ErrorDER(Exception):
    pass


# =========================== Codificador DER ===========================

def _codificar_longitud(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    partes = []
    while n:
        partes.append(n & 0xFF)
        n >>= 8
    partes.reverse()
    return bytes([0x80 | len(partes)]) + bytes(partes)


def _tlv(tag: int, contenido: bytes) -> bytes:
    return bytes([tag]) + _codificar_longitud(len(contenido)) + contenido


def codificar_entero(n: int) -> bytes:
    if n == 0:
        return _tlv(TAG_INTEGER, b"\x00")
    negativo = n < 0
    if negativo:
        raise ErrorDER("codificar_entero: enteros negativos no usados por STTM")
    largo = (n.bit_length() + 7) // 8
    b = n.to_bytes(largo, "big")
    if b[0] & 0x80:  # bit alto seteado: agregar 0x00 para no parecer negativo
        b = b"\x00" + b
    return _tlv(TAG_INTEGER, b)


def codificar_octet_string(datos: bytes) -> bytes:
    return _tlv(TAG_OCTET_STRING, datos)


def codificar_booleano(valor: bool) -> bytes:
    return _tlv(TAG_BOOLEAN, b"\xff" if valor else b"\x00")


def codificar_null() -> bytes:
    return _tlv(TAG_NULL, b"")


def codificar_secuencia(*elementos: bytes) -> bytes:
    return _tlv(TAG_SEQUENCE, b"".join(elementos))


def _base128(n: int) -> list:
    if n == 0:
        return [0]
    out = []
    while n:
        out.append(n & 0x7F)
        n >>= 7
    out.reverse()
    for i in range(len(out) - 1):
        out[i] |= 0x80
    return out


def codificar_oid(oid: str) -> bytes:
    arcos = [int(x) for x in oid.split(".")]
    if len(arcos) < 2 or arcos[0] > 2 or (arcos[0] < 2 and arcos[1] >= 40):
        raise ErrorDER(f"OID mal formado: {oid}")
    cuerpo = bytearray([40 * arcos[0] + arcos[1]])
    for arco in arcos[2:]:
        cuerpo.extend(_base128(arco))
    return _tlv(TAG_OID, bytes(cuerpo))


# =========================== Decodificador DER ===========================
# Genérico y mínimo: solo entiende definite-length (que es todo lo que
# emite este módulo). Sirve para el test de autoconsistencia y para leer
# lo justo y necesario de una TimeStampResp (ver extraer_estado_respuesta).

class NodoDER:
    __slots__ = ("tag", "contenido", "hijos")

    def __init__(self, tag, contenido, hijos):
        self.tag = tag
        self.contenido = contenido  # bytes crudos del value
        self.hijos = hijos          # lista de NodoDER si es constructed, si no []

    def __repr__(self):
        return f"NodoDER(tag=0x{self.tag:02x}, len={len(self.contenido)}, hijos={len(self.hijos)})"


def _leer_longitud(datos: bytes, i: int):
    primero = datos[i]
    i += 1
    if primero < 0x80:
        return primero, i
    num_bytes = primero & 0x7F
    if num_bytes == 0:
        raise ErrorDER("longitud indefinida (BER) no soportada, solo DER")
    valor = int.from_bytes(datos[i:i + num_bytes], "big")
    return valor, i + num_bytes


def decodificar_un_nodo(datos: bytes, i: int = 0):
    tag = datos[i]
    i += 1
    largo, i = _leer_longitud(datos, i)
    contenido = datos[i:i + largo]
    fin = i + largo
    es_constructed = bool(tag & 0x20) or tag == TAG_SEQUENCE
    hijos = []
    if es_constructed:
        j = 0
        while j < len(contenido):
            nodo, j = decodificar_un_nodo(contenido, j)
            hijos.append(nodo)
    return NodoDER(tag, contenido, hijos), fin


def decodificar(datos: bytes) -> NodoDER:
    nodo, fin = decodificar_un_nodo(datos, 0)
    if fin != len(datos):
        raise ErrorDER(
            f"quedan {len(datos) - fin} bytes sin consumir tras decodificar")
    return nodo


def decodificar_entero(nodo: NodoDER) -> int:
    if nodo.tag != TAG_INTEGER:
        raise ErrorDER(f"se esperaba INTEGER, vino tag 0x{nodo.tag:02x}")
    return int.from_bytes(nodo.contenido, "big", signed=True) if nodo.contenido else 0


def decodificar_oid(nodo: NodoDER) -> str:
    if nodo.tag != TAG_OID:
        raise ErrorDER(f"se esperaba OID, vino tag 0x{nodo.tag:02x}")
    b = nodo.contenido
    primero = b[0]
    arcos = [primero // 40, primero % 40]
    valor = 0
    for byte in b[1:]:
        valor = (valor << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            arcos.append(valor)
            valor = 0
    return ".".join(str(a) for a in arcos)


# =========================== TimeStampReq (RFC 3161 §2.4.1) ===========================

def construir_tsq(hash_sha256: bytes, incluir_certs: bool = True,
                   nonce: int = None) -> bytes:
    """Construye un TimeStampReq DER para un digest SHA-256 ya calculado.

    TimeStampReq ::= SEQUENCE {
        version        INTEGER { v1(1) },
        messageImprint MessageImprint,
        reqPolicy      TSAPolicyId OPTIONAL,       -- se omite (ninguna política específica)
        nonce          INTEGER OPTIONAL,
        certReq        BOOLEAN DEFAULT FALSE,
        extensions     [0] IMPLICIT Extensions OPTIONAL }  -- se omite

    MessageImprint ::= SEQUENCE {
        hashAlgorithm  AlgorithmIdentifier,
        hashedMessage  OCTET STRING }
    """
    if len(hash_sha256) != 32:
        raise ErrorDER(f"se esperaba un digest SHA-256 de 32 bytes, vinieron {len(hash_sha256)}")
    algoritmo = codificar_secuencia(codificar_oid(OID_SHA256), codificar_null())
    message_imprint = codificar_secuencia(algoritmo, codificar_octet_string(hash_sha256))
    if nonce is None:
        # 128 bits, con el bit más alto en 0 para evitar ambigüedad de signo en DER.
        nonce = secrets.randbits(127)
    partes = [codificar_entero(1), message_imprint, codificar_entero(nonce)]
    partes.append(codificar_booleano(incluir_certs))
    return codificar_secuencia(*partes)


def enviar_tsq(tsq_bytes: bytes, url: str = "https://freetsa.org/tsr",
               timeout: int = 15) -> bytes:
    """Envía el TSQ por HTTP y devuelve los bytes crudos de la respuesta.

    ⚠️ No probado end-to-end en este entorno (sin red saliente). La
    llamada HTTP en sí es estándar (POST con el content-type de RFC 3161);
    lo no verificado es si el TSQ que construimos es aceptado por una TSA
    real. Probar con: `python scripts/testigo_rfc3161.py probar <archivo>`
    desde un entorno CON red (ej. Termux).
    """
    req = urllib.request.Request(
        url, data=tsq_bytes, method="POST",
        headers={"Content-Type": "application/timestamp-query"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def extraer_estado_respuesta(tsr_bytes: bytes) -> dict:
    """Lee solo el PKIStatusInfo de una TimeStampResp (no valida la firma CMS).

    TimeStampResp ::= SEQUENCE { status PKIStatusInfo, timeStampToken ... }
    PKIStatusInfo ::= SEQUENCE { status INTEGER, ... }

    Verificar la firma criptográfica del token (CMS/PKCS#7 completo, con
    su cadena de certificados) es un parser mucho más grande y queda
    fuera del alcance de esta versión — declarado pendiente, no activo.
    Esta función solo confirma si la TSA aceptó o rechazó la petición.
    """
    raiz = decodificar(tsr_bytes)
    if raiz.tag != TAG_SEQUENCE or not raiz.hijos:
        raise ErrorDER("respuesta no tiene forma de TimeStampResp")
    pki_status_info = raiz.hijos[0]
    if not pki_status_info.hijos:
        raise ErrorDER("PKIStatusInfo vacío")
    status = decodificar_entero(pki_status_info.hijos[0])
    tiene_token = len(raiz.hijos) > 1
    return {"status": status, "concedido": status == 0, "tiene_token": tiene_token,
            "bytes_totales": len(tsr_bytes)}


if __name__ == "__main__":
    import argparse
    import hashlib
    import sys

    p = argparse.ArgumentParser(description="Testigo externo RFC 3161 (beta, no validado end-to-end).")
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("probar", help="Sellar un archivo contra una TSA real (requiere red)")
    pp.add_argument("archivo")
    pp.add_argument("--url", default="https://freetsa.org/tsr")
    args = p.parse_args()

    if args.cmd == "probar":
        datos = Path(args.archivo).read_bytes()
        digest = hashlib.sha256(datos).digest()
        tsq = construir_tsq(digest)
        print(f"📤 TSQ construido: {len(tsq)} bytes. Enviando a {args.url} ...")
        try:
            tsr = enviar_tsq(tsq, url=args.url)
        except Exception as e:
            print(f"❌ No se pudo contactar la TSA: {e}")
            sys.exit(1)
        try:
            estado = extraer_estado_respuesta(tsr)
        except ErrorDER as e:
            print(f"❌ Respuesta no se pudo interpretar: {e}")
            sys.exit(1)
        if estado["concedido"]:
            print(f"✅ Sello de tiempo CONCEDIDO ({estado['bytes_totales']} bytes de respuesta).")
        else:
            print(f"⚠️ La TSA respondió status={estado['status']} (no concedido).")
