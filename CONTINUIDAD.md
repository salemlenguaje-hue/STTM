# CONTINUIDAD.md — STTM v0.4

Este documento existe para que cualquiera (incluida una versión futura de
quien mantiene el proyecto) pueda retomarlo sin tener que releer todo el
historial. Si estás por tocar código acá, leé esto primero.

## 1. Qué es esto, en dos párrafos

STTM (Salem Traceability & Trust Method) es un método y una herramienta
de trazabilidad auditable: cada decisión relevante de un proyecto se
registra en una bitácora append-only, encadenada por hash, firmada por
la persona real que la generó. Un tercero puede verificar la cadena
entera sin tener que confiar en quien la mantiene — solo necesita el
código de `verificar.py` (o una reimplementación propia de RFC 8785 +
Ed25519, si prefiere no confiar ni en ese código).

Esta v0.4 es la iteración "empresarial": agrega identidad multiusuario
real, cifrado para cumplimiento tipo GDPR, búsqueda, contenedorización y
mapeo a estándares (ISO 42001, NIST AI RMF, SOC 2). Ver CHANGELOG.md
para el detalle completo.

## 2. Estructura del repositorio

```
scripts/          Todo el código. Sin paquete pip: se corre como scripts
                   sueltos (python scripts/<archivo>.py), pensado para
                   correr también en Termux sin infraestructura extra.
web/               Interfaz web (HTML/CSS/JS plano, sin build step).
docs/              Documentación versionada: gobernanza, arquitectura
                   (ADRs), cumplimiento, UI.
tests/             80 tests automatizados (unittest de stdlib).
hooks/             Git hook opcional de registro automático.
docker/            Dockerfile + docker-compose + Caddyfile.
data/              Se crea al usar el sistema (usuarios, claves, bitácoras
                   por proyecto). No viene poblado en este paquete.
auditorias/        Reportes de auditoría generados (vacío al empezar).
```

## 3. Reglas de oro (no negociables, heredadas y vigentes)

1. **La bitácora es sagrada.** Nunca se edita ni se borra una línea ya
   escrita. Los errores se corrigen con una entrada nueva que lo diga,
   no reescribiendo la vieja.
2. **Nadie confía en el código de STTM por default.** Todo lo que
   importa (hash, firma, canonicalización) tiene que poder
   reimplementarse desde el estándar (RFC 8785, RFC 8032/Ed25519, RFC
   3161) por un tercero que no confíe en este repositorio.
3. **El índice nunca es la fuente de verdad.** Se puede borrar y
   reconstruir siempre. Si alguna vez el índice y el ledger no
   coinciden, gana el ledger, sin excepción.
4. **Honestidad técnica.** Lo no implementado o no validado se declara
   "pendiente" o "BETA", nunca "activo". Esta v0.4 tiene dos piezas en
   ese estado ahora mismo (ver §5) — no se ocultan.
5. **Sin nombres de entidades externas en documentos versionados
   públicamente**, salvo que sea explícitamente el propósito del
   documento (ej. un contrato o convenio con esa entidad).

## 4. Decisiones de esta versión que alguien podría querer revertir

Documentadas para que, si en el futuro alguien las cuestiona, no haya
que reconstruir el razonamiento desde cero:

- **Gestión de usuarios solo por CLI, no por API.** Se decidió así para
  minimizar superficie de ataque en esta versión. Si el caso de uso
  real exige altas de usuarios self-service, es una extensión
  razonable, no un error a corregir "cuando haya tiempo".
- **PBKDF2 en vez de Argon2id.** Ver ADR-004 §5: fue una limitación del
  entorno de desarrollo (sin red para instalar `argon2-cffi`), no una
  preferencia de diseño. Si el entorno de despliegue lo permite, migrar
  a Argon2id es una mejora directa, no un cambio de arquitectura.
- **Rate-limit de login en memoria del proceso, no en un store
  compartido.** Correcto para un servidor único; con más de una
  instancia detrás de un balanceador, hace falta un store tipo Redis.

## 5. Estado declarado: qué es BETA, qué falta

- **Testigo RFC 3161** (`testigo_rfc3161.py`): el codificador DER está
  probado por autoconsistencia y contra un vector de referencia
  conocido (OID de SHA-256), pero **nunca se validó contra una TSA
  real** — el entorno de desarrollo no tenía salida de red. Ver
  INSTALACION.md §E para el comando de validación manual (una línea).
- **Docker**: Dockerfile y docker-compose escritos siguiendo la sintaxis
  estándar, pero **`docker build`/`docker compose up` nunca se
  corrieron** en este entorno. Mismo motivo.
- **Auditoría de seguridad externa del código**: no realizada. Sigue
  siendo, con diferencia, el paso más importante antes de que cualquier
  empresa confíe su cadena de custodia a esto — ver AYUDA.md §7.

## 6. Cómo se probó lo que sí se probó

80 tests automatizados, corridos de verdad (no solo escritos) durante el
desarrollo de esta versión, incluyendo dos niveles de integración real:

- `test_registro_v3_integracion.py`: levanta `registrar.py` y
  `verificar.py` como subprocesos reales, no mocks.
- `test_servidor_integracion.py`: levanta `servidor.py` como proceso
  HTTP real, en un puerto libre, y le pega con peticiones HTTP reales
  (login, roles, rate-limit, búsqueda, logout) — no se probó "la
  función que arma la respuesta", se probó el servidor andando.

Correr toda la batería: `PYTHONPATH=scripts python3 -m unittest
discover tests`.

## 7. Si vas a agregar un campo nuevo a una entrada

Actualizá `CAMPOS_BASE` (o `CAMPOS_BASE_V3`) en `firma.py`. `registrar.py`
tiene un guard que rechaza escribir una entrada cuyas claves no coincidan
exactamente con las canónicas — es intencional, para que un campo nuevo
agregado sin querer no quede fuera del hash silenciosamente.
