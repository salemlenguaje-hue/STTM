#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
firma.py — Adaptador de firma para STTM (schema v2).

Reglas canónicas (incidente 001 mediante):
- HASH de contenido = SHA-256 sobre campos base SIN 'firma' y SIN 'hash'.
- FIRMA             = sobre campos base + 'hash', SIN 'firma'.
  (Una firma nunca se calcula sobre sí misma.)
- Compatibilidad: el verificador acepta la fórmula v1 (historia)
  y el HMAC legacy del incidente 001, como casos documentados.
"""
import hashlib
import hmac as modulo_hmac
import json
import os
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
CLAVES_DIR = RAIZ / "data" / "claves"

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    ED25519_DISPONIBLE = True
except Exception:
    ED25519_DISPONIBLE = False

# Campos que entran al hash de contenido (schema v2).
CAMPOS_BASE = ("n", "ts", "titulo", "detalle", "archivos",
               "commit_ref", "firma_tipo", "hash_prev")


def _texto(datos: dict) -> str:
    """Serialización canónica: claves ordenadas y UTF-8 sin escapes."""
    return json.dumps(datos, sort_keys=True, ensure_ascii=False)


def base_v2(entrada: dict) -> dict:
    """Campos canónicos sin firma y sin hash."""
    return {c: entrada.get(c) for c in CAMPOS_BASE}


def base_v1(entrada: dict) -> dict:
    """Fórmula histórica: incluía 'firma': None. Solo para verificar pasado."""
    d = base_v2(entrada)
    d["firma"] = None
    return d


def hash_contenido(entrada: dict) -> str:
    """Hash canónico v2."""
    return hashlib.sha256(_texto(base_v2(entrada)).encode("utf-8")).hexdigest()


def hash_contenido_v1(entrada: dict) -> str:
    """Hash histórico v1. Solo para compatibilidad hacia atrás."""
    return hashlib.sha256(_texto(base_v1(entrada)).encode("utf-8")).hexdigest()


def entrada_firmable(entrada: dict) -> dict:
    """Lo que cubre una firma: base v2 + hash, SIN el campo firma."""
    d = base_v2(entrada)
    d["hash"] = entrada.get("hash")
    return d


def hmac_firma(entrada: dict, clave: str) -> str:
    """Firma HMAC canónica (sobre entrada_firmable)."""
    return modulo_hmac.new(
        clave.encode("utf-8"),
        _texto(entrada_firmable(entrada)).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def hmac_firma_legacy(entrada: dict, clave: str) -> str:
    """Fórmula buggy del incidente 001: dict completo con firma=None.
    Se conserva SOLO para reconocer entradas ya firmadas así."""
    d = dict(entrada)
    d["firma"] = None
    return modulo_hmac.new(
        clave.encode("utf-8"),
        _texto(d).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def generar_claves_ed25519() -> tuple:
    """Genera un par de claves Ed25519. Retorna (privada_pem, publica_pem)."""
    if not ED25519_DISPONIBLE:
        raise RuntimeError("Ed25519 no disponible: instala cryptography de Termux")
    privada = Ed25519PrivateKey.generate()
    privada_pem = privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    publica_pem = privada.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return privada_pem, publica_pem


def ed25519_firmar(entrada: dict, privada_pem: bytes) -> bytes:
    """Firma Ed25519 canónica (sobre entrada_firmable)."""
    privada = serialization.load_pem_private_key(privada_pem, password=None)
    return privada.sign(_texto(entrada_firmable(entrada)).encode("utf-8"))


def ed25519_verificar(entrada: dict, firma_hex: str, publica_pem: bytes) -> bool:
    """Verifica una firma Ed25519 canónica."""
    publica = serialization.load_pem_public_key(publica_pem)
    try:
        publica.verify(
            bytes.fromhex(firma_hex),
            _texto(entrada_firmable(entrada)).encode("utf-8")
        )
        return True
    except Exception:
        return False


def ceremonia_claves():
    """Genera y guarda el par de claves en data/claves/."""
    CLAVES_DIR.mkdir(parents=True, exist_ok=True)
    privada_pem, publica_pem = generar_claves_ed25519()
    (CLAVES_DIR / "sofia_privada.pem").write_bytes(privada_pem)
    (CLAVES_DIR / "sofia_publica.pem").write_bytes(publica_pem)
    print(f"✅ Clave privada en: {CLAVES_DIR / 'sofia_privada.pem'} (NUNCA subir al repo)")
    print(f"✅ Clave pública en: {CLAVES_DIR / 'sofia_publica.pem'} (publicable)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ceremonia":
        ceremonia_claves()
    else:
        print("Uso: python scripts/firma.py ceremonia")
