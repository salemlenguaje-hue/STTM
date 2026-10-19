# Mapeo de STTM a estándares de cumplimiento

**Alcance de este documento.** STTM no certifica nada por sí solo. Este documento mapea qué evidencia genera cada pieza de STTM contra tres marcos que una empresa evaluadora probablemente ya usa (o le van a pedir usar). Nadie compra "trazabilidad" en abstracto — compra "esto me ayuda a demostrar cumplimiento con el marco que ya tengo que auditar". Este mapeo es orientativo, no es una opinión legal ni un dictamen de un auditor certificado: para una certificación real, un profesional matriculado en el marco correspondiente tiene que confirmarlo caso por caso.

Fuentes: ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023) + Generative AI Profile NIST AI 600-1 (2024), AICPA Trust Services Criteria (SOC 2, TSC 2017 con puntos de foco 2022).

## 1. NIST AI RMF (Govern / Map / Measure / Manage)

El AI RMF no es una checklist de controles técnicos sino un ciclo continuo de cuatro funciones. STTM no implementa el framework — genera la **evidencia auditable** que cada función necesita para poder demostrarse ante un tercero.

| Función NIST AI RMF | Qué pide, en esencia | Qué evidencia aporta STTM |
|---|---|---|
| **Govern** (transversal: políticas, roles, rendición de cuentas) | Políticas y procesos de gestión de riesgo establecidos, transparentes, con responsabilidad clara por persona. | Roles diferenciados (lector/auditor/admin, ADR-004), cada acción atribuida a una persona autenticada con su propia clave — no a "el sistema" en abstracto. Los ADRs mismos son el registro de decisiones de gobernanza, versionados y trazables. |
| **Map** (contexto y casos de uso) | Documentar el contexto, alcance y límites declarados de un sistema. | GOB-STTM-001 y los ADRs documentan explícitamente qué STTM NO hace (sección "What STTM is NOT" del README) — el mapeo de límites es, literalmente, lo que Map pide. |
| **Measure** (evaluar y trackear riesgos con métricas) | Evidencia cuantitativa/cualitativa de qué tan confiable es el sistema, no solo afirmaciones. | `verificar.py` produce un número verificable (entradas íntegras / totales), no una opinión. Los reportes de `auditar.py` (rojo/ámbar/verde) son medición estructurada, repetible por un tercero. |
| **Manage** (asignar recursos, tratar y monitorear riesgos en el tiempo) | Evidencia de que los hallazgos se atienden y de que el sistema mejora con el tiempo. | La bitácora append-only ES el historial de gestión de riesgo: cada incidente, cada corrección, cada decisión de nivel de rigor (`proyectos.py nivel`) queda registrado con fecha y quién lo hizo. |

## 2. ISO/IEC 42001:2023 (Sistema de Gestión de IA — AIMS)

ISO 42001 tiene dos mitades: las cláusulas 4–10 (obligatorias, definen el sistema de gestión en sí) y el Anexo A (38 controles de referencia agrupados en 9 objetivos, A.2 a A.10; una organización elige cuáles aplican y lo justifica en su Declaración de Aplicabilidad — SoA). STTM no reemplaza ninguna de las dos mitades: es una **fuente de evidencia** que alimenta ambas.

| Objetivo del Anexo A (A.2–A.10) | Qué evidencia aporta STTM |
|---|---|
| A.2 Política de IA | Los documentos de gobernanza (`docs/00-gobernanza/`) versionados y firmados son la política, con historial de cambios verificable. |
| A.3 Organización interna, roles | Roles de identidad (ADR-004) mapean directo a "accountability" exigida por A.3. |
| A.4 Recursos | Fuera del alcance técnico de STTM (es un registro de gestión, no un inventario de recursos). |
| A.5 Evaluación de impacto de IA | `auditar.py` y sus reportes son el mecanismo recurrente de evaluación; STTM no define los *criterios* de impacto (eso lo decide la organización), pero registra cuándo se evaluó, con qué resultado y quién lo pidió. |
| A.6 Ciclo de vida del sistema de IA | La bitácora versiona decisiones a lo largo del ciclo de vida (creación de proyecto, cambios de nivel, incidentes) — es el registro de trazabilidad del ciclo de vida en sí. |
| A.7 Datos para IA | Fuera de alcance directo: STTM audita procesos y documentos, no datasets de entrenamiento (salvo que el equipo decida registrar decisiones sobre datos como entradas de bitácora, lo cual es válido pero no automático). |
| A.8 Información a partes interesadas | Documentos públicos (`docs/`) + el propio README declarando límites son exactamente este objetivo: transparencia hacia quien confía en el sistema. |
| A.9 Uso de sistemas de IA | Si el "sistema de IA" auditado es, por ejemplo, un asistente como Alejandra (ecosistema Salem), STTM puede registrar sus decisiones de diseño y cambios — igual que con cualquier otro proyecto. |
| A.10 Relaciones con terceros/clientes | El testigo externo (RFC 3161, ADR-008) y el modelo de firma por-actor dan a un tercero (cliente, proveedor, auditor externo) una forma de verificar sin depender de la palabra de la organización. |

## 3. SOC 2 (AICPA Trust Services Criteria)

SOC 2 tiene cinco categorías: Security (obligatoria, criterios CC1–CC9), y Availability, Processing Integrity, Confidentiality y Privacy (opcionales, según lo que la organización le compromete a sus clientes).

| Categoría / criterio | Qué evidencia aporta STTM |
|---|---|
| **Security — CC6 (Controles de acceso lógico)** | Autenticación + roles jerárquicos (ADR-004) es exactamente lo que CC6 pide demostrar: quién puede acceder a qué, y por qué ese acceso está limitado a lo necesario. |
| **Security — CC7 (Operación de sistemas, monitoreo)** | El índice de búsqueda (ADR-006) y la bitácora misma dan capacidad de auditoría/detección después del hecho — un componente típico de evidencia de CC7. |
| **Security — CC8 (Gestión de cambios)** | Cada cambio de nivel de un proyecto, cada documento editado, queda registrado con quién y cuándo — trazabilidad de cambios es el corazón de CC8. |
| **Processing Integrity** | La cadena de hashes encadenados es, literalmente, una prueba de integridad de procesamiento: que los registros no fueron alterados después de creados. |
| **Confidentiality** | Cifrado en reposo de contenido sensible (`cifrado.py`), permisos 0o600 en toda clave y archivo de credenciales. |
| **Privacy** | Crypto-shredding (ADR-007) es la respuesta directa al criterio de Privacy sobre derecho de las personas a pedir la eliminación de sus datos. |

## 4. Lo que este mapeo NO dice

- No dice que usar STTM implica automáticamente pasar una auditoría SOC 2, ISO 42001 o alinearse con NIST AI RMF: esos marcos evalúan a la *organización completa* (procesos humanos incluidos), no solo una herramienta.
- No dice que los módulos marcados como BETA en esta versión (testigo RFC 3161, ver ADR-008) ya sean evidencia válida — una TSA no validada no es evidencia de sellado de tiempo real ante un auditor.
- No reemplaza una auditoría externa de seguridad del código en sí (pedido ya identificado como bloqueante antes de cualquier venta a una empresa — ver AYUDA.md).
