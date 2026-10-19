# Política de divulgación de vulnerabilidades

## Cómo reportar

Si encontrás una vulnerabilidad de seguridad en STTM, reportala de forma
privada antes que pública: un issue público en un repositorio da tiempo
a un atacante de explotarla antes de que exista un arreglo. Mientras el
proyecto no tenga un canal dedicado (ej. una dirección de seguridad
propia), el canal de contacto es el que figure en el perfil del
mantenedor en el repositorio público del proyecto.

## Qué esperar

- Confirmación de recepción.
- Una evaluación honesta de severidad — incluyendo la posibilidad de que
  el reporte se declare "no es una vulnerabilidad" con la explicación
  correspondiente, en vez de un silencio.
- Si se confirma, una entrada en la bitácora documentando el hallazgo y
  la corrección una vez publicado el arreglo (ver ADR-STTM-001: los
  incidentes de seguridad reales son, literalmente, el tipo de evento
  que este método existe para registrar).

## Qué NO hacer

No conviene abrir un issue público con detalles de explotación antes de
que exista un arreglo disponible. Un resumen genérico ("posible problema
de autenticación, reportado en privado") es razonable; los detalles
técnicos de explotación, no.

## Alcance de esta política (honestidad, no relleno)

Esta es una política mínima, no un programa de bug bounty ni una SLA de
respuesta garantizada — sería deshonesto prometer eso sin la
infraestructura para cumplirlo. Antes de cualquier despliegue serio en
una empresa, una auditoría de seguridad externa (ver AYUDA.md §7) es el
paso que realmente importa; esta política solo cubre qué hacer si algo
se encuentra *después* de esa auditoría, o en el uso cotidiano.
