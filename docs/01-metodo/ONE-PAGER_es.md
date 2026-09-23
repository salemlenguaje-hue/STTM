# STTM — Método Salem de Trazabilidad y Confianza

**Cadenas de auditoría locales y a prueba de manipulaciones para evaluaciones de Seguridad en IA.**

> *Nota: Este documento es la versión en español del One-Pager. La versión en inglés (README.md en la raíz) es la referencia para evaluaciones internacionales y grants.*

## 1. El Problema
En la seguridad de la IA (AI Safety) y la evaluación de agentes, las métricas y los resultados experimentales suelen guardarse en bases de datos mutables o archivos de texto planos. Cuando las apuestas son altas (publicar benchmarks de seguridad, auditar modelos, solicitar fondos de investigación), la integridad de la traza de evaluación es tan crítica como el modelo mismo.

## 2. La Solución: STTM
**STTM** es una metodología y herramienta de código abierto diseñada para generar cadenas de evidencia verificables y de solo adición (append-only) para experimentos de IA.

### Principios Fundamentales
- **Local-First (Local primero):** Funciona offline. Los datos no salen de la máquina a menos que se exporten.
- **Ledger de Solo Adición:** Utiliza una bitácora JSONL encadenada criptográficamente. Las entradas pasadas no pueden alterarse en silencio sin romper la cadena de hashes.
- **Criptografía Honesta:** Encadenamiento SHA-256 por defecto. Firma Ed25519 disponible como adaptador opcional, declarando siempre sus límites (sin promesas de "inmutabilidad mágica").
- **Privacidad por Diseño:** Scripts de auditoría integrados para detectar y sanitar claves privadas y rutas locales antes de publicar.

## 3. Tres Modos de Gobernanza
1. **Modo Simple:** Registro básico y encadenamiento de hashes.
2. **Modo Continuidad:** Agrega seguimiento de estado y documentos de handoff (ideal para retomar proyectos con IA).
3. **Modo Salem:** Trazabilidad completa con ADRs, matrices de riesgo y preparación formal para auditorías.

## 4. Lo que STTM NO es (Límites Declarados)
- ❌ No es una herramienta de auditoría certificada por ISO.
- ❌ No provee inmutabilidad absoluta frente al dueño del hardware.
- ❌ No reemplaza a los HSMs (Módulos de Seguridad por Hardware).
- ❌ No ejecuta modelos de IA; solo traza la evidencia de su evaluación.

## 5. Autoría
Creado por **Martín José Dalberto** (Argentina, 2026).  
Parte del Ecosistema Salem.
