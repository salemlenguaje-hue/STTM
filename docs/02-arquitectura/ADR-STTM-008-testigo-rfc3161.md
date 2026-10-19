# ADR-STTM-008 — Testigo externo automático (RFC 3161)

**SALEM**
**STTM — ADR-008: TESTIGO EXTERNO RFC 3161**
Borrador de trabajo interno

Argentina, 2026

## 1. Control documental

| Dato | Definición |
|---|---|
| Identificador | STTM-ADR-008-2026-R1 |
| Estado | **BETA — no validado end-to-end contra una TSA real.** Ver §5. |
| Alcance | Automatiza el sellado de tiempo externo (hasta ahora una ceremonia manual: mail a uno mismo + subida manual a OpenTimestamps). |
| Antecedentes | Testigo K-005 manual (v0.3); análisis crítico externo previo (hallazgo: la ceremonia de testigos era manual, no automatizada). |

## 2. Contexto

Un hash o una firma dicen "este contenido no cambió desde que se firmó", pero no dicen *cuándo* de forma que un tercero neutral lo respalde — para eso STTM usaba una ceremonia manual de testigo (K-005). Automatizarla con una Autoridad de Sellado de Tiempo (TSA) vía el protocolo estándar RFC 3161 es el paso obvio siguiente, pero es también la pieza de esta entrega con más riesgo técnico real: construir mal una estructura ASN.1/DER a mano es un error clásico y difícil de notar sin probarlo contra un servidor real.

## 3. Decisión

Implementar un codificador/decodificador DER mínimo (`testigo_rfc3161.py`) y construir sobre él un cliente RFC 3161: arma un `TimeStampReq` para un digest SHA-256, lo envía por HTTP a una TSA configurable (por defecto, la pública de pruebas `freetsa.org`), y sabe leer el estado (`PKIStatusInfo`) de la respuesta.

## 4. Validación realizada (honestidad técnica — regla de oro #4 del proyecto)

Este módulo se escribió en un entorno **sin salida de red**. Lo que sí se pudo probar, y se probó:

- El codificador DER es autoconsistente: `decode(encode(x)) == x` para enteros, booleanos, OID y secuencias anidadas.
- El OID de SHA-256 (`2.16.840.1.101.3.4.2.1`) codifica byte a byte igual al vector de referencia públicamente conocido (`60 86 48 01 65 03 04 02 01`), verificado con un test que compara contra ese valor literal, no solo contra sí mismo.
- La forma general de un `TimeStampReq` (versión, digest, nonce, certReq) tiene la estructura `SEQUENCE` correcta según RFC 3161 §2.4.1.

Lo que **no** se pudo probar: que una TSA real acepte esta petición y devuelva un token válido. Eso requiere una petición HTTP saliente real.

## 5. Estado declarado

Por la regla de oro de STTM ("lo no implementado se dice 'pendiente', nunca 'activo'"), este módulo se marca **BETA** hasta que alguien lo corra con red real y confirme la respuesta de una TSA. Validación manual (una línea, desde un entorno con red — por ejemplo Termux):

```
python scripts/testigo_rfc3161.py probar <algún-archivo>
```

Si devuelve "✅ Sello de tiempo CONCEDIDO", este ADR debería actualizarse a estado "activo" con la fecha y la TSA usada como evidencia — y ese cambio, en sí mismo, es exactamente el tipo de entrada que vale la pena dejar en la bitácora.

## 6. Límites declarados

- No se implementa verificación de la firma CMS/PKCS#7 completa del token de respuesta (certificados, cadena de confianza): el cliente solo confirma si la TSA concedió o rechazó la petición. Verificar criptográficamente el token entero es un parser mucho más grande, declarado pendiente.
- Sin reintentos ni failover entre TSAs: una sola TSA configurada, sin redundancia. Para un caso de uso serio, valdría la pena sellar contra dos TSAs independientes en paralelo (ninguna es un único punto de confianza) — declarado como mejora futura, no implementado acá.
