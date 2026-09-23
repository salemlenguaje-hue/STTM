// app.js — Lógica del visor STTM.
// Lee la bitácora y los documentos desde la API del servidor local
// y los muestra en pantalla. Incluye sistema de copiado en 3 capas.

// --- Elementos de la pantalla ---
const btnBitacora = document.getElementById('btn-bitacora');
const btnDocumentos = document.getElementById('btn-documentos');
const vistaBitacora = document.getElementById('vista-bitacora');
const vistaDocumentos = document.getElementById('vista-documentos');
const listaBitacora = document.getElementById('lista-bitacora');
const listaDocumentos = document.getElementById('lista-documentos');
const visorDocumento = document.getElementById('visor-documento');
const contenidoDoc = document.getElementById('contenido-doc');
const cerrarDoc = document.getElementById('cerrar-doc');

// --- Navegación entre pestañas ---
btnBitacora.addEventListener('click', () => {
    btnBitacora.classList.add('active');
    btnDocumentos.classList.remove('active');
    vistaBitacora.classList.remove('oculto');
    vistaDocumentos.classList.add('oculto');
});

btnDocumentos.addEventListener('click', () => {
    btnDocumentos.classList.add('active');
    btnBitacora.classList.remove('active');
    vistaDocumentos.classList.remove('oculto');
    vistaBitacora.classList.add('oculto');
});

// =====================================================
// COPIAR AL PORTAPAPELES — 3 CAPAS
// =====================================================
// Capa 1: API moderna. Solo existe en "contextos seguros"
//         (https o localhost / 127.0.0.1).
// Capa 2: execCommand('copy'). Método viejo, pero funciona
//         en páginas http normales (como tu IP de red).
// Capa 3: Ventana con el texto seleccionado, para copiar
//         con pulsación larga si el navegador bloquea todo.

async function copiar(texto, boton) {
    const original = boton.dataset.original || boton.textContent;
    let metodo = null;

    // Capa 1: API moderna
    if (window.isSecureContext && navigator.clipboard) {
        try {
            await navigator.clipboard.writeText(texto);
            metodo = 'moderno';
        } catch (err) {
            metodo = null;
        }
    }

    // Capa 2: compatibilidad
    if (!metodo) {
        if (copiarConExecCommand(texto)) {
            metodo = 'compatibilidad';
        }
    }

    // Capa 3: copiado manual asistido
    if (!metodo) {
        mostrarCopiadoManual(texto);
        return; // el overlay ya explica qué hacer
    }

    // Feedback visual según el método usado (honestidad UI)
    boton.textContent = (metodo === 'moderno') ? '¡Copiado!' : 'Copiado (compat.)';
    boton.classList.add('copiado');
    setTimeout(() => {
        boton.textContent = original;
        boton.classList.remove('copiado');
    }, 1500);
}

function copiarConExecCommand(texto) {
    // Creamos un textarea casi invisible SOBRE la pantalla.
    // Los navegadores móviles exigen que el elemento esté
    // "a la vista" para poder seleccionarlo y copiarlo.
    const area = document.createElement('textarea');
    area.value = texto;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.left = '0';
    area.style.top = '0';
    area.style.width = '2em';
    area.style.height = '2em';
    area.style.padding = '0';
    area.style.border = 'none';
    area.style.outline = 'none';
    area.style.boxShadow = 'none';
    area.style.background = 'transparent';
    document.body.appendChild(area);

    area.focus();
    area.select();
    area.setSelectionRange(0, 999999);

    let ok = false;
    try {
        ok = document.execCommand('copy');
    } catch (err) {
        ok = false;
    }

    document.body.removeChild(area);
    return ok;
}

function mostrarCopiadoManual(texto) {
    // Última capa: overlay con el texto ya seleccionado.
    const overlay = document.createElement('div');
    overlay.className = 'overlay-copia';
    overlay.innerHTML = `
        <div class="overlay-caja">
            <p class="overlay-titulo">El navegador bloqueó el copiado automático.</p>
            <p class="overlay-ayuda">Mantené presionado el texto y elegí "Copiar".</p>
            <textarea readonly class="overlay-texto"></textarea>
            <button class="btn-copiar overlay-cerrar">Cerrar</button>
        </div>
    `;
    overlay.querySelector('.overlay-texto').value = texto;
    overlay.querySelector('.overlay-cerrar').addEventListener('click', () => {
        document.body.removeChild(overlay);
    });
    document.body.appendChild(overlay);

    // Dejamos el texto seleccionado para facilitar la pulsación larga.
    const ta = overlay.querySelector('.overlay-texto');
    ta.focus();
    ta.select();
}

// =====================================================
// CARGA DE DATOS DESDE LA API
// =====================================================

async function cargarBitacora() {
    try {
        const res = await fetch('/api/bitacora');
        const entradas = await res.json();
        listaBitacora.innerHTML = '';
        if (entradas.length === 0) {
            listaBitacora.innerHTML = '<p style="color: var(--texto-dim);">No hay entradas.</p>';
            return;
        }
        entradas.forEach(e => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta';
            const hashCorto = e.hash ? e.hash.substring(0, 8) : 'N/A';
            const fecha = new Date(e.ts).toLocaleString();
            tarjeta.innerHTML = `
                <h3>#${e.n} ${e.titulo}</h3>
                <div class="meta">${fecha} | Hash: ${hashCorto}...</div>
                <p>${e.detalle}</p>
                <div class="acciones">
                    <button class="btn-copiar" data-original="Copiar Hash">Copiar Hash</button>
                    <button class="btn-copiar" data-original="Copiar Detalle">Copiar Detalle</button>
                    <button class="btn-copiar" data-original="Copiar JSON">Copiar JSON</button>
                </div>
            `;
            const botones = tarjeta.querySelectorAll('.btn-copiar');
            botones[0].addEventListener('click', (ev) => copiar(e.hash, ev.target));
            botones[1].addEventListener('click', (ev) => copiar(e.detalle, ev.target));
            botones[2].addEventListener('click', (ev) => copiar(JSON.stringify(e, null, 2), ev.target));
            listaBitacora.appendChild(tarjeta);
        });
    } catch (err) {
        listaBitacora.innerHTML = '<p style="color: red;">Error al cargar la bitácora.</p>';
    }
}

async function cargarDocumentos() {
    try {
        const res = await fetch('/api/documentos');
        const docs = await res.json();
        listaDocumentos.innerHTML = '';
        docs.forEach(ruta => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta';
            tarjeta.style.cursor = 'pointer';
            const nombre = ruta.split('/').pop();
            tarjeta.innerHTML = `<h3>📄 ${nombre}</h3><div class="meta">${ruta}</div>`;
            tarjeta.addEventListener('click', () => abrirDocumento(ruta));
            listaDocumentos.appendChild(tarjeta);
        });
    } catch (err) {
        listaDocumentos.innerHTML = '<p style="color: red;">Error al cargar documentos.</p>';
    }
}

async function abrirDocumento(ruta) {
    try {
        const res = await fetch(`/api/documento?ruta=${encodeURIComponent(ruta)}`);
        const texto = await res.text();
        contenidoDoc.textContent = texto;
        listaDocumentos.classList.add('oculto');
        visorDocumento.classList.remove('oculto');
    } catch (err) {
        console.error(err);
    }
}

cerrarDoc.addEventListener('click', () => {
    visorDocumento.classList.add('oculto');
    listaDocumentos.classList.remove('oculto');
});

// --- Arranque ---
cargarBitacora();
cargarDocumentos();
