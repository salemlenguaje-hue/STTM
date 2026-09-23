#!/usr/bin/env python3
"""
proyectos.py — Gestor del catálogo de proyectos STTM (ADR-003).

El catálogo es append-only: cada línea de data/proyectos.jsonl es
una entrada de creación o una entrada de actualización. El estado
actual se reconstruye leyendo todo en orden y aplicando las acciones.

Reglas ADR-003 que respeta:
- n es estable y nunca se reutiliza.
- Correcciones = entrada nueva con accion=actualizar.
- Desactivar no borra, solo marca activo=false.

Uso:
    python scripts/proyectos.py listar
    python scripts/proyectos.py crear --titulo T --descripcion D [--ref R] [--nivel N]
    python scripts/proyectos.py nivel --n 1 --nivel salem --motivo M
    python scripts/proyectos.py desactivar --n 2 --motivo M
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
CATALOGO = RAIZ / "data" / "proyectos.jsonl"

NIVELES = ("simple", "continuidad", "salem")

CAMPOS_CREACION = ("n", "ref_interna", "titulo", "descripcion", "creado_utc",
                   "nivel_inicial", "nivel_actual", "primera_auditoria_utc",
                   "ultima_auditoria_utc", "activo")


def ahora_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def leer_lineas():
    if not CATALOGO.exists():
        return []
    lineas = []
    for linea in CATALOGO.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea:
            lineas.append(json.loads(linea))
    return lineas


def cargar_estado():
    """Reconstruye el estado actual aplicando entradas en orden."""
    estado = {}
    for entrada in leer_lineas():
        n = entrada.get("n")
        if entrada.get("accion") == "actualizar":
            if n in estado:
                estado[n].update(entrada.get("cambios", {}))
        else:
            estado[n] = {k: entrada.get(k) for k in CAMPOS_CREACION}
    return estado


def proximo_n(estado):
    return (max(estado.keys()) + 1) if estado else 1


def agregar(entrada):
    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    with CATALOGO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def cmd_listar(args):
    estado = cargar_estado()
    if not estado:
        print("Catálogo vacío.")
        return 0
    for n in sorted(estado):
        p = estado[n]
        marca = "" if p.get("activo") else "  [INACTIVO]"
        ref = p.get("ref_interna") or "-"
        print(f"#{n}  {ref}  |  {p.get('titulo')}  |  nivel={p.get('nivel_actual')}{marca}")
    return 0


def cmd_crear(args):
    if args.nivel not in NIVELES:
        print(f"❌ Nivel inválido: {args.nivel}. Válidos: {', '.join(NIVELES)}")
        return 1
    estado = cargar_estado()
    n = proximo_n(estado)
    entrada = {
        "n": n,
        "ref_interna": args.ref,
        "titulo": args.titulo,
        "descripcion": args.descripcion,
        "creado_utc": ahora_utc(),
        "nivel_inicial": args.nivel,
        "nivel_actual": args.nivel,
        "primera_auditoria_utc": None,
        "ultima_auditoria_utc": None,
        "activo": True,
    }
    agregar(entrada)
    print(f"✅ Proyecto #{n} creado: {args.titulo} (nivel inicial: {args.nivel})")
    print("Recordá registrar este hito en la bitácora:")
    print(f'  python scripts/registrar.py "Proyecto #{n} creado: {args.titulo}" '
          f'"Detalle del nuevo proyecto." --archivos "data/proyectos.jsonl" --modo-firma ed25519')
    return 0


def cmd_nivel(args):
    if args.nivel not in NIVELES:
        print(f"❌ Nivel inválido: {args.nivel}. Válidos: {', '.join(NIVELES)}")
        return 1
    estado = cargar_estado()
    if args.n not in estado:
        print(f"❌ No existe el proyecto #{args.n}")
        return 1
    entrada = {
        "accion": "actualizar",
        "n": args.n,
        "ts": ahora_utc(),
        "cambios": {"nivel_actual": args.nivel},
        "motivo": args.motivo,
    }
    agregar(entrada)
    print(f"✅ Proyecto #{args.n} ahora en nivel: {args.nivel}")
    print("Recordá registrar este cambio en la bitácora.")
    return 0


def cmd_desactivar(args):
    estado = cargar_estado()
    if args.n not in estado:
        print(f"❌ No existe el proyecto #{args.n}")
        return 1
    entrada = {
        "accion": "actualizar",
        "n": args.n,
        "ts": ahora_utc(),
        "cambios": {"activo": False},
        "motivo": args.motivo,
    }
    agregar(entrada)
    print(f"✅ Proyecto #{args.n} marcado como inactivo (no borrado).")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Gestor del catálogo de proyectos STTM.")
    sub = parser.add_subparsers(dest="comando")

    sub.add_parser("listar", help="Lista proyectos activos e inactivos.")

    p_crear = sub.add_parser("crear", help="Crea un proyecto nuevo.")
    p_crear.add_argument("--titulo", required=True)
    p_crear.add_argument("--descripcion", required=True)
    p_crear.add_argument("--ref", default=None)
    p_crear.add_argument("--nivel", default="simple")

    p_nivel = sub.add_parser("nivel", help="Cambia el nivel de un proyecto.")
    p_nivel.add_argument("--n", type=int, required=True)
    p_nivel.add_argument("--nivel", required=True)
    p_nivel.add_argument("--motivo", default="")

    p_des = sub.add_parser("desactivar", help="Marca un proyecto como inactivo.")
    p_des.add_argument("--n", type=int, required=True)
    p_des.add_argument("--motivo", default="")

    args = parser.parse_args()

    if args.comando == "listar":
        return cmd_listar(args)
    if args.comando == "crear":
        return cmd_crear(args)
    if args.comando == "nivel":
        return cmd_nivel(args)
    if args.comando == "desactivar":
        return cmd_desactivar(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
