SALEM

DESCRIPCIÓN DEL SISTEMA STTM
Salem Traceability & Trust Method
Documento técnico y de activo — base para presentación y valuación

Autor del proyecto
Martín José Dalberto
Argentina, 2026

---

1. Control documental

| Dato | Definición |
| --- | --- |
| Identificador | SEA-SALEM-DST-0.1-2026-R1 |
| Estado | Documento técnico e informativo. Describe el sistema y sus características como activo; no asigna valor monetario (corresponde a un profesional matriculado). |
| Alcance | Describe qué es STTM, su arquitectura técnica, su estado actual, sus garantías de integridad y los criterios que lo constituyen como activo de valor. |
| Autor | Martín José Dalberto, Argentina. |
| Antecedentes | Descripción General del Ecosistema (SEA-SALEM-DGE), ADR-002 (visor de evidencia), ADR-003 (sistema de auditoría), documentación de ingeniería del repositorio. |

Declaración de alcance. Este documento describe el sistema STTM con fines
técnicos, de presentación y de valuación de activo. Distingue expresamente
entre capacidades demostradas (verificables por tests y por la bitácora
firmada) y capacidades proyectadas. No constituye una tasación ni una oferta
comercial.

---

2. Propósito

STTM (Salem Traceability & Trust Method) es un método y una herramienta de
trazabilidad criptográfica para la gestión de evidencia de proyectos.

Su objetivo es simple y potente: permitir que cualquier persona registre el
historial de decisiones, documentos y eventos de un proyecto de forma que
nadie pueda modificarlo en secreto después. Si alguien altera un registro
del pasado, el sistema lo detecta.

STTM nació como la herramienta de gobernanza interna del ecosistema Salem y
se desarrolló con el mismo rigor que se le exige: cada cambio queda firmado,
encadenado y es auditable por terceros.

Este documento sirve como:
- presentación técnica del sistema;
- referencia para evaluadores, colaboradores o instituciones;
- base documental para que un asesor contable determine el valor del activo.

---

3. Qué es y para qué sirve

STTM es una cadena de evidencia verificable: una bitácora donde cada entrada
incluye un resumen criptográfico (hash) de la entrada anterior. Esto forma
una cadena: si se modifica una entrada antigua, su hash cambia y rompe la
cadena, y el verificador lo señala.

Resuelve un problema concreto de confianza: cómo demostrar que un proyecto
se desarrolló de cierta manera, con ciertas decisiones, en cierto orden, sin
que nadie pueda borrar o reescribir la historia después.

Aplicaciones:
- gobernanza de proyectos de software e investigación;
- registro auditable de decisiones de arquitectura;
- evidencia para auditorías internas o externas;
- respaldo probatorio para propiedad intelectual;
- transparencia ante instituciones, financiadores o colaboradores.

---

4. Arquitectura técnica

STTM está organizado en cuatro capas, cada una con responsabilidad clara.

4.1 Capa 1 — Núcleo criptográfico

Es el corazón del sistema. Garantiza la integridad de la bitácora.

Componentes:
- registrar.py: crea entradas firmadas y las encadena a la anterior.
- verificar.py: recorre la cadena y detecta cualquier alteración.
- firma.py: implementa los esquemas de firma.

Esquemas de firma soportados (de menor a mayor rigor):
- Hash SHA-256: integridad básica, sin clave.
- HMAC-SHA256: integridad con clave simétrica compartida.
- Ed25519: firma asimétrica; permite verificar sin revelar la clave privada.

La bitácora es append-only: solo se agregan entradas, nunca se borran ni se
editan. Las correcciones se registran como entradas nuevas.

4.2 Capa 2 — Servidor y visor

Interfaz para usar STTM sin operar por línea de comandos.

Componentes:
- servidor.py: servidor HTTP local, sin dependencias externas. Escucha en
  loopback por defecto (solo la propia máquina), con opción de red local.
- Visor web: interfaz responsive con tres niveles visuales de rigor
  (Simple, Continuidad, Salem) y panel de ayuda integrado.

Diseño sin dependencias: usa exclusivamente la biblioteca estándar de Python.
No requiere instalar paquetes de terceros ni servicios comerciales.

4.3 Capa 3 — Motor de auditoría

Genera reportes de estado y paquetes de evidencia verificables.

Componentes:
- auditar.py: verifica la cadena, escanea el proyecto en busca de archivos
  o textos sensibles (claves, secretos) y clasifica hallazgos por severidad
  (rojo, ámbar, informativo).
- Produce tres artefactos por auditoría: reporte legible (reporte.md),
  manifiesto con hashes de los archivos (manifiesto.json) y metadatos
  estructurados (meta.json).

4.4 Capa 4 — Catálogo de proyectos

Permite gestionar varios proyectos con un solo sistema.

Componentes:
- proyectos.py: catálogo append-only de proyectos. El estado actual se
  reconstruye leyendo todas las entradas en orden (nada se borra, las
  correcciones son entradas nuevas).
- Multi-proyecto sin estado global: cada operación indica su proyecto
  explícitamente; ningún proceso guarda estado compartido que pueda
  causar conflictos.

---

5. Decisiones de arquitectura documentadas

STTM documenta sus decisiones de diseño como ADR (Architecture Decision
Records), cada una registrada y trazable:

- ADR-002: diseño del visor de evidencia (interfaz).
- ADR-003: diseño del sistema de auditoría y sus metadatos.
- Extensión multi-proyecto (tarjeta K-001): separación de evidencia por proyecto.

Esta documentación forma parte del activo: no solo existe el código, sino la
razón de cada decisión importante.

---

6. Estado actual (a septiembre de 2026)

- Bitácora del proyecto: 42 entradas firmadas, cadena íntegra (42/42 verificadas).
- Suite de pruebas: 89 tests automatizados en verde.
- Revisiones de código completadas sobre las cuatro capas, con sus
  correcciones documentadas y registradas en bitácora.
- Funciona en entornos restringidos: desarrollado y operado en Termux
  (Android), además de computadoras de escritorio.

Nota de honestidad: STTM es una herramienta funcional y verificable, pero se
encuentra en etapa de desarrollo y validación inicial. No constituye un
producto comercial empaquetado ni cuenta todavía con adopción por terceros.

---

7. Hoja de ruta de uso por nivel

STTM se opera en tres niveles de rigor. Esta hoja de ruta muestra, para cada
uno, qué capacidades están disponibles y cómo se ejercen. Los comandos son
los reales del sistema; el detalle completo de la interfaz está en el
documento de ayuda integrado (docs/05-ui/AYUDA.md).

Nota de paridad: la interfaz web del visor (Capa 2) expone todas las
funcionalidades de los comandos de línea de comandos mostrados en esta hoja
de ruta, a través de sus formularios y selectores. Los comandos de este
documento se presentan porque son la forma canónica y portable de operar
STTM; la UI es una capa de presentación sobre las mismas operaciones.

7.1 Nivel Simple — integridad básica

Propósito: registrar eventos y verificar que no se alteren.

1. Registrar una entrada:

   python scripts/registrar.py "Título del evento" "Detalle de lo ocurrido" \
       --modo-firma hash

2. Verificar la cadena:

   python scripts/verificar.py
   → recorre todas las entradas y reporta si alguna fue alterada.

Resultado: una bitácora encadenada por SHA-256, verificable en cualquier
momento.

7.2 Nivel Continuidad — firma y auditoría

Propósito: además de integridad, firma digital y control periódico.

1. Registrar con firma Ed25519 (asimétrica):

   python scripts/registrar.py "Título" "Detalle" --modo-firma ed25519

2. Crear y gestionar proyectos:

   python scripts/proyectos.py listar
   python scripts/proyectos.py crear --titulo "..." --descripcion "..."

3. Ejecutar una auditoría:

   python scripts/auditar.py --motivo "..." --tipo estandar
   → genera reporte legible, manifiesto con hashes y metadatos.

Resultado: entradas firmadas, catálogo de proyectos y paquetes de auditoría.

7.3 Nivel Salem — máxima trazabilidad con testigos externos

Propósito: demostrar integridad ante terceros combinando capacidades del
código con procedimientos manuales de anclaje a testigos externos.

Lo que aporta el código:
- Todas las capacidades del nivel Continuidad.
- Paquetes de auditoría completos y verificables.
- Reporte con hashes reproducibles.

Lo que aporta el procedimiento manual documentado:
- Anclaje de artefactos de STTM (PDFs de claves públicas, reportes) a
  testigos externos verificables: servicios con timestamp propio
  (por ejemplo, Gmail) y blockchain (Bitcoin vía OpenTimestamps).
- El anclaje externo no está automatizado en el código; es una práctica
  del ecosistema que puede aplicarse a los artefactos que STTM produce.

Resultado: evidencia verificable no solo por el autor, sino por cualquier
tercero con acceso al paquete de auditoría y a los testigos externos
anclados.

Nota de coherencia: cada cambio de nivel queda registrado en la bitácora,
de modo que la propia herramienta demuestra su historia de configuración.
Los testigos externos quedan documentados en entradas específicas de la
bitácora, con sus hashes anclados.

---

8. Criterios de valor como activo

Esta sección describe las características que hacen de STTM un activo con
valor, para que un profesional matriculado pueda evaluarlo. No asigna un
monto.

8.1 Originalidad y autoría
Código original desarrollado desde cero por el autor. La autoría está
declarada en cada archivo y registrada en la bitácora firmada.

8.2 Documentación de ingeniería
El sistema incluye documentación técnica, decisiones de arquitectura (ADR),
pruebas automatizadas y una bitácora cronológica firmada. Este conjunto
documental tiene valor propio, independiente del código.

8.3 Trazabilidad auditable
A diferencia de la mayoría del software, STTM puede demostrar su propia
historia de desarrollo: cada cambio está firmado y encadenado. Esto reduce
el riesgo para un evaluador, porque el estado del activo es verificable.

8.4 Licencia permisiva
Distribuido bajo licencia MIT, que permite uso, modificación y
comercialización, incluyendo derivados. Esto amplía su potencial de
aprovechamiento económico.

8.5 Portabilidad y bajo costo operativo
Funciona sin dependencias externas y en hardware modesto (incluso un
teléfono Android). Esto reduce barreras de adopción y costos de operación.

8.6 Doble condición: herramienta y producto
STTM es simultáneamente la herramienta de gobernanza del ecosistema Salem
y un producto potencialmente ofrecible a terceros. Esa doble condición
amplía sus vías de aprovechamiento.

---

9. Licencia y propiedad

- Código: licencia MIT.
- Autoría: Martín José Dalberto, Argentina, 2026, declarada en cada archivo.
- Metodología y documentación: parte del acervo del ecosistema Salem.

---

10. Condición de revisión

Este documento se revisa ante cambios relevantes en el sistema (nueva versión
estable, cambio de licencia, primera adopción por terceros, tasación formal)
y como mínimo una vez al año. Las cifras de estado (entradas, tests) se
actualizan en cada revisión mayor.

---

Referencias

[1] Descripción General del Ecosistema Salem (SEA-SALEM-DGE-0.1-2026-R1), 2026.
[2] ADR-002 — Visor de evidencia, repositorio STTM, 2026.
[3] ADR-003 — Sistema de auditoría, repositorio STTM, 2026.
[4] Documentación de ingeniería y bitácora firmada del repositorio STTM, 2026.

---

Martín José Dalberto, Argentina, 2026
