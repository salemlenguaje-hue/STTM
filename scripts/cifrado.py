#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
cifrado.py — Crypto-shredding para STTM (ADR-STTM-007).

El problema que resuelve:
    STTM promete que el ledger es append-only e inmutable ("la bitácora
    es sagrada"). Una empresa con obligaciones de tipo GDPR / Ley 25.326
    (Argentina) en algún momento va a necesitar poder decir "borramos
    el dato personal de esta persona" de forma real y verificable —
    y un ledger genuinamente inmutable no puede borrar nada. Estos dos
    requisitos son, en apariencia, incompatibles.

La solución (estándar en sistemas de ledger con estos requisitos,
conocida como "crypto-shredding" o "crypto-erasure"):
    1. El contenido potencialmente personal de una entrada (el campo
       `detalle`) NO se guarda en texto plano en el JSONL. Se cifra
       con una clave simétrica (Fernet/AES-128-CBC+HMAC) generada UNA
       VEZ por entrada.
    2. Esa clave se guarda en un archivo aparte, chico, por entrada:
       data/claves/entradas/<n>.key (permisos 600).
    3. El ledger guarda: el ciphertext (o directamente su hash, según
       el modo elegido) y el hash del contenido en claro — así la
       cadena de integridad sigue intacta y verificable.
    4. "Triturar" una entrada = borrar SOLO su archivo .key. El
       ciphertext que queda en el ledger es, a partir de ese momento,
       ruido computacionalmente irrecuperable. La entrada (que existió,
       cuándo, con qué hash) permanece para siempre en la cadena — igual
       que cualquier evento en un ledger inmutable — pero su *contenido*
       ya no.

Lo que esto NO resuelve (límite declarado, no ocultado):
    - No borra el `titulo` de la entrada (se asume no-personal por
      convención; si un título contiene datos personales, es un error
      de uso, no algo que cifrado.py pueda detectar).
    - No es "olvido" en el sentido de que el evento desaparezca: cumple
      con "no se puede volver a acceder al dato personal", no con
      "nunca existió". Para la mayoría de los marcos de protección de
      datos esto es exactamente la distinción que aceptan (ver
      docs/07-cumplimiento/MAPEO-ESTANDARES.md), pero no es asesoría
      legal — un equipo de compliance real debe confirmarlo para su caso.
"""
import hashlib
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))


class ErrorCifrado(Exception):
    pass


def _ruta_clave(carpeta_claves: Path, n: int) -> Path:
    return carpeta_claves / f"{n}.key"


def cifrar_detalle(carpeta_claves: Path, n: int, detalle_claro: str) -> dict:
    """Cifra `detalle_claro` para la entrada n. Devuelve lo que va al ledger.

    Guarda la clave en carpeta_claves/<n>.key (0o600). Devuelve un dict
    con 'detalle_cifrado' (base64 de Fernet, seguro de guardar en JSON)
    y 'detalle_hash' (SHA-256 del texto EN CLARO, para que verificar.py
    pueda seguir comprobando integridad de contenido aun después de un
    triturado — el hash no se borra nunca, solo la clave que permite
    leer el texto).
    """
    carpeta_claves.mkdir(parents=True, exist_ok=True)
    clave = Fernet.generate_key()
    ruta = _ruta_clave(carpeta_claves, n)
    if ruta.exists():
        raise ErrorCifrado(f"ya existe una clave para la entrada #{n}: "
                            f"no se sobreescribe (evita perder acceso a datos vivos)")
    ruta.write_bytes(clave)
    os.chmod(ruta, 0o600)
    f = Fernet(clave)
    detalle_hash = hashlib.sha256(detalle_claro.encode("utf-8")).hexdigest()
    detalle_cifrado = f.encrypt(detalle_claro.encode("utf-8")).decode("ascii")
    return {"detalle_cifrado": detalle_cifrado, "detalle_hash": detalle_hash}


def descifrar_detalle(carpeta_claves: Path, n: int, detalle_cifrado: str) -> str:
    """Devuelve el texto en claro, o lanza ErrorCifrado si fue triturado."""
    ruta = _ruta_clave(carpeta_claves, n)
    if not ruta.exists():
        raise ErrorCifrado(
            f"entrada #{n}: sin clave disponible (triturada o nunca cifrada). "
            f"El contenido es irrecuperable por diseño.")
    clave = ruta.read_bytes()
    f = Fernet(clave)
    try:
        return f.decrypt(detalle_cifrado.encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise ErrorCifrado(f"entrada #{n}: token cifrado inválido o corrupto")


def triturar(carpeta_claves: Path, n: int) -> bool:
    """Borra la clave de la entrada n. Devuelve True si había algo que borrar.

    Después de esto, descifrar_detalle(n) siempre falla: es irreversible
    por construcción, no por política (no hay backup de la clave en
    ningún otro lugar de STTM — si el usuario hizo su propio backup del
    directorio de claves, esa es una decisión fuera del alcance de esta
    herramienta, y se documenta así en AYUDA.md).
    """
    ruta = _ruta_clave(carpeta_claves, n)
    if not ruta.exists():
        return False
    ruta.unlink()
    return True


def esta_triturada(carpeta_claves: Path, n: int) -> bool:
    return not _ruta_clave(carpeta_claves, n).exists()


def registrar_triturado_en_manifiesto(carpeta_claves: Path, n: int, motivo: str) -> Path:
    """Deja constancia local (fuera del ledger) de cuándo y por qué se trituró.

    No va en el ledger porque el ledger es append-only y esto no es un
    evento de negocio del proyecto auditado — es una acción de
    administración de datos personales. Vive en un manifiesto aparte,
    pensado para mostrarlo a un DPO/auditor de privacidad si lo piden.
    """
    import time
    ruta = carpeta_claves / "_triturados.jsonl"
    entrada = {
        "n": n, "motivo": motivo,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    os.chmod(ruta, 0o600)
    return ruta
