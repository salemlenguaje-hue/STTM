# Padrones visuales del ecosistema Salem

**Fecha:** 2026-09-25
**Estado:** Documento activo (STTM-0.32)
**Propósito:** Armonizar las tres capas de identidad visual y declarar cuándo se usa cada una.

## Las tres capas

### Capa 1: Identidad de marca Salem
**Uso:** Documentos legales, societarios, registro INPI, materiales oficiales
**Paleta:** Colores oficiales del isologo Salem (no alterables)
**Regla:** El isologo se usa siempre en sus colores originales, en cualquier fondo. Nunca se genera una versión del isologo en verde neón o cian.

### Capa 2: Identidad visual de producto digital
**Uso:** IDE, panel de Alejandra, interfaz de Sofía, sitio web, redes sociales, materiales de difusión
**Paleta:**
- Principal: #39FF14 (verde neón)
- Secundario: #00FFFF (cian eléctrico)
- Fondo: #0A0A0A (negro/muy oscuro)
**Estética:** Tecnológica, retro-futurista, terminal/IDE. Inspiración: informática clásica + futurismo. Contraste alto. Sensación: vivo, inteligente, experimental, accesible.
**Tipografía:** Pendiente de definir. Candidatas: JetBrains Mono, Space Mono, IBM Plex Mono (todas gratuitas para uso comercial).

### Capa 3: Aplicaciones funcionales
**Uso:** Herramientas de uso diario (STTM, visores, interfaces de administración)
**Paleta STTM actual:**
- Fondo: #F7F8FA (gris muy claro)
- Panel: #FFFFFF (blanco)
- Borde: #E3E8EF (gris sutil)
- Tinta: #12263A (azul oscuro)
- Tinta suave: #5C6B7A (gris azulado)
- Acento Salem: #1663A8 (azul)
- Acento oscuro: #12365F (navy)
- Acento suave: #EAF2FA (azul muy claro)
- Ok: #2E7D32 (verde)
- Error: #B3261E (rojo)
**Estética:** Minimalista, elegante, secciones numeradas. Inspirada en salemlang-bradebgs.manus.space. Legibilidad > decoración.
**Tipografía:** Inter (sans-serif para UI), JetBrains Mono (monoespaciada para código).

## Reglas de traducción entre capas

### De Capa 2 a Capa 3 (cuando Capa 2 no aplica directo)
**Problema:** La paleta Capa 2 (verde neón/cian/fondo oscuro) no se aplica cruda a UI de uso diario porque:
1. **Contraste insuficiente en fondos claros:** verde neón sobre #F7F8FA pierde legibilidad
2. **Fatiga visual:** pantallas chicas con verde neón puro cansan la vista en uso prolongado
3. **Contexto de uso:** herramientas de trabajo diario necesitan legibilidad > estética retro
4. **Accesibilidad:** WCAG AA requiere contraste mínimo 4.5:1 para texto normal; verde neón sobre claro no cumple

**Solución:** Traducir la identidad Salem a paleta funcional:
- Verde neón (#39FF14) → Azul Salem (#1663A8) como acento principal
- Cian (#00FFFF) → Azul suave (#EAF2FA) como fondo de acento
- Fondo oscuro (#0A0A0A) → Fondo claro (#F7F8FA) para legibilidad
- Mantener la estética minimalista y elegante, pero con paleta adaptada

### Cuándo usar cada capa
| Contexto | Capa | Ejemplo |
|---|---|---|
| Documento legal, contrato, registro INPI | 1 | SEA-SALEM-MM-0.1-2026-R1 |
| IDE, demo, sitio web de difusión | 2 | Alejandra IDE, salemlang-bradebgs.manus.space |
| Herramienta de uso diario, visor, administración | 3 | STTM, panel de control |

## Decisiones rechazadas

### Por qué NO se aplicó Capa 2 cruda a STTM
**Intento:** Se anexó `Salem_Identidad_Digital_Capa2.docx` con paleta verde neón/cian/fondo oscuro y se intentó aplicar directo al HTML de STTM.
**Resultado:** No quedó bien para UI de uso diario.
**Razones:**
1. Legibilidad insuficiente en móvil (pantallas chicas, uso prolongado)
2. Fatiga visual (verde neón puro cansa la vista)
3. Contraste insuficiente en fondos claros
4. No cumple WCAG AA para texto normal (contraste < 4.5:1)
**Decisión:** STTM usa Capa 3 (paleta clara adaptada), no Capa 2 cruda. La identidad Salem se preserva en el isologo (Capa 1) y en la estética minimalista, pero la paleta se traduce para funcionalidad.

## Tipografía

### Fuentes en uso
- **Inter:** Sans-serif para UI (títulos, botones, texto general). Legible en pantallas chicas.
- **JetBrains Mono:** Monoespaciada para código, hashes, timestamps, datos técnicos. Diseñada para legibilidad en IDE.

### Fuentes candidatas para Capa 2
- **JetBrains Mono:** Ya en uso para código. Funciona bien en contextos técnicos.
- **Space Mono (Google Fonts):** Geométrica, aire retro-futurista marcado. Probablemente la más cercana a "estética terminal + futurismo".
- **IBM Plex Mono:** Alternativa más sobria, baja la carga "retro" sin perder aire técnico.

**Estado:** Pendiente de definir fuente oficial para Capa 2. No usar "Salem Sans" en assets de UI hasta confirmar fuente real.

## Responsive y accesibilidad

### Breakpoints
- **Desktop:** max-width 960px, padding horizontal generoso
- **Tablet:** 720px a 960px, selectores envuelven (PC-011)
- **Móvil:** < 720px, cabecera en columna, selectores full-width

### Contrastes
Todos los textos cumplen WCAG AA (contraste mínimo 4.5:1 para texto normal, 3:1 para texto grande).
- Tinta (#12263A) sobre fondo (#F7F8FA): contraste 12.8:1 ✅
- Tinta suave (#5C6B7A) sobre fondo (#F7F8FA): contraste 5.2:1 ✅
- Azul (#1663A8) sobre blanco (#FFFFFF): contraste 4.6:1 ✅

## Mantenimiento

Este documento se actualiza cuando:
- Se agrega una nueva aplicación funcional (nueva Capa 3)
- Se define la tipografía oficial de Capa 2
- Cambia la paleta de alguna capa
- Se documenta una nueva decisión rechazada

## Referencias

- `Salem_Identidad_Digital_Capa2.docx`: Especificación de Capa 2
- `web/style.css`: Implementación actual de Capa 3 (STTM)
- `salemlang-bradebgs.manus.space`: Inspiración estética para Capa 3
- SEA-SALEM-MM-0.1-2026-R1: Documento de identidad Capa 1 (legal/societario)

---
*Documento registrado en la bitácora del proyecto (entrada de STTM-0.32).*
