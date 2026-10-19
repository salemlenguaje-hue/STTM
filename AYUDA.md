# AYUDA.md — STTM v0.4 (Salem Traceability & Trust Method)

Esta es la guía de referencia completa. Si buscás los pasos de instalación,
andá a `INSTALACION.md`. Si buscás por qué se tomó una decisión de diseño
puntual, los `docs/02-arquitectura/ADR-STTM-*.md` tienen el detalle. Este
documento es el mapa entre unos y otros.

## 1. Qué es STTM, en una frase

Un método y una herramienta para que las decisiones de un proyecto —quién
hizo qué, cuándo, y por qué— queden en un registro que cualquiera puede
verificar de forma independiente, sin tener que confiar en la palabra de
quien lo mantiene.

## 2. Roles y qué puede hacer cada uno

| Rol | Puede leer | Puede registrar/auditar/editar docs | Puede administrar (usuarios, proyectos, nivel) |
|---|---|---|---|
| **lector** | ✅ | ❌ | ❌ |
| **auditor** | ✅ | ✅ | ❌ |
| **admin** | ✅ | ✅ | ✅ |

Los roles son jerárquicos: admin puede todo lo que puede auditor, que
puede todo lo que puede lector. La gestión de usuarios es **solo por
línea de comandos** (ver §3), a propósito: no está expuesta por la API
web, para no ampliar la superficie de ataque sin necesidad real.

## 3. Comandos de línea de comandos más usados

Todos asumen que corriste `export STTM_ROOT=$(pwd)` parado en la carpeta
del proyecto.

```
# Usuarios
python scripts/identidad.py crear <usuario> --rol lector|auditor|admin
python scripts/identidad.py listar
python scripts/identidad.py desactivar <usuario>

# Registro y verificación
python scripts/registrar.py "<título>" "<detalle>" --actor <usuario>
python scripts/verificar.py data/proyectos/1-STTM/BITACORA.jsonl

# Índice de búsqueda
python scripts/indice.py --proyecto 1                    # reconstruir
python scripts/indice.py --proyecto 1 --buscar "palabra"  # buscar

# Auditoría
python scripts/auditar.py --proyecto 1 --tipo rapida --actor <usuario>

# Testigo externo (BETA, requiere red — ver ADR-008)
python scripts/testigo_rfc3161.py probar <archivo>

# Servidor web
python scripts/servidor.py            # local, sin exponer a la red
python scripts/servidor.py --movil    # accesible desde tu red local
```

## 4. La interfaz web

`http://localhost:8000` (o el dominio que hayas configurado con Docker).
Pide login: cualquier usuario creado con `identidad.py crear`. El token
de sesión vive en `sessionStorage` del navegador — se borra solo al
cerrar la pestaña, nunca queda guardado permanentemente en el dispositivo.

## 5. Referencia de la API (para integrarla con otras herramientas)

Todos los endpoints `/api/*` (excepto `/api/login`) exigen el header
`Authorization: Bearer <token>`.

| Método | Ruta | Rol mínimo | Qué hace |
|---|---|---|---|
| POST | `/api/login` | (ninguno) | `{usuario, password}` → `{token, usuario, rol}` |
| POST | `/api/logout` | lector | Invalida el token actual |
| GET | `/api/bitacora` | lector | Lista entradas del proyecto |
| GET | `/api/buscar?q=texto` | lector | Búsqueda de texto libre (índice SQLite) |
| GET | `/api/documentos` | lector | Lista documentos `.md` |
| GET | `/api/documento?ruta=...` | lector | Contenido de un documento |
| GET | `/api/auditorias` | lector | Lista auditorías ejecutadas |
| GET | `/api/reporte?carpeta=...` | lector | Reporte de una auditoría |
| GET | `/api/verificar-paquete?carpeta=...` | lector | Verifica una auditoría contra la cadena |
| GET | `/api/usuarios` | admin | Lista usuarios (sin datos de autenticación) |
| POST | `/api/registrar` | auditor | Nueva entrada en la bitácora |
| POST | `/api/documento` | auditor | Crea/edita un documento |
| POST | `/api/auditar` | auditor | Ejecuta una auditoría |
| POST | `/api/modo` | admin | Cambia el nivel de rigor de un proyecto |
| POST | `/api/proyecto/crear` | admin | Da de alta un proyecto nuevo |

## 6. Lo que STTM garantiza, y lo que no

**Garantiza (verificable, no solo prometido):**
- Que una entrada de la bitácora no fue modificada después de firmada (cadena de hashes + firma Ed25519 por-actor).
- Que cada entrada v3 queda atribuida a una persona real y autenticada, no a un usuario compartido.
- Que borrar un dato personal (crypto-shredding, ADR-007) lo vuelve irrecuperable de verdad, no solo "oculto".

**NO garantiza (declarado, no ocultado):**
- Que el contenido de una entrada sea *verdadero* — solo que no cambió después de escrita. Si alguien registra una mentira y la firma, STTM prueba que esa persona firmó esa mentira, no que sea cierta.
- Seguridad de nivel producción sin una auditoría externa de código — ver §7.
- El testigo RFC 3161 (sellado de tiempo automático) no está validado contra una TSA real todavía (BETA, ver ADR-008).

## 7. Antes de llevar esto a producción en una empresa

Por orden de prioridad real (lo que bloquea la conversación antes que lo demás):

1. **Auditoría de seguridad externa e independiente del código.** Ninguna empresa debería confiar su cadena de custodia a criptografía sin revisión de un tercero — esto no es opcional, es lo primero que va a preguntar cualquier responsable de seguridad.
2. **Continuidad del proyecto.** ¿Qué pasa si la persona que lo mantiene no puede seguir? Roadmap público, política de divulgación de vulnerabilidades.
3. **TLS real** — usá el Docker + Caddy incluido (`docker/`), nunca expongas `servidor.py` sin TLS a internet.
4. **Decidí si necesitás mapeo a un estándar específico** (ISO 42001, NIST AI RMF, SOC 2) — ver `docs/07-cumplimiento/MAPEO-ESTANDARES.md`.

## 8. Preguntas frecuentes

**¿Puedo migrar entradas v1/v2 viejas a v3?** No hay una herramienta de
migración automática en esta versión — las entradas viejas siguen siendo
válidas y verificables tal como están (`verificar.py` reconoce los tres
schemas). Migrar cambiaría su hash, lo cual traicionaría el propio
principio de inmutabilidad. No se migra: se sigue hacia adelante.

**¿Qué pasa si pierdo mi clave privada de usuario?** No hay recuperación:
es la contraparte de que nadie más (ni un admin) pueda firmar en tu
nombre. Un admin puede desactivar tu cuenta vieja y darte una nueva —
tus entradas pasadas siguen siendo verificables con tu clave pública
anterior.

**¿Por qué la gestión de usuarios no está en la interfaz web?** Decisión
deliberada de superficie de ataque mínima en esta versión (ver §2). Si
tu caso de uso realmente lo necesita, es una extensión razonable —
declarada como pendiente, no como olvido.

**¿Esto reemplaza un sistema de control de versiones (Git)?** No. STTM
registra *decisiones y eventos* ("por qué", "quién", "cuándo"); Git
registra *cambios de código* ("qué cambió, línea por línea"). Se
complementan — de hecho `hooks/post-commit` los conecta.
