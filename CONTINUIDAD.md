# CONTINUIDAD — Proyecto STTM

**Propósito:** Este documento existe para que cualquier persona, colaborador o asistente IA que clone este repositorio sin contexto previo pueda entender qué es STTM, cómo está estructurado, cómo se trabaja y dónde continuar.
**Lectura obligatoria antes de tocar cualquier archivo.**

**Última actualización:** 2026-09-23
**Versión del proyecto:** 0.2.0 (Línea base pública)
**Entorno de desarrollo:** Termux (Android) / Linux / macOS
**Tests automatizados:** 7 (GitHub Actions CI)

---

## ÍNDICE
1. Qué es STTM
2. Los Tres Modos de Gobernanza
3. Estructura del proyecto
4. Cómo está programado
5. Estado actual y Límites declarados
6. Cómo continuar (Flujo de trabajo)
7. Reglas de oro

---

## 1. QUÉ ES STTM

### 1.1. Visión
STTM (Salem Traceability & Trust Method) es una metodología y una herramienta de código abierto diseñada para generar cadenas de evidencia verificables, locales y a prueba de manipulaciones (tamper-evident) para experimentos, auditorías y reportes técnicos.

No es una blockchain. No es un SaaS en la nube. Es un ledger local (append-only) que permite a investigadores independientes y auditores probar *qué* se hizo, *cuándo* y *bajo qué condiciones*, sin depender de servicios externos.

### 1.2. Filosofía
- **Local-First:** Los datos no salen de la máquina a menos que el usuario los exporte.
- **Evidencia antes que publicidad:** Ninguna capacidad se anuncia si no hay un test, un hash o un reporte que la respalde.
- **Criptografía honesta:** Usamos encadenamiento SHA-256 por defecto. No prometemos "inmutabilidad mágica" frente al dueño del hardware; prometemos detección matemática de alteraciones.

---

## 2. LOS TRES MODOS DE GOBERNANZA

STTM se adapta al usuario. No obliga a usar ingeniería pesada en proyectos simples.

1. **Modo Registro Simple:** Solo bitácora JSONL encadenada. Ideal para tracking rápido de experimentos.
2. **Modo Continuidad:** Agrega documentos de estado, índices y handoff. Ideal para proyectos que retoma una IA o un colaborador. (Este proyecto usa este modo).
3. **Modo Salem:** Trazabilidad completa con ADRs, GOBs, matrices de riesgo y preparación formal para auditorías externas.

---

## 3. ESTRUCTURA DEL PROYECTO

```text
~/sttm/
├── CONTINUIDAD.md           <- ESTE DOCUMENTO
├── README.md                <- One-Pager público (Inglés)
├── BITACORA.jsonl           <- Cadena de evidencia (Append-only)
├── LICENSE                  <- MIT (Código)
├── LICENSE-DOCS.md          <- CC-BY 4.0 (Documentación)
│
├── docs/                    <- Documentación y Gobernanza
│   ├── 00-gobernanza/       <- GOBs (Reglas del proyecto)
│   ├── 01-metodo/           <- One-Pagers y definiciones
│   ├── 02-arquitectura/     <- ADRs (Decisiones técnicas)
│   └── 05-ui/               <- (Pendiente) Padrón de estilos
│
├── scripts/                 <- El núcleo de la herramienta
│   ├── registrar.py         <- Agrega entradas a la bitácora
│   ├── verificar.py         <- Valida la cadena de hashes
│   └── auditar.py           <- Motor de inspección (privacidad + integridad)
│
├── tests/                   <- Suite de tests (unittest + tempfile)
├── web/                     <- Visor HTML local (API + Frontend)
└── auditorias/              <- Reportes Markdown generados por auditar.py
```

---

## 4. CÓMO ESTÁ PROGRAMADO

- **Lenguaje:** Python 3.11+ (Biblioteca estándar únicamente. Cero dependencias externas por ahora).
- **Tests:** `unittest` con aislamiento de entornos temporales (`tempfile`). Los tests nunca tocan la bitácora real del usuario.
- **Servidor Web:** `http.server` (stdlib) sirviendo en loopback (`127.0.0.1`) por seguridad, con flag `--movil` para desarrollo en red local.

### Convenciones
- Los scripts leen la variable de entorno `STTM_ROOT` para saber dónde está la raíz del proyecto. Si no está, asumen que están en `scripts/` y suben un nivel.
- Las correcciones a la bitácora **nunca** se hacen editando líneas pasadas. Se agrega una entrada nueva de "Fe de erratas".

---

## 5. ESTADO ACTUAL Y LÍMITES DECLARADOS

### Qué funciona hoy
✅ Cadena JSONL append-only con SHA-256.
✅ Verificador de integridad (detecta alteraciones de contenido y de cadena).
✅ Motor de auditoría (detecta archivos `.pem`, `.key`, tokens `ghp_`).
✅ Visor web local con estética Salem Capa 2 (Verde neón / Cian).
✅ CI/CD con GitHub Actions (Tests corren en cada push).

### Lo que STTM NO es (Límites honestos)
❌ **No es un HSM:** No protege contra un usuario root que quiera borrar el disco.
❌ **No usa Ed25519 (aún):** La firma asimétrica está diseñada pero no integrada. Hoy usa hashes simétricos.
❌ **No es una base de datos:** No reemplaza a SQLite o Postgres para consultas complejas; es un ledger de auditoría.

---

## 6. CÓMO CONTINUAR (FLUJO DE TRABAJO)

Si vas a agregar una feature o arreglar un bug, este es el ciclo PDCA obligatorio:

1. **Planificar:** Crear un ADR en `docs/02-arquitectura/` si es un cambio estructural.
2. **Hacer:** Escribir el código en `scripts/` o `web/`.
3. **Verificar (Tests):** Agregar un test en `tests/test_sttm.py`. Correr `python -m unittest tests.test_sttm -v`.
4. **Verificar (Auditoría):** Correr `python scripts/auditar.py` para asegurar que no filtraste secretos.
5. **Registrar:** 
```bash
   python scripts/registrar.py "Título del hito" "Detalle" --archivos "script.py"
```
6. **Liberar:** `git add . && git commit && git push`.

---

## 7. REGLAS DE ORO

1. **Nada se acepta sin test.** Si no está en `tests/test_sttm.py`, no existe.
2. **Nada se edita hacia atrás.** La bitácora es sagrada. Los errores se corrigen con entradas nuevas.
3. **Cero secretos en el repo.** El `.gitignore` y `auditar.py` protegen esto. Nunca commitees un `.env` o una `.key`.
4. **Honestidad técnica.** Si una feature criptográfica no está integrada, la documentación debe decir "reservada" o "experimental", nunca "activa". (Alineado a Tomo II de Salem, R20-33).

---
*Documento generado y mantenido bajo la metodología STTM.*
