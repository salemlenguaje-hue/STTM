# STTM — Salem Traceability & Trust Method

**v0.4.0** — Un método y una herramienta de trazabilidad auditable: cada
decisión relevante de un proyecto queda en un registro append-only,
encadenado por hash y firmado por la persona real que la generó,
verificable por un tercero sin depender de la palabra de quien lo mantiene.

Creado por Martín José Dalberto, Argentina, 2026.

## Empezar

- **¿Primera vez?** → `INSTALACION.md` (Termux, Linux/macOS o Docker).
- **¿Ya lo instalaste?** → `AYUDA.md` (comandos, roles, referencia de la API).
- **¿Por qué está hecho así?** → `docs/02-arquitectura/ADR-STTM-*.md`.
- **¿Vas a evaluarlo para tu empresa?** → `docs/07-cumplimiento/MAPEO-ESTANDARES.md` y la sección 7 de `AYUDA.md` ("antes de llevar esto a producción").
- **¿Vas a seguir desarrollándolo?** → `CONTINUIDAD.md`.

## Qué es STTM, en una frase

Que "quién hizo qué, cuándo, y por qué" en un proyecto quede en un
registro que cualquiera puede verificar de forma independiente.

## Qué NO es STTM (declarado, no implícito)

- No es un sistema de control de versiones de código (para eso está Git — de hecho se integra con él, ver `hooks/post-commit`).
- No certifica que el contenido de una entrada sea *verdadero* — solo que no cambió después de firmada.
- No es, todavía, una herramienta auditada externamente en seguridad (ver `AYUDA.md` §7 antes de un despliegue serio).
- El testigo de sellado de tiempo externo (RFC 3161) está en BETA, sin validar contra una TSA real (ver ADR-008).

## Principios de diseño (los que importan de verdad)

1. La bitácora es append-only. Nunca se edita ni se borra una línea escrita.
2. Nadie tiene que confiar en este código: hash, firma y canonicalización siguen estándares públicos (RFC 8785, Ed25519, RFC 3161), reimplementables por cualquiera.
3. El índice de búsqueda es siempre derivado y desechable — nunca la fuente de verdad.
4. Lo no probado se declara "pendiente" o "BETA". Nunca "activo" sin evidencia.

## Licencias

- Código: MIT (`LICENSE`).
- Documentación: CC BY 4.0 (`LICENSE-DOCS.md`).

## Estado de pruebas

80/80 tests automatizados en verde (`PYTHONPATH=scripts python3 -m unittest discover tests`), incluyendo integración real del servidor HTTP y del flujo registrar→verificar. Ver `CONTINUIDAD.md` §6 para el detalle de qué se probó y cómo.
