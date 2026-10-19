#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
indice.py — Índice SQLite DERIVADO del ledger (STTM v0.4).

Principio de diseño (no negociable): el índice nunca es la fuente de
verdad. BITACORA.jsonl lo sigue siendo, siempre. El índice es una
proyección desechable para hacer rápido lo que hoy es lento (buscar
texto o filtrar por fecha implica leer y parsear el archivo entero
línea por línea — deuda declarada H6 del proyecto original).

Consecuencia práctica de este principio:
- Se puede borrar indice.db en cualquier momento sin perder nada:
  `reconstruir()` lo repuebla desde cero leyendo el JSONL.
- Nunca se escribe en el índice como parte del flujo de registro
  normal en esta versión (evita divergencia silenciosa); se reconstruye
  bajo demanda o por un job periódico. Ver INSTALACION.md para el cron
  sugerido.
- El índice NO valida firmas ni hashes — para eso sigue existiendo
  verificar.py. El índice solo sirve para encontrar rápido qué entrada
  mirar; la verificación criptográfica sigue siendo responsabilidad
  exclusiva de la cadena, nunca del índice.
"""
import json
import os
import re
import sqlite3
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _consulta_fts_segura(texto: str) -> str:
    """Convierte texto libre en una consulta FTS5 segura y predecible.

    Problema que resuelve: la sintaxis de consultas de FTS5 trata '-'
    como operador NOT y ':' como filtro de columna. Un texto libre común
    como "Ref-STTM-004" o un título con guiones rompe MATCH con un
    OperationalError (o, peor, devuelve resultados que no son los
    esperados) en vez de buscar esas palabras. Acá extraemos las
    palabras del texto ignorando la puntuación y las unimos como
    términos entrecomillados (AND implícito entre comillas): la persona
    que busca no necesita conocer la sintaxis de FTS5 para encontrar lo
    que escribió tal cual.
    """
    tokens = _TOKEN_RE.findall(texto)
    if not tokens:
        return '""'  # consulta vacía tras sanitizar: no matchea nada, no rompe
    return " ".join(f'"{t}"' for t in tokens)


def ruta_indice(proyecto_carpeta: Path) -> Path:
    return proyecto_carpeta / "indice.db"


def _conectar(ruta_db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(ruta_db))
    con.execute("""
        CREATE TABLE IF NOT EXISTS entradas (
            n INTEGER PRIMARY KEY,
            ts TEXT NOT NULL,
            titulo TEXT NOT NULL,
            detalle TEXT NOT NULL,
            firma_tipo TEXT,
            hash TEXT NOT NULL,
            actor TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_ts ON entradas(ts)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_actor ON entradas(actor)")
    # FTS5 para búsqueda de texto libre en título+detalle.
    con.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS entradas_fts
        USING fts5(titulo, detalle, content='entradas', content_rowid='n')
    """)
    return con


def reconstruir(ruta_bitacora: Path, ruta_db: Path) -> dict:
    """Reconstruye el índice desde cero a partir del JSONL. Idempotente."""
    if ruta_db.exists():
        ruta_db.unlink()
    con = _conectar(ruta_db)
    total = 0
    if ruta_bitacora.exists():
        with con:
            for linea in ruta_bitacora.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    e = json.loads(linea)
                except json.JSONDecodeError:
                    continue  # el índice es tolerante; verificar.py es quien juzga integridad
                con.execute(
                    "INSERT OR REPLACE INTO entradas "
                    "(n, ts, titulo, detalle, firma_tipo, hash, actor) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (e.get("n"), e.get("ts", ""), e.get("titulo", ""),
                     e.get("detalle", ""), e.get("firma_tipo"),
                     e.get("hash", ""), e.get("actor")))
                con.execute(
                    "INSERT OR REPLACE INTO entradas_fts (rowid, titulo, detalle) "
                    "VALUES (?, ?, ?)",
                    (e.get("n"), e.get("titulo", ""), e.get("detalle", "")))
                total += 1
    con.commit()
    con.close()
    return {"entradas_indexadas": total, "ruta_db": str(ruta_db)}


def buscar_texto(ruta_db: Path, consulta: str, limite: int = 20) -> list:
    if not ruta_db.exists():
        return []
    con = sqlite3.connect(str(ruta_db))
    con.row_factory = sqlite3.Row
    try:
        filas = con.execute(
            "SELECT e.n, e.ts, e.titulo, e.hash FROM entradas_fts f "
            "JOIN entradas e ON e.n = f.rowid "
            "WHERE entradas_fts MATCH ? ORDER BY e.n DESC LIMIT ?",
            (_consulta_fts_segura(consulta), limite)).fetchall()
    except sqlite3.OperationalError:
        # Consulta FTS con sintaxis inválida (ej. comillas sin cerrar):
        # se degrada a "sin resultados" en vez de romper el endpoint.
        return []
    finally:
        con.close()
    return [dict(f) for f in filas]


def por_rango_fecha(ruta_db: Path, desde: str, hasta: str, limite: int = 100) -> list:
    if not ruta_db.exists():
        return []
    con = sqlite3.connect(str(ruta_db))
    con.row_factory = sqlite3.Row
    filas = con.execute(
        "SELECT n, ts, titulo, hash, actor FROM entradas "
        "WHERE ts >= ? AND ts <= ? ORDER BY n ASC LIMIT ?",
        (desde, hasta, limite)).fetchall()
    con.close()
    return [dict(f) for f in filas]


def contar(ruta_db: Path) -> int:
    if not ruta_db.exists():
        return 0
    con = sqlite3.connect(str(ruta_db))
    n = con.execute("SELECT COUNT(*) FROM entradas").fetchone()[0]
    con.close()
    return n


if __name__ == "__main__":
    import argparse
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import rutas

    p = argparse.ArgumentParser(description="Índice SQLite derivado del ledger.")
    p.add_argument("--proyecto", type=int, default=1)
    p.add_argument("--buscar", default=None, help="Texto libre a buscar (FTS5)")
    args = p.parse_args()

    carpeta = rutas.carpeta_de(args.proyecto)
    ruta_bit = rutas.bitacora_de(args.proyecto)
    ruta_db = ruta_indice(carpeta)

    if args.buscar:
        for r in buscar_texto(ruta_db, args.buscar):
            print(f"  #{r['n']:<4} {r['ts']}  {r['titulo']}")
    else:
        res = reconstruir(ruta_bit, ruta_db)
        print(f"✅ Índice reconstruido: {res['entradas_indexadas']} entradas "
              f"en {res['ruta_db']}")
