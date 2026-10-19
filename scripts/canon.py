#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
canon.py — Canonicalización JSON según RFC 8785 (JCS) para STTM schema v3.

Por qué existe (deuda declarada H7 del proyecto original):
    Las versiones v1/v2 usaban json.dumps(sort_keys=True, ensure_ascii=False),
    que es determinístico *dentro de Python* pero no es un estándar
    interoperable: un verificador escrito en Go, Rust o JS tendría que
    replicar exactamente el comportamiento del serializador de CPython
    para llegar al mismo hash. Eso rompe la promesa central de STTM
    ("cualquiera puede verificar, sin depender de este código").

    RFC 8785 (JSON Canonicalization Scheme) es un estándar del IETF que
    define una única representación textual posible para un valor JSON.
    Cualquier implementación conforme, en cualquier lenguaje, produce
    byte-a-byte el mismo resultado.

Alcance de esta implementación:
    STTM solo canonicaliza sus propias entradas de bitácora: dict con
    claves string y valores que son string, int, bool, None, list o dict
    anidado de esos mismos tipos. Esta implementación cubre exactamente
    ese subconjunto — no es un serializador JCS de propósito general
    (no cubre float con notación exponencial, ni Unicode fuera del BMP
    con pares subrogados en claves, casos que STTM no produce).
    Se declara así explícitamente para no prometer más de lo que se probó.

Reglas aplicadas (RFC 8785 §3.2.3 para objetos, §3.2.2 para strings):
    - Las claves de un objeto se ordenan por comparación de code points
      UTF-16 (para ASCII, que es lo único que usa STTM, coincide con el
      orden lexicográfico simple de Python).
    - Sin espacios: separadores "," y ":" exactos, sin whitespace.
    - Strings: escapes mínimos de RFC 8259 (comillas, backslash, y
      controles \\b \\f \\n \\r \\t; el resto de caracteres de control
      como \\u00XX). Sin escapar caracteres no-ASCII (UTF-8 directo).
    - Enteros: forma decimal simple, sin '+', sin ceros a la izquierda.
    - No se admiten float en esta implementación: STTM no los usa en
      campos de firma, y la forma canónica de float en JCS (ECMAScript
      Number-to-String) es una fuente conocida de bugs de interoperabilidad
      que no vale la pena introducir sin necesidad real.
"""
import re

_ESCAPES = {
    '"': '\\"', '\\': '\\\\',
    '\b': '\\b', '\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t',
}
_CONTROL_RE = re.compile(r'[\x00-\x1f]')


def _escapar_control(m):
    c = m.group(0)
    return _ESCAPES.get(c, f'\\u{ord(c):04x}')


def _codificar_string(s: str) -> str:
    partes = []
    i = 0
    for ch in s:
        if ch in _ESCAPES:
            partes.append(_ESCAPES[ch])
        elif ch < '\x20':
            partes.append(f'\\u{ord(ch):04x}')
        else:
            partes.append(ch)
    return '"' + ''.join(partes) + '"'


def _codificar_valor(v) -> str:
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        # bool ya se descartó arriba; acá solo enteros reales.
        return str(v)
    if isinstance(v, float):
        raise TypeError(
            "canon.py (JCS v3) no admite float: STTM no los usa en "
            "campos firmables. Si esto aparece, es una entrada mal "
            "formada, no un caso a soportar silenciosamente.")
    if isinstance(v, str):
        return _codificar_string(v)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_codificar_valor(x) for x in v) + "]"
    if isinstance(v, dict):
        claves = sorted(v.keys())  # orden UTF-16 == orden Python para ASCII
        piezas = (f'{_codificar_string(k)}:{_codificar_valor(v[k])}' for k in claves)
        return "{" + ",".join(piezas) + "}"
    raise TypeError(f"canon.py (JCS v3): tipo no soportado: {type(v).__name__}")


def canonicalizar(datos: dict) -> str:
    """Serializa `datos` a su forma canónica JCS (RFC 8785), como texto."""
    return _codificar_valor(datos)


def canonicalizar_bytes(datos: dict) -> bytes:
    """Forma canónica codificada en UTF-8, lista para hashear o firmar."""
    return canonicalizar(datos).encode("utf-8")
