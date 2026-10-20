#!/usr/bin/env python3
# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
servidor.py — API local + estáticos del visor STTM (ADR-002, v3 multi-proyecto K-001).

Cambios v3:
- Todos los endpoints de evidencia aceptan ?proyecto=N (GET) o
  "proyecto": N (POST). Por defecto, proyecto 1.
- Los subprocess (registrar.py, auditar.py) reciben STTM_PROYECTO=N
  solo en su propio entorno: sin estado global, sin carreras.
- /api/auditorias filtra por meta.json proyecto_n; las auditorías
  previas a ADR-003 (sin meta) se atribuyen al proyecto 1 (declarado).
- Documentos (docs/) siguen siendo GLOBALES del repo: son gobernanza,
  no evidencia por proyecto. Divergencia con la visión ADR-003 declarada.

Lectura:
  GET  /api/bitacora?proyecto=N
  GET  /api/proyecto?n=N
  GET  /api/documentos | /api/documento?ruta=      (globales)
  GET  /api/auditorias?proyecto=N
  GET  /api/reporte?carpeta=
  GET  /api/verificar-paquete?carpeta=&proyecto=N
Escritura:
  POST /api/registrar   {"proyecto": N, ...}
  POST /api/modo        {"n": N, "nivel": ...}
  POST /api/documento   (global)
  POST /api/auditar     {"proyecto": N, ...}

Seguridad: sin shell; rutas .md solo bajo docs/ o CONTINUIDAD.md sin '..';
nombres de carpeta de auditoría con regex estricta; loopback por defecto.
"""
import argparse
import hashlib
import http.server
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(os.environ.get("STTM_ROOT", Path(__file__).resolve().parent.parent))
WEB = RAIZ / "web"
SCRIPTS = RAIZ / "scripts"
DOCS = RAIZ / "docs"
AUDITORIAS = RAIZ / "auditorias"

sys.path.insert(0, str(SCRIPTS))
import verificar as mod_verificar  # verificación estructurada
import rutas                       # resolución de carpetas por proyecto
import identidad                   # STTM v0.4: usuarios, roles, sesiones
import indice                      # STTM v0.4: índice SQLite derivado

RE_CARPETA = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")
MODOS = ("simple", "continuidad", "salem")
MODOS_FIRMA = ("hash", "hmac", "ed25519", "ed25519_actor")

# --- Rate limiting simple de /api/login (en memoria, por proceso) ---
# No pretende ser una defensa de nivel producción distribuida (eso
# requeriría un store compartido tipo Redis si hay más de un proceso
# servidor detrás de un balanceador). Para el caso de uso real de STTM
# —un servidor único, self-hosted, por equipo u organización— esto ya
# corta un ataque de fuerza bruta trivial. Declarado como suficiente
# para v0.4, no como "protección enterprise contra DDoS de login".
#
# Clave = (ip, usuario), NO solo ip: en el taller de la escuela (CEP 40),
# decenas de alumnos van a compartir la misma IP de red local. Si el
# límite fuera por IP sola, un alumno que se equivoca de contraseña
# varias veces bloquearía el login de toda el aula durante 15 minutos.
# Por usuario, cada quien se bloquea solo a sí mismo.
_INTENTOS_LOGIN = {}  # (ip, usuario) -> [timestamps de intentos fallidos]
LIMITE_INTENTOS = 5
VENTANA_BLOQUEO_SEGUNDOS = 15 * 60


def _login_bloqueado(ip: str, usuario: str) -> bool:
    clave = (ip, usuario)
    ahora = time.time()
    intentos = [t for t in _INTENTOS_LOGIN.get(clave, []) if ahora - t < VENTANA_BLOQUEO_SEGUNDOS]
    _INTENTOS_LOGIN[clave] = intentos
    return len(intentos) >= LIMITE_INTENTOS


def _registrar_intento_fallido(ip: str, usuario: str):
    _INTENTOS_LOGIN.setdefault((ip, usuario), []).append(time.time())


def correr_script(nombre, *args, proyecto=None):
    env = os.environ.copy()
    env["STTM_ROOT"] = str(RAIZ)
    if proyecto is not None:
        env["STTM_PROYECTO"] = str(proyecto)
    # H5: timeout para que un script colgado no congele el hilo del servidor.
    # Configurable vía STTM_SCRIPT_TIMEOUT (default 30s) para permitir
    # valores cortos en los tests.
    timeout = int(os.environ.get("STTM_SCRIPT_TIMEOUT", "30"))
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / nombre), *args],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
        # H4: sanitizar stderr para no filtrar paths absolutos al cliente.
        r.stderr = sanitizar(r.stderr)
        return r
    except subprocess.TimeoutExpired:
        # Un script que excede el timeout se reporta como fallo, sin
        # colgar el servidor ni propagar la excepción a los endpoints.
        return subprocess.CompletedProcess(
            args=[nombre], returncode=-1, stdout="",
            stderr=f"timeout: el script {nombre} excedió {timeout} segundos")


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def ruta_documento_valida(ruta_rel):
    if not ruta_rel or ".." in ruta_rel.split("/"):
        return None
    candidata = (RAIZ / ruta_rel).resolve()
    try:
        candidata.relative_to(RAIZ.resolve())
    except ValueError:
        return None
    if candidata.suffix.lower() != ".md":
        return None
    bajo_docs = False
    try:
        candidata.relative_to((RAIZ / "docs").resolve())
        bajo_docs = True
    except ValueError:
        pass
    es_continuidad = candidata == (RAIZ / "CONTINUIDAD.md").resolve()
    return candidata if (bajo_docs or es_continuidad) else None


def siguiente_numero(carpeta, prefijo):
    nums = [0]
    for p in carpeta.glob(prefijo + "-*"):
        m = re.match(re.escape(prefijo) + r"-STTM-(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1


def slug(texto):
    s = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return s or "sin-titulo"


def proyecto_de_query(q, clave="proyecto"):
    try:
        return int(q.get(clave, ["1"])[0])
    except ValueError:
        return None


# H4: regex para detectar paths absolutos Unix de 2+ componentes.
# Ej: /data/data/com.termux/... → "...". No matchea "/a" solo (muy corto).
RE_PATH_ABSOLUTO = re.compile(r'(?:/[a-zA-Z0-9_.\-]+){2,}')


def sanitizar(texto):
    """H4: evitar filtrar paths absolutos del sistema en respuestas al cliente.

    Reemplaza paths absolutos por '...' y trunca a 500 caracteres para
    evitar respuestas gigantes. No afecta el contenido útil del mensaje.
    """
    texto = RE_PATH_ABSOLUTO.sub("...", texto)
    MAX = 500
    if len(texto) > MAX:
        texto = texto[:MAX] + "..."
    return texto


class STTMHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt, *a):
        pass

    def send_header(self, keyword, value):
        # PC-013: el navegador móvil servía JS viejo tras un deploy y la
        # UI nueva parecía rota sin errores. STTM es herramienta local:
        # los estáticos se sirven sin caché, siempre frescos.
        super().send_header(keyword, value)
        tipo = value.split(";")[0].strip() if keyword == "Content-type" else ""
        if tipo in ("text/html", "text/css",
                    "application/javascript", "text/javascript"):
            super().send_header("Cache-Control", "no-store")

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_texto(self, texto, code=200):
        body = texto.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------------- STTM v0.4: autenticación y autorización ----------------
    def _token_de_header(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        return None

    def _autorizar(self, rol_minimo="lector"):
        """Exige un token de sesión válido con al menos `rol_minimo`.

        Si falla, ya envió la respuesta HTTP (401/403) y devuelve None:
        el llamador debe hacer `if not info: return`.
        """
        info = identidad.validar_token(self._token_de_header())
        if not info:
            self.send_json({"error": "no autenticado: token ausente o expirado"}, 401)
            return None
        if not identidad.rol_alcanza(info["rol"], rol_minimo):
            self.send_json({"error": f"permisos insuficientes (requiere rol {rol_minimo})"}, 403)
            return None
        return info

    def leer_json(self):
        largo = int(self.headers.get("Content-Length", 0))
        LIMITE_JSON = 10 * 1024 * 1024  # 10 MB
        if largo > LIMITE_JSON:
            self.send_json({"error": f"JSON demasiado grande (máximo {LIMITE_JSON} bytes)"}, 413)
            self._respondido = True  # evita una segunda respuesta en do_POST
            return None
        crudo = self.rfile.read(largo) if largo else b"{}"
        try:
            return json.loads(crudo.decode("utf-8"))
        except Exception:
            return None

    # ---------------- lectura ----------------
    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)

        if parsed.path == "/api/bitacora":
            if not self._autorizar("lector"): return
            n = proyecto_de_query(q)
            if n is None:
                return self.send_json({"error": "proyecto invalido"}, 400)
            try:
                ruta_bit = rutas.bitacora_de(n)
            except RuntimeError as e:
                return self.send_json({"error": str(e)}, 404)
            entradas = []
            if ruta_bit.exists():
                for linea in ruta_bit.read_text(encoding="utf-8").splitlines():
                    if linea.strip():
                        entradas.append(json.loads(linea))
            return self.send_json(entradas[::-1])

        if parsed.path == "/api/proyecto":
            if not self._autorizar("lector"): return
            r = correr_script("proyectos.py", "listar", "--json")
            if r.returncode != 0:
                return self.send_json({"error": r.stderr.strip()}, 500)
            lista = json.loads(r.stdout)
            activos = [p for p in lista if p.get("activo")]
            if not activos:
                return self.send_json({"error": "no hay proyectos activos"}, 404)
            n = q.get("n", [str(activos[0]["n"])])[0]
            elegido = next((p for p in lista if str(p.get("n")) == n), None)
            if elegido is None:
                return self.send_json({"error": f"proyecto {n} no existe"}, 404)
            return self.send_json({"proyecto": elegido, "activos": activos})

        if parsed.path == "/api/proyecto/crear":
            return self.send_json({"error": "solo POST"}, 405)

        if parsed.path == "/api/documentos":
            if not self._autorizar("lector"): return
            docs = [str(p.relative_to(RAIZ)) for p in DOCS.rglob("*.md")]
            if (RAIZ / "CONTINUIDAD.md").exists():
                docs.append("CONTINUIDAD.md")
            return self.send_json(sorted(docs))

        if parsed.path == "/api/documento":
            if not self._autorizar("lector"): return
            ruta = ruta_documento_valida(q.get("ruta", [""])[0])
            if ruta is None or not ruta.exists():
                return self.send_json({"error": "ruta no autorizada o inexistente"}, 404)
            return self.send_texto(ruta.read_text(encoding="utf-8"))

        if parsed.path == "/api/auditorias":
            if not self._autorizar("lector"): return
            n = proyecto_de_query(q)
            if n is None:
                return self.send_json({"error": "proyecto invalido"}, 400)
            salida = []
            if AUDITORIAS.exists():
                for carpeta in sorted(AUDITORIAS.iterdir(), reverse=True):
                    if not carpeta.is_dir() or not RE_CARPETA.match(carpeta.name):
                        continue
                    meta = carpeta / "meta.json"
                    m = None
                    if meta.exists():
                        try:
                            m = json.loads(meta.read_text(encoding="utf-8"))
                        except Exception:
                            m = None
                    # Sin meta (pre ADR-003): se atribuyen al proyecto 1 (declarado).
                    if (m or {}).get("proyecto_n", 1) != n:
                        continue
                    item = {"carpeta": carpeta.name, "sin_meta": m is None}
                    if m:
                        item.update({
                            "auditoria_id": m.get("auditoria_id"),
                            "fecha": m.get("fecha_utc"),
                            "motivo": m.get("motivo"),
                            "estado": m.get("estado_final"),
                            "hallazgos": m.get("hallazgos"),
                        })
                    salida.append(item)
            return self.send_json(salida)

        if parsed.path == "/api/reporte":
            if not self._autorizar("lector"): return
            nombre = q.get("carpeta", [""])[0]
            if not RE_CARPETA.match(nombre):
                return self.send_json({"error": "carpeta inválida"}, 400)
            reporte = AUDITORIAS / nombre / "reporte.md"
            if not reporte.exists():
                return self.send_json({"error": "reporte inexistente"}, 404)
            return self.send_json({"carpeta": nombre,
                                   "contenido": reporte.read_text(encoding="utf-8")})

        if parsed.path == "/api/verificar-paquete":
            if not self._autorizar("lector"): return
            nombre = q.get("carpeta", [""])[0]
            if not RE_CARPETA.match(nombre):
                return self.send_json({"error": "carpeta inválida"}, 400)
            n = proyecto_de_query(q)
            if n is None:
                return self.send_json({"error": "proyecto invalido"}, 400)
            try:
                ruta_bit = rutas.bitacora_de(n)
            except RuntimeError as e:
                return self.send_json({"error": str(e)}, 404)
            carpeta = AUDITORIAS / nombre
            res = mod_verificar.verificar(ruta_bit)
            cadena = {
                "integra": res["integra"],
                "entradas": res["entradas"],
                "verificadas": res["entradas_verificadas"],
                "avisos": res["avisos"],
                "problemas": res["problemas"],
            }
            manifiesto = None
            ruta_man = carpeta / "manifiesto.json"
            if ruta_man.exists():
                m = json.loads(ruta_man.read_text(encoding="utf-8"))
                detalles, ok = [], True
                for nombre_arch, hash_guardado in (m.get("archivos") or {}).items():
                    p = carpeta / nombre_arch
                    if not p.exists():
                        detalles.append(f"{nombre_arch}: falta archivo")
                        ok = False
                    elif sha256_archivo(p) != hash_guardado:
                        detalles.append(f"{nombre_arch}: hash distinto")
                        ok = False
                nota_bit = None
                bit_guardado = m.get("bitacora_sha256")
                bit_actual = sha256_archivo(ruta_bit) if ruta_bit.exists() else None
                if bit_guardado and bit_actual != bit_guardado:
                    nota_bit = ("la bitácora cambió después de esta auditoría "
                                "(esperado si hubo registros posteriores)")
                manifiesto = {"ok": ok, "detalles": detalles, "nota_bitacora": nota_bit}
            import auditoria_meta
            firma_meta = auditoria_meta.verificar_firma_meta(carpeta)
            return self.send_json({"carpeta": nombre, "cadena": cadena,
                                   "manifiesto": manifiesto,
                                   "firma_meta": firma_meta})

        if parsed.path == "/api/buscar":
            if not self._autorizar("lector"): return
            n = proyecto_de_query(q)
            if n is None:
                return self.send_json({"error": "proyecto invalido"}, 400)
            consulta = q.get("q", [""])[0].strip()
            if not consulta:
                return self.send_json({"error": "parámetro 'q' obligatorio"}, 400)
            try:
                carpeta = rutas.carpeta_de(n)
                ruta_bit = rutas.bitacora_de(n)
            except RuntimeError as e:
                return self.send_json({"error": str(e)}, 404)
            ruta_db = indice.ruta_indice(carpeta)
            # Reconstrucción bajo demanda: garantiza resultados frescos aun
            # si hubo registros por CLI (fuera de este servidor) desde la
            # última búsqueda. En un ledger muy grande esto convendría
            # moverlo a un job periódico (ver INSTALACION.md) en vez de
            # hacerlo en cada request; para v0.4 se prioriza correctitud.
            indice.reconstruir(ruta_bit, ruta_db)
            resultados = indice.buscar_texto(ruta_db, consulta)
            return self.send_json({"consulta": consulta, "resultados": resultados})

        if parsed.path == "/api/usuarios":
            if not self._autorizar("admin"): return
            return self.send_json(identidad.listar_usuarios())

        return super().do_GET()

    # ---------------- escritura ----------------
    def do_POST(self):
        parsed = urlparse(self.path)
        datos = self.leer_json()
        if datos is None:
            if getattr(self, "_respondido", False):
                return
            return self.send_json({"error": "JSON inválido"}, 400)

        if parsed.path == "/api/login":
            ip = self.client_address[0]
            usuario = (datos.get("usuario") or "").strip()
            if _login_bloqueado(ip, usuario):
                return self.send_json(
                    {"error": "demasiados intentos fallidos; esperá unos minutos"}, 429)
            password = datos.get("password") or ""
            try:
                sesion = identidad.autenticar(usuario, password)
            except identidad.ErrorIdentidad:
                _registrar_intento_fallido(ip, usuario)
                return self.send_json({"error": "usuario o contraseña inválidos"}, 401)
            return self.send_json(sesion)

        if parsed.path == "/api/logout":
            token = self._token_de_header()
            if token:
                identidad.cerrar_sesion(token)
            return self.send_json({"ok": True})

        if parsed.path == "/api/proyecto/crear":
            info = self._autorizar("admin")
            if not info: return
            titulo = (datos.get("titulo") or "").strip()
            ref = (datos.get("ref") or "").strip().upper()
            nivel = datos.get("nivel", "simple")
            descripcion = (datos.get("descripcion") or "").strip()
            if not titulo:
                return self.send_json({"error": "titulo obligatorio"}, 400)
            if not ref:
                return self.send_json({"error": "ref obligatoria"}, 400)
            if not re.match(r"^[A-Z0-9]{1,16}$", ref):
                return self.send_json({"error": "ref invalida: solo A-Z 0-9, max 16"}, 400)
            if nivel not in MODOS:
                return self.send_json({"error": f"nivel invalido: {nivel}"}, 400)
            r_list = correr_script("proyectos.py", "listar", "--json")
            if r_list.returncode == 0:
                lista = json.loads(r_list.stdout)
                if any(p.get("ref_interna") == ref for p in lista):
                    return self.send_json({"error": f"ref {ref} ya existe"}, 409)
            r = correr_script("proyectos.py", "crear",
                              "--titulo", titulo,
                              "--descripcion", descripcion,
                              "--ref", ref,
                              "--nivel", nivel)
            if r.returncode != 0:
                return self.send_json({"error": r.stderr.strip()}, 500)
            r2 = correr_script("registrar.py",
                               f"Proyecto creado: {titulo}",
                               f"Ref: {ref}, nivel: {nivel}. {descripcion}",
                               "--archivos", "data/proyectos.jsonl",
                               "--modo-firma", "ed25519_actor", "--actor", info["usuario"])
            return self.send_json({"ok": True, "stdout": r.stdout.strip(),
                                   "registro": r2.stdout.strip()})

        if parsed.path == "/api/registrar":
            info = self._autorizar("auditor")
            if not info: return
            titulo = (datos.get("titulo") or "").strip()
            detalle = (datos.get("detalle") or "").strip()
            modo = datos.get("modo_firma", "ed25519_actor")
            if not titulo or not detalle:
                return self.send_json({"error": "titulo y detalle son obligatorios"}, 400)
            if modo not in MODOS_FIRMA:
                return self.send_json({"error": f"modo de firma inválido: {modo}"}, 400)
            proyecto = datos.get("proyecto")
            if proyecto is not None:
                try:
                    proyecto = int(proyecto)
                except (TypeError, ValueError):
                    return self.send_json({"error": "proyecto invalido"}, 400)
            args = [titulo, detalle, "--modo-firma", modo]
            if modo == "ed25519_actor":
                args += ["--actor", info["usuario"]]
            archivos = (datos.get("archivos") or "").strip()
            if archivos:
                args += ["--archivos", archivos]
            commit = (datos.get("commit") or "").strip()
            if commit:
                args += ["--commit", commit]
            r = correr_script("registrar.py", *args, proyecto=proyecto)
            return self.send_json({"ok": r.returncode == 0, "rc": r.returncode,
                                   "stdout": r.stdout.strip(),
                                   "stderr": r.stderr.strip()})

        if parsed.path == "/api/modo":
            info = self._autorizar("admin")
            if not info: return
            nivel = datos.get("nivel")
            if nivel not in MODOS:
                return self.send_json({"error": f"nivel inválido: {nivel}"}, 400)
            n = str(datos.get("n", 1))
            motivo = (datos.get("motivo") or "cambio desde la interfaz").strip()
            r = correr_script("proyectos.py", "nivel", "--n", n,
                              "--nivel", nivel, "--motivo", motivo)
            if r.returncode != 0:
                return self.send_json({"ok": False, "error": r.stdout.strip()}, 400)
            r2 = correr_script("registrar.py",
                               f"Cambio de modo del proyecto #{n} a {nivel}",
                               f"Solicitado desde la interfaz. Motivo: {motivo}",
                               "--modo-firma", "ed25519_actor", "--actor", info["usuario"],
                               "--archivos", "data/proyectos.jsonl",
                               proyecto=int(n))
            return self.send_json({"ok": True, "stdout": r.stdout.strip(),
                                   "registro": r2.stdout.strip()})

        if parsed.path == "/api/documento":
            info = self._autorizar("auditor")
            if not info: return
            cuerpo = datos.get("cuerpo") or ""
            LIMITE_DOC = 5 * 1024 * 1024  # 5 MB
            if len(cuerpo.encode("utf-8")) > LIMITE_DOC:
                return self.send_json(
                    {"error": f"Documento demasiado grande (máximo {LIMITE_DOC} bytes)"}, 413)
            ruta_rel = (datos.get("ruta") or "").strip()
            if ruta_rel:
                ruta = ruta_documento_valida(ruta_rel)
                if ruta is None:
                    return self.send_json({"error": "ruta no autorizada"}, 400)
                creada = not ruta.exists()
            else:
                tipo = datos.get("tipo", "otro")
                titulo = (datos.get("titulo") or "").strip()
                if not titulo:
                    return self.send_json({"error": "titulo obligatorio para crear"}, 400)
                if tipo == "gob":
                    carpeta, pref = DOCS / "00-gobernanza", "GOB"
                    nombre = f"{pref}-STTM-{siguiente_numero(carpeta, pref):03d}-{slug(titulo)}.md"
                elif tipo == "adr":
                    carpeta, pref = DOCS / "02-arquitectura", "ADR"
                    nombre = f"{pref}-STTM-{siguiente_numero(carpeta, pref):03d}-{slug(titulo)}.md"
                elif tipo == "metodo":
                    carpeta = DOCS / "01-metodo"
                    nombre = f"{slug(titulo)}.md"
                else:
                    carpeta = DOCS
                    nombre = f"{slug(titulo)}.md"
                carpeta.mkdir(parents=True, exist_ok=True)
                ruta = carpeta / nombre
                creada = not ruta.exists()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(cuerpo, encoding="utf-8")
            rel = str(ruta.relative_to(RAIZ))
            r2 = correr_script("registrar.py",
                               f"Documento {'creado' if creada else 'actualizado'}: {rel}",
                               "Guardado desde el editor de la interfaz (ADR-002).",
                               "--archivos", rel, "--modo-firma", "ed25519_actor",
                               "--actor", info["usuario"])
            return self.send_json({"ok": True, "creada": creada, "ruta": rel,
                                   "registro": r2.stdout.strip()})

        if parsed.path == "/api/auditar":
            info = self._autorizar("auditor")
            if not info: return
            motivo = (datos.get("motivo") or "Auditoría desde la interfaz").strip()
            tipo = datos.get("tipo", "rapida")
            if tipo not in ("rapida", "estandar", "profunda"):
                return self.send_json({"error": "tipo inválido"}, 400)
            try:
                proyecto = int(datos.get("proyecto", 1))
            except (TypeError, ValueError):
                return self.send_json({"error": "proyecto invalido"}, 400)
            r = correr_script("auditar.py", "--proyecto", str(proyecto),
                              "--motivo", motivo, "--tipo", tipo,
                              "--actor", info["usuario"], "--rol-actor", info["rol"],
                              proyecto=proyecto)
            carpeta = None
            if AUDITORIAS.exists():
                dirs = [d.name for d in sorted(AUDITORIAS.iterdir(), reverse=True)
                        if d.is_dir() and RE_CARPETA.match(d.name)]
                carpeta = dirs[0] if dirs else None
            return self.send_json({"ok": r.returncode == 0, "rc": r.returncode,
                                   "stdout": r.stdout.strip(), "carpeta": carpeta})

        return self.send_json({"error": "endpoint desconocido"}, 404)


def main():
    parser = argparse.ArgumentParser(description="Servidor local del visor STTM.")
    parser.add_argument("--movil", action="store_true",
                        help="escucha en 0.0.0.0 (red local). Por defecto: loopback.")
    args = parser.parse_args()
    host = "0.0.0.0" if args.movil else "127.0.0.1"
    port = int(os.environ.get("STTM_PORT", "8000"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((host, port), STTMHandler) as httpd:
        print(f"✅ Servidor STTM corriendo en http://{host}:{port}")
        if args.movil:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                print(f"📱 Desde tu celular (misma WiFi): http://{s.getsockname()[0]}:{port}")
                s.close()
            except Exception:
                pass
        print("Ctrl+C para detener.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido.")


if __name__ == "__main__":
    main()
