#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
identidad.py — Usuarios, roles, sesiones y claves por persona (STTM v0.4).

Resuelve la deuda enterprise más grande de STTM v0.3: `solicitante` y
`ejecutado_por` eran literalmente el nombre del autor, hardcodeado en
auditar.py. Sin identidad real por persona, "quién hizo qué" —el corazón
de cualquier sistema de trazabilidad— no existía.

Diseño:
- Cada usuario tiene: nombre_usuario único, rol, hash de contraseña
  (PBKDF2-HMAC-SHA256, 600.000 iteraciones — recomendación OWASP 2023
  para cuando no hay Argon2/bcrypt disponibles, como en este entorno),
  y SU PROPIO par de claves Ed25519 (data/claves/usuarios/<usuario>_privada.pem,
  con os.chmod 0o600). Reemplaza el patrón anterior de una sola clave
  compartida ("sofia_*") para todo el proyecto.
- Roles (ADR-STTM-004): lector, auditor, admin. Jerárquicos: admin
  incluye los permisos de auditor, que incluye los de lector.
- Sesiones: token opaco (secrets.token_hex, 256 bits) con expiración,
  guardado en memoria del proceso servidor (data/sesiones.json como
  respaldo simple para reinicios; no es un JWT ni pretende serlo).

Límites declarados (honestidad técnica, regla de oro #4 del proyecto):
- PBKDF2 vía hashlib, no Argon2id: este entorno de desarrollo no tiene
  acceso de red para instalar `argon2-cffi`. PBKDF2-HMAC-SHA256 con
  600k iteraciones es una opción defendible (así lo indica OWASP), pero
  Argon2id es preferible en producción si el entorno de despliegue lo
  permite. Ver INSTALACION.md.
- No hay recuperación de contraseña por email (no hay servidor de correo
  en el alcance de esta versión): un admin puede resetear a otro usuario.
- No hay 2FA. Declarado pendiente, no activo.
"""
import hashlib
import json
import os
import secrets
import time
from pathlib import Path

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
USUARIOS_JSON = RAIZ / "data" / "usuarios.json"
CLAVES_USUARIOS_DIR = RAIZ / "data" / "claves" / "usuarios"
SESIONES_JSON = RAIZ / "data" / "sesiones.json"

ITERACIONES_PBKDF2 = 600_000
TTL_SESION_SEGUNDOS = 12 * 3600  # 12 horas

ROLES = ("lector", "auditor", "admin")
# Jerarquía explícita: cada rol hereda los permisos de los anteriores.
JERARQUIA_ROLES = {"lector": 0, "auditor": 1, "admin": 2}

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    ED25519_DISPONIBLE = True
except Exception:
    ED25519_DISPONIBLE = False


class ErrorIdentidad(Exception):
    pass


def _cargar_usuarios() -> dict:
    if not USUARIOS_JSON.exists():
        return {}
    return json.loads(USUARIOS_JSON.read_text(encoding="utf-8"))


def _guardar_usuarios(datos: dict):
    USUARIOS_JSON.parent.mkdir(parents=True, exist_ok=True)
    USUARIOS_JSON.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    os.chmod(USUARIOS_JSON, 0o600)


def _hash_password(password: str, sal: bytes = None) -> tuple:
    sal = sal or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal,
                             ITERACIONES_PBKDF2)
    return sal.hex(), h.hex()


def _verificar_password(password: str, sal_hex: str, hash_hex: str) -> bool:
    _, h = _hash_password(password, bytes.fromhex(sal_hex))
    return secrets.compare_digest(h, hash_hex)


def _generar_claves_usuario(nombre_usuario: str) -> str:
    """Genera un par Ed25519 propio para este usuario. Devuelve fingerprint."""
    if not ED25519_DISPONIBLE:
        return ""
    CLAVES_USUARIOS_DIR.mkdir(parents=True, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    ruta_priv = CLAVES_USUARIOS_DIR / f"{nombre_usuario}_privada.pem"
    ruta_pub = CLAVES_USUARIOS_DIR / f"{nombre_usuario}_publica.pem"
    ruta_priv.write_bytes(priv_pem)
    os.chmod(ruta_priv, 0o600)
    ruta_pub.write_bytes(pub_pem)
    fingerprint = hashlib.sha256(pub_pem).hexdigest()[:16]
    return fingerprint


def crear_usuario(nombre_usuario: str, password: str, rol: str,
                   nombre_completo: str = "") -> dict:
    if rol not in ROLES:
        raise ErrorIdentidad(f"rol inválido: {rol} (opciones: {ROLES})")
    if not nombre_usuario or not password:
        raise ErrorIdentidad("nombre_usuario y password son obligatorios")
    if len(password) < 10:
        raise ErrorIdentidad("password demasiado corta (mínimo 10 caracteres)")
    usuarios = _cargar_usuarios()
    if nombre_usuario in usuarios:
        raise ErrorIdentidad(f"el usuario '{nombre_usuario}' ya existe")
    sal_hex, hash_hex = _hash_password(password)
    fingerprint = _generar_claves_usuario(nombre_usuario)
    usuarios[nombre_usuario] = {
        "nombre_completo": nombre_completo or nombre_usuario,
        "rol": rol,
        "sal": sal_hex,
        "hash": hash_hex,
        "fingerprint_clave": fingerprint,
        "creado_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "activo": True,
    }
    _guardar_usuarios(usuarios)
    return {"nombre_usuario": nombre_usuario, "rol": rol,
            "fingerprint_clave": fingerprint}


def autenticar(nombre_usuario: str, password: str) -> dict:
    usuarios = _cargar_usuarios()
    u = usuarios.get(nombre_usuario)
    if not u or not u.get("activo", True):
        raise ErrorIdentidad("usuario o contraseña inválidos")
    if not _verificar_password(password, u["sal"], u["hash"]):
        raise ErrorIdentidad("usuario o contraseña inválidos")
    return crear_sesion(nombre_usuario, u["rol"])


def crear_sesion(nombre_usuario: str, rol: str) -> dict:
    sesiones = _cargar_sesiones()
    token = secrets.token_hex(32)
    expira = time.time() + TTL_SESION_SEGUNDOS
    sesiones[token] = {"usuario": nombre_usuario, "rol": rol, "expira": expira}
    _guardar_sesiones(sesiones)
    return {"token": token, "usuario": nombre_usuario, "rol": rol,
            "expira_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expira))}


def _cargar_sesiones() -> dict:
    if not SESIONES_JSON.exists():
        return {}
    try:
        return json.loads(SESIONES_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _guardar_sesiones(datos: dict):
    SESIONES_JSON.parent.mkdir(parents=True, exist_ok=True)
    SESIONES_JSON.write_text(json.dumps(datos), encoding="utf-8")
    os.chmod(SESIONES_JSON, 0o600)


def validar_token(token: str):
    """Devuelve {"usuario", "rol"} si el token es válido y no expiró, o None."""
    if not token:
        return None
    sesiones = _cargar_sesiones()
    s = sesiones.get(token)
    if not s:
        return None
    if time.time() > s["expira"]:
        del sesiones[token]
        _guardar_sesiones(sesiones)
        return None
    return {"usuario": s["usuario"], "rol": s["rol"]}


def cerrar_sesion(token: str):
    sesiones = _cargar_sesiones()
    if token in sesiones:
        del sesiones[token]
        _guardar_sesiones(sesiones)


def rol_alcanza(rol_usuario: str, rol_requerido: str) -> bool:
    """True si rol_usuario tiene al menos el nivel de rol_requerido."""
    return JERARQUIA_ROLES.get(rol_usuario, -1) >= JERARQUIA_ROLES.get(rol_requerido, 99)


def listar_usuarios() -> list:
    """Lista usuarios SIN datos de autenticación (para UI/auditoría)."""
    usuarios = _cargar_usuarios()
    return [
        {"nombre_usuario": nu, "nombre_completo": u["nombre_completo"],
         "rol": u["rol"], "fingerprint_clave": u.get("fingerprint_clave", ""),
         "activo": u.get("activo", True), "creado_utc": u.get("creado_utc")}
        for nu, u in sorted(usuarios.items())
    ]


def desactivar_usuario(nombre_usuario: str):
    usuarios = _cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise ErrorIdentidad(f"usuario '{nombre_usuario}' no existe")
    usuarios[nombre_usuario]["activo"] = False
    _guardar_usuarios(usuarios)


def firmar_como(nombre_usuario: str, texto_canonico: bytes) -> str:
    """Firma con la clave privada PROPIA de este usuario. Devuelve hex."""
    if not ED25519_DISPONIBLE:
        raise ErrorIdentidad("Ed25519 no disponible en este entorno")
    ruta = CLAVES_USUARIOS_DIR / f"{nombre_usuario}_privada.pem"
    if not ruta.exists():
        raise ErrorIdentidad(f"el usuario '{nombre_usuario}' no tiene clave propia")
    priv = serialization.load_pem_private_key(ruta.read_bytes(), password=None)
    return priv.sign(texto_canonico).hex()


def verificar_firma_de(nombre_usuario: str, texto_canonico: bytes, firma_hex: str) -> bool:
    if not ED25519_DISPONIBLE:
        return False
    ruta_pub = CLAVES_USUARIOS_DIR / f"{nombre_usuario}_publica.pem"
    if not ruta_pub.exists():
        return False
    pub = serialization.load_pem_public_key(ruta_pub.read_bytes())
    try:
        pub.verify(bytes.fromhex(firma_hex), texto_canonico)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import argparse
    import getpass
    p = argparse.ArgumentParser(description="Gestión de usuarios STTM.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("crear", help="Crear un usuario nuevo")
    pc.add_argument("nombre_usuario")
    pc.add_argument("--rol", choices=ROLES, default="lector")
    pc.add_argument("--nombre-completo", default="")

    sub.add_parser("listar", help="Listar usuarios")

    pd = sub.add_parser("desactivar", help="Desactivar un usuario")
    pd.add_argument("nombre_usuario")

    args = p.parse_args()
    if args.cmd == "crear":
        pwd = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
        pwd2 = getpass.getpass("Repetir contraseña: ")
        if pwd != pwd2:
            print("❌ Las contraseñas no coinciden.")
            raise SystemExit(1)
        try:
            r = crear_usuario(args.nombre_usuario, pwd, args.rol, args.nombre_completo)
            print(f"✅ Usuario creado: {r['nombre_usuario']} (rol={r['rol']}, "
                  f"clave={r['fingerprint_clave'] or 'sin Ed25519'})")
        except ErrorIdentidad as e:
            print(f"❌ {e}")
            raise SystemExit(1)
    elif args.cmd == "listar":
        for u in listar_usuarios():
            estado = "activo" if u["activo"] else "desactivado"
            print(f"  {u['nombre_usuario']:<20} rol={u['rol']:<8} "
                  f"clave={u['fingerprint_clave'] or '—':<18} {estado}")
    elif args.cmd == "desactivar":
        try:
            desactivar_usuario(args.nombre_usuario)
            print(f"✅ Usuario '{args.nombre_usuario}' desactivado.")
        except ErrorIdentidad as e:
            print(f"❌ {e}")
            raise SystemExit(1)
