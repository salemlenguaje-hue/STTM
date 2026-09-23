# IDENTIDAD VISUAL — Salem / STTM

**Documento de referencia para UI y materiales de difusión**

**Autor:** Martín José Dalberto  
**Fecha:** 2026-09-23  
**Versión:** 1.0.0  
**Ubicación:** docs/IDENTIDAD-VISUAL-SALEM-STTM.md

---

## ÍNDICE

1. Introducción
2. Dos sistemas de color
3. Capa visual clara (visor STTM actual)
4. Capa 2 oficial (Salem retro-futurista)
5. Logotipos y assets
6. Tipografía
7. Uso y restricciones
8. Referencias

---

## 1. INTRODUCCIÓN

Este documento consolida la identidad visual de Salem y STTM. Salem es el marco conceptual más amplio (lenguaje de programación, arquitectura cognitiva, filosofía). STTM (Salem Traceability & Trust Method) es una herramienta específica dentro del ecosistema Salem.

**Dos sistemas de color coexisten:**

- **Capa visual clara:** Usada actualmente en el visor STTM. Minimalista, profesional, inspirada en el sitio web de Salem.
- **Capa 2 oficial:** Estética retro-futurista, terminal/IDE, verde neón y cian eléctrico. Reservada para IDE, panel de Alejandra, interfaz de Sofía, y materiales de difusión con isologo integrado.

**Regla de oro:** El isologo Salem (la S infinita) **nunca se altera**. Se muestra siempre con sus colores originales registrados ante INPI, en cualquier fondo.

---

## 2. DOS SISTEMAS DE COLOR

### 2.1 Capa visual clara (STTM actual)

**Uso:** Visor STTM, documentación técnica, reportes de auditoría, One-Pager público.

**Filosofía:** Minimalista, profesional, accesible. Inspirada en salemlang-bradebgs.manus.space.

| Rol | Hex | Nombre | Uso |
|---|---|---|---|
| Fondo | `#F7F8FA` | Gris muy claro | Fondo de página |
| Panel | `#FFFFFF` | Blanco | Tarjetas, secciones |
| Borde | `#E3E8EF` | Gris sutil | Bordes de tarjetas |
| Tinta | `#12263A` | Azul oscuro | Texto principal |
| Tinta suave | `#5C6B7A` | Gris azulado | Texto secundario, metadata |
| Acento | `#1663A8` | Azul Salem | Botones, enlaces, acentos |
| Acento oscuro | `#12365F` | Azul navy | Títulos, headers |
| Acento suave | `#EAF2FA` | Azul muy claro | Fondos de botones hover |
| OK | `#2E7D32` | Verde | Estados exitosos |
| Error | `#B3261E` | Rojo | Estados de error |

**Características:**
- Contraste moderado (WCAG AA compliant)
- Espacios amplios, tipografía limpia
- Secciones numeradas (01, 02, 03...)
- Tarjetas blancas con bordes sutiles
- Sombras suaves

**Implementación actual:** `web/style.css` (visor STTM)

---

### 2.2 Capa 2 oficial (Salem retro-futurista)

**Uso:** IDE, panel de Alejandra, interfaz de Sofía, sitio web, redes sociales, materiales de difusión con isologo integrado.

**Filosofía:** Tecnológica, retro-futurista, terminal/IDE. Inspiración: informática clásica + futurismo.

| Rol | Hex | Nombre | Uso |
|---|---|---|---|
| Principal | `#39FF14` | Verde neón | Acentos principales, botones activos |
| Secundario | `#00FFFF` | Cian eléctrico | Acentos secundarios, enlaces |
| Fondo | `#0A0A0A` | Negro profundo | Fondo de página |
| Texto | `#FFFFFF` | Blanco | Texto principal |
| Texto dim | `#888888` | Gris | Texto secundario, metadata |
| Borde | `#333333` | Gris oscuro | Bordes de elementos |

**Características:**
- Contraste alto (pensado para pantallas chicas)
- Sensación: vivo, inteligente, experimental, accesible
- Estética terminal/IDE
- Tipografía monoespaciada

**Implementación futura:** Pendiente de aplicar a IDE, panel de Alejandra, interfaz de Sofía.

---

## 3. CAPA VISUAL CLARA (VISOR STTM ACTUAL)

### 3.1 Paleta detallada

```css
:root {
  --bg: #F7F8FA;          /* fondo claro */
  --panel: #FFFFFF;       /* tarjetas */
  --borde: #E3E8EF;       /* bordes sutiles */
  --tinta: #12263A;       /* texto principal */
  --tinta-suave: #5C6B7A; /* texto secundario */
  --azul: #1663A8;        /* acento Salem */
  --azul-oscuro: #12365F; /* navy */
  --azul-suave: #EAF2FA;  /* fondo de acento */
  --ok: #2E7D32;
  --error: #B3261E;
  --radio: 10px;
  --sombra: 0 1px 2px rgba(18,38,58,.06), 0 4px 12px rgba(18,38,58,.05);
}
```

### 3.2 Componentes

**Cabecera:**
- Fondo blanco, borde inferior sutil
- Isologo Salem (44px altura) + título "STTM" + subtítulo
- Navegación con botones pill (borde redondeado)

**Hero:**
- Ilustración derivada (equipo de auditoría)
- Borde redondeado, sombra suave

**Tarjetas:**
- Fondo blanco, borde `#E3E8EF`
- Padding 1rem, border-radius 10px
- Hover: borde cambia a azul Salem

**Botones:**
- Fondo transparente, borde azul Salem
- Hover: fondo azul suave
- Activo: fondo verde OK

**Secciones numeradas:**
- Título con número en badge (JetBrains Mono, fondo blanco, borde sutil)
- Lista de tarjetas con gap 0.9rem

### 3.3 Implementación

**Archivo:** `web/style.css`  
**HTML:** `web/index.html`  
**Assets:** `web/salem-logo.png`, `web/sttm-equipo.png`

---

## 4. CAPA 2 OFICIAL (SALEM RETRO-FUTURISTA)

### 4.1 Paleta detallada

```css
:root {
  --principal: #39FF14;   /* verde neón */
  --secundario: #00FFFF;  /* cian eléctrico */
  --fondo: #0A0A0A;       /* negro profundo */
  --texto: #FFFFFF;       /* blanco */
  --texto-dim: #888888;   /* gris */
  --borde: #333333;       /* gris oscuro */
}
```

### 4.2 Características

**Estética:**
- Tecnológica, retro-futurista
- Inspiración: informática clásica + futurismo
- Contraste alto para pantallas chicas
- Sensación: vivo, inteligente, experimental, accesible

**Uso previsto:**
- IDE de Salem
- Panel de Alejandra (IA integrada)
- Interfaz de Sofía (arquitectura cognitiva)
- Sitio web oficial
- Redes sociales
- Materiales de difusión con isologo integrado

**No usar en:**
- Documentos legales o societarios (esos siguen el estilo sobrio de la serie SEA-SALEM)
- Documentación técnica interna (usa capa visual clara)

### 4.3 Implementación

**Estado:** Pendiente de aplicar.  
**Referencia:** Documento `Salem_Identidad_Digital_Capa2.docx`

---

## 5. LOGOTIPOS Y ASSETS

### 5.1 Isologo Salem (la S infinita)

**Archivo:** `web/salem-logo.png`  
**Origen:** Registro INPI (marca registrada)  
**Regla de uso:** **Nunca se altera**. Se muestra siempre con sus colores originales, en cualquier fondo.

**Usos correctos:**
- Sobre fondo claro (capa visual clara)
- Sobre fondo oscuro (capa 2)
- Con sus colores originales intactos

**Usos incorrectos:**
- Recolorear el isologo (nunca verde neón, nunca cian)
- Alterar proporciones
- Agregar efectos (sombras, gradientes) que modifiquen los colores

### 5.2 Ilustración derivada (hero STTM)

**Archivo:** `web/sttm-equipo.png`  
**Descripción:** Equipo humano alrededor de una mesa con libros de actas, sello, lupa y documentos. El isologo Salem emerge como holograma desde una laptop, conectado a cada documento por líneas de luz.

**Uso:** Hero del visor STTM (capa visual clara).  
**Regla:** Es un asset derivado nuevo, no una versión recoloreada del isologo. Por eso no viola la regla de marca.

### 5.3 Ubicación de assets

```text
web/
├── salem-logo.png       ← Isologo Salem (marca registrada)
├── sttm-equipo.png      ← Ilustración derivada (hero STTM)
├── index.html           ← Visor HTML
├── style.css            ← Estilos capa visual clara
└── app.js               ← Lógica del visor
```

---

## 6. TIPOGRAFÍA

### 6.1 Capa visual clara (STTM actual)

**Texto principal:** Inter (Google Fonts)
- Weights: 400 (regular), 600 (semibold), 700 (bold)
- Uso: cuerpo de texto, títulos, botones

**Código y hashes:** JetBrains Mono (Google Fonts)
- Weights: 400 (regular), 600 (semibold)
- Uso: hashes, código, metadata técnica

**Implementación:**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

### 6.2 Capa 2 oficial (pendiente de definir)

**Candidatas (todas gratuitas para uso comercial):**

1. **JetBrains Mono** — diseñada específicamente para código, muy legible en pantallas chicas.
2. **Space Mono** (Google Fonts) — geométrica y con un aire retro-futurista más marcado; probablemente la que más se acerca al "estética terminal + futurismo".
3. **IBM Plex Mono** — alternativa más sobria, si se quiere bajar un poco la carga "retro" sin perder el aire técnico.

**Estado:** Pendiente de decisión final.  
**Nota:** "Salem Sans" es hoy un nombre conceptual, todavía sin una fuente real elegida. No usar ese nombre en assets de UI hasta confirmar la fuente real.

---

## 7. USO Y RESTRICCIONES

### 7.1 Cuándo usar cada capa

| Contexto | Capa recomendada | Razón |
|---|---|---|
| Visor STTM | Capa visual clara | Documentación técnica, accesibilidad |
| One-Pager público | Capa visual clara | Profesionalismo, claridad |
| Reportes de auditoría | Capa visual clara | Legibilidad, formalidad |
| IDE de Salem | Capa 2 oficial | Estética terminal/IDE |
| Panel de Alejandra | Capa 2 oficial | Integración con Salem |
| Interfaz de Sofía | Capa 2 oficial | Coherencia con ecosistema |
| Sitio web oficial | Capa 2 oficial | Identidad de marca |
| Redes sociales | Capa 2 oficial | Difusión con isologo |
| Documentos legales | Estilo sobrio SEA-SALEM | Formalidad legal |

### 7.2 Reglas de uso del isologo

1. **Nunca se altera.** Los colores del isologo son los del registro INPI.
2. **Nunca se recolorea.** Ni verde neón, ni cian, ni ningún otro color.
3. **Se muestra sobre cualquier fondo.** Claro u oscuro, con sus colores originales.
4. **No se agregan efectos.** Sin sombras, sin gradientes, sin distorsiones.
5. **Se respeta el espacio.** No se comprime ni se estira.

### 7.3 Reglas de coherencia

1. **No mezclar capas.** Un documento usa una capa o la otra, no ambas.
2. **El isologo es sagrado.** Cualquier asset derivado (como la ilustración del hero) es un asset nuevo, no una modificación del isologo.
3. **Documentar decisiones.** Si se crea un nuevo asset, se registra en bitácora y se actualiza este documento.
4. **Respetar el estado.** Si una capa está "pendiente de implementar", no se usa hasta que esté lista.

---

## 8. REFERENCIAS

### 8.1 Documentos relacionados

- `Salem_Identidad_Digital_Capa2.docx` — Documento original de identidad visual Capa 2
- `CONTINUIDAD.md` — Documento de continuidad del proyecto STTM
- `docs/02-arquitectura/ADR-STTM-002-interfaz-tres-niveles.md` — Decisión arquitectónica de interfaz
- `docs/02-arquitectura/ADR-STTM-003-proyectos-y-auditorias.md` — Catálogo de proyectos y auditorías

### 8.2 Sitios web de referencia

- **salemlang-bradebgs.manus.space** — Sitio web de Salem (inspiración para capa visual clara)
- **Google Fonts** — Fuente de Inter, JetBrains Mono, Space Mono, IBM Plex Mono

### 8.3 Archivos de implementación

- `web/style.css` — Estilos de capa visual clara (visor STTM)
- `web/index.html` — HTML del visor STTM
- `web/salem-logo.png` — Isologo Salem (marca registrada)
- `web/sttm-equipo.png` — Ilustración derivada (hero STTM)

### 8.4 Entradas de bitácora relacionadas

- Entrada #12: "Capa visual clara del visor y assets de identidad en web/"
- Entrada #16: "Incidente 002: patrón de detección sin forma real y clasificación binaria de archivos sensibles"

---

## HISTORIAL DEL DOCUMENTO

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 2026-09-23 | Martín José Dalberto (asistido por Claude) | Versión inicial. Consolida identidad visual de Salem/STTM. Documenta dos sistemas de color (capa visual clara y Capa 2 oficial). Incluye logotipos, tipografía, uso y restricciones. |

---

*Documento generado bajo la metodología STTM.*  
*Última actualización: 2026-09-23*
