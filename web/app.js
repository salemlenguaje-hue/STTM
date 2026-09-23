/**
 * app.js v3 — Visor STTM (ADR-002).
 * Fixes integrados:
 *  - PC-006: listeners de copiar con scope (solo la lista renderizada).
 *  - PC-009: auditorías sin meta.json se declaran con 📜, no crashean.
 *  - Guard de copiado si un botón no tiene dato asociado.
 *  - Manifiesto null-safe en el visor de paquete.
 *  - Datos de bitácora/auditorías renderizados con createElement +
 *    textContent (innerHTML con datos rompía atributos con comillas).
 */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let proyectoActual = null;

// ---------- utilidades ----------
async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || 'Error de red');
  }
  return res.json();
}

function mostrarMensaje(texto, tipo) {
  const div = document.createElement('div');
  div.className = 'mensaje mensaje-' + (tipo || 'info');
  div.textContent = texto;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3500);
}

function mostrarOverlayCopia(texto) {
  const overlay = document.createElement('div');
  overlay.className = 'overlay-copia';
  const caja = document.createElement('div');
  caja.className = 'overlay-caja';
  const t = document.createElement('h3');
  t.className = 'overlay-titulo';
  t.textContent = 'Copiado manual';
  const p = document.createElement('p');
  p.className = 'overlay-ayuda';
  p.textContent = 'El navegador no permitió copiar automáticamente. Seleccioná y copiá el texto:';
  const ta = document.createElement('textarea');
  ta.className = 'overlay-texto';
  ta.readOnly = true;
  ta.value = texto;
  const btn = document.createElement('button');
  btn.className = 'btn-accion overlay-cerrar';
  btn.textContent = 'Cerrar';
  btn.onclick = () => overlay.remove();
  caja.append(t, p, ta, btn);
  overlay.appendChild(caja);
  document.body.appendChild(overlay);
}

function copiarFallback(texto, btn, avisar) {
  const textarea = document.createElement('textarea');
  textarea.value = texto;
  document.body.appendChild(textarea);
  textarea.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
  document.body.removeChild(textarea);
  if (ok) {
    avisar('Copiado (compat.)');
  } else {
    mostrarOverlayCopia(texto);
  }
}

function copiarAlPortapapeles(texto, btn) {
  if (texto === undefined || texto === null) {
    mostrarMensaje('Nada para copiar: el botón no tiene dato asociado.', 'error');
    return;
  }
  const original = btn.dataset.textoOriginal || btn.textContent;
  btn.dataset.textoOriginal = original;
  const avisar = (etiqueta) => {
    btn.textContent = etiqueta;
    btn.classList.add('copiado');
    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('copiado');
    }, 2000);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(texto)
      .then(() => avisar('¡Copiado!'))
      .catch(() => copiarFallback(texto, btn, avisar));
  } else {
    copiarFallback(texto, btn, avisar);
  }
}

// ---------- proyecto y modo ----------
function aplicarModo(modo) {
  const btnDocs = $('#btn-documentos');
  const btnAud = $('#btn-auditorias');
  btnDocs.classList.toggle('oculto', modo === 'simple');
  btnAud.classList.toggle('oculto', modo !== 'salem');
}

async function cargarProyecto() {
  try {
    const data = await fetchJSON('/api/proyecto');
    proyectoActual = data.proyecto;
    $('#modo-select').value = proyectoActual.nivel_actual;
    aplicarModo(proyectoActual.nivel_actual);
    await cargarBitacora();
    if (proyectoActual.nivel_actual !== 'simple') await cargarDocumentos();
    if (proyectoActual.nivel_actual === 'salem') await cargarAuditorias();
    cargarAyuda();
  } catch (err) {
    mostrarMensaje('Error al cargar proyecto: ' + err.message, 'error');
  }
}

// ---------- bitácora ----------
async function cargarBitacora() {
  try {
    const entradas = await fetchJSON('/api/bitacora');
    const lista = $('#lista-bitacora');
    lista.innerHTML = '';
    entradas.forEach(ent => {
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta';
      const h3 = document.createElement('h3');
      h3.textContent = '#' + ent.n + ' · ' + ent.titulo + ' ';
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = ent.ts;
      h3.appendChild(meta);
      const p = document.createElement('p');
      p.textContent = ent.detalle;
      const acciones = document.createElement('div');
      acciones.className = 'acciones';
      [['Copiar hash', ent.hash],
       ['Copiar detalle', ent.detalle],
       ['Copiar JSON', JSON.stringify(ent)]].forEach(([etiqueta, dato]) => {
        const b = document.createElement('button');
        b.className = 'btn-copiar';
        b.textContent = etiqueta;
        b.dataset.texto = dato;
        b.onclick = () => copiarAlPortapapeles(b.dataset.texto, b);
        acciones.appendChild(b);
      });
      tarjeta.append(h3, p, acciones);
      lista.appendChild(tarjeta);
    });
  } catch (err) {
    mostrarMensaje('Error al cargar bitácora: ' + err.message, 'error');
  }
}

// ---------- documentos ----------
async function cargarDocumentos() {
  try {
    const rutas = await fetchJSON('/api/documentos');
    const lista = $('#lista-documentos');
    lista.innerHTML = '';
    rutas.forEach(ruta => {
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta';
      const h3 = document.createElement('h3');
      h3.textContent = ruta.split('/').pop() + ' ';
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = ruta;
      h3.appendChild(meta);
      const acciones = document.createElement('div');
      acciones.className = 'acciones';
      const b = document.createElement('button');
      b.className = 'btn-copiar';
      b.textContent = 'Ver documento';
      b.onclick = () => verDocumento(ruta);
      acciones.appendChild(b);
      tarjeta.append(h3, acciones);
      lista.appendChild(tarjeta);
    });
  } catch (err) {
    mostrarMensaje('Error al cargar documentos: ' + err.message, 'error');
  }
}

async function verDocumento(ruta) {
  try {
    const res = await fetch('/api/documento?ruta=' + encodeURIComponent(ruta));
    if (!res.ok) throw new Error('ruta no autorizada o inexistente');
    const texto = await res.text();
    $('#lista-documentos').classList.add('oculto');
    $('#visor-documento').classList.remove('oculto');
    $('#contenido-doc').textContent = texto;
  } catch (err) {
    mostrarMensaje('Error al cargar documento: ' + err.message, 'error');
  }
}

// ---------- auditorías ----------
async function cargarAuditorias() {
  try {
    const auds = await fetchJSON('/api/auditorias');
    const lista = $('#lista-auditorias');
    lista.innerHTML = '';
    auds.forEach(aud => {
      const sinMeta = aud.sin_meta || !aud.hallazgos;
      const estado = sinMeta ? '📜'
        : aud.estado === 'apto' ? '✅'
        : aud.estado === 'apto_con_observaciones' ? '⚠️' : '❌';
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta';
      const h3 = document.createElement('h3');
      h3.textContent = estado + ' ' + (aud.auditoria_id || aud.carpeta) + ' ';
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = aud.fecha || '';
      h3.appendChild(meta);
      const pMotivo = document.createElement('p');
      pMotivo.textContent = aud.motivo || '(sin motivo registrado)';
      const pHall = document.createElement('p');
      pHall.className = 'meta';
      pHall.textContent = sinMeta
        ? 'Auditoria previa al schema de metadatos (ADR-003): sin meta.json.'
        : 'Rojos: ' + aud.hallazgos.rojos + ' · Amarillos: ' + aud.hallazgos.amarillos;
      const acciones = document.createElement('div');
      acciones.className = 'acciones';
      const b = document.createElement('button');
      b.className = 'btn-copiar';
      b.textContent = 'Ver reporte';
      b.onclick = () => verAuditoria(aud.carpeta);
      acciones.appendChild(b);
      tarjeta.append(h3, pMotivo, pHall, acciones);
      lista.appendChild(tarjeta);
    });
  } catch (err) {
    mostrarMensaje('Error al cargar auditorías: ' + err.message, 'error');
  }
}

async function verAuditoria(carpeta) {
  try {
    const reporte = await fetchJSON('/api/reporte?carpeta=' + encodeURIComponent(carpeta));
    const verif = await fetchJSON('/api/verificar-paquete?carpeta=' + encodeURIComponent(carpeta));
    $('#lista-auditorias').classList.add('oculto');
    $('#visor-auditoria').classList.remove('oculto');
    const cont = $('#contenido-auditoria');
    cont.innerHTML = '';
    const h3r = document.createElement('h3');
    h3r.textContent = 'Reporte: ' + reporte.carpeta;
    const pre = document.createElement('pre');
    pre.textContent = reporte.contenido;
    const h3v = document.createElement('h3');
    h3v.textContent = 'Verificación de paquete';
    const pCad = document.createElement('p');
    pCad.innerHTML = '<strong>Cadena:</strong> ' +
      (verif.cadena.integra ? '✅ Íntegra' : '❌ Rota') +
      ' (' + verif.cadena.verificadas + '/' + verif.cadena.entradas + ' entradas)';
    const pMan = document.createElement('p');
    const lineaMan = verif.manifiesto === null
      ? '📜 Sin manifiesto (auditoria previa a ADR-003)'
      : verif.manifiesto.ok ? '✅ Válido'
      : '❌ Inválido: ' + (verif.manifiesto.detalles || []).join(', ');
    pMan.innerHTML = '<strong>Manifiesto:</strong> ' + lineaMan;
    cont.append(h3r, pre, h3v, pCad, pMan);
    agregarBotonesExport(cont, reporte.carpeta, reporte.contenido, verif);
    if (verif.manifiesto && verif.manifiesto.nota_bitacora) {
      const pNota = document.createElement('p');
      pNota.className = 'meta';
      pNota.textContent = 'Nota: ' + verif.manifiesto.nota_bitacora;
      cont.appendChild(pNota);
    }
  } catch (err) {
    mostrarMensaje('Error al cargar auditoría: ' + err.message, 'error');
  }
}

// ---------- ayuda ----------
function markdownBasico(md) {
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>');
}

async function cargarAyuda() {
  try {
    const res = await fetch('/api/documento?ruta=' + encodeURIComponent('docs/05-ui/PUNTOS-CRITICOS-UX.md'));
    const texto = await res.text();
    $('#contenido-ayuda').innerHTML = markdownBasico(texto);
  } catch (err) {
    $('#contenido-ayuda').textContent = 'Error al cargar la ayuda.';
  }
}

// ---------- formularios ----------
$('#btn-nueva-entrada').onclick = () => {
  $('#vista-bitacora').classList.add('oculto');
  $('#formulario-entrada').classList.remove('oculto');
};
$('#btn-cancelar-entrada').onclick = () => {
  $('#formulario-entrada').classList.add('oculto');
  $('#vista-bitacora').classList.remove('oculto');
  $('#form-entrada').reset();
};
$('#form-entrada').addEventListener('submit', async (e) => {
  e.preventDefault();
  const datos = {
    titulo: $('#ent-titulo').value,
    detalle: $('#ent-detalle').value,
    archivos: $('#ent-archivos').value,
    commit: $('#ent-commit').value,
    modo_firma: $('#ent-modo-firma').value
  };
  try {
    const res = await fetchJSON('/api/registrar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos)
    });
    if (res.ok) {
      mostrarMensaje('Entrada registrada en la bitácora.', 'ok');
      $('#formulario-entrada').classList.add('oculto');
      $('#vista-bitacora').classList.remove('oculto');
      $('#form-entrada').reset();
      await cargarBitacora();
    } else {
      mostrarMensaje('Error al registrar: ' + (res.stderr || res.error), 'error');
    }
  } catch (err) {
    mostrarMensaje('Error al registrar: ' + err.message, 'error');
  }
});

$('#btn-nuevo-doc').onclick = () => {
  $('#vista-documentos').classList.add('oculto');
  $('#formulario-documento').classList.remove('oculto');
};
$('#btn-cancelar-doc').onclick = () => {
  $('#formulario-documento').classList.add('oculto');
  $('#vista-documentos').classList.remove('oculto');
  $('#form-documento').reset();
};
$('#form-documento').addEventListener('submit', async (e) => {
  e.preventDefault();
  const datos = {
    tipo: $('#doc-tipo').value,
    titulo: $('#doc-titulo').value,
    cuerpo: $('#doc-cuerpo').value
  };
  try {
    const res = await fetchJSON('/api/documento', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos)
    });
    if (res.ok) {
      mostrarMensaje('Documento ' + (res.creada ? 'creado' : 'actualizado') + ': ' + res.ruta, 'ok');
      $('#formulario-documento').classList.add('oculto');
      $('#vista-documentos').classList.remove('oculto');
      $('#form-documento').reset();
      await cargarDocumentos();
    } else {
      mostrarMensaje('Error: ' + res.error, 'error');
    }
  } catch (err) {
    mostrarMensaje('Error al guardar documento: ' + err.message, 'error');
  }
});

$('#btn-nueva-auditoria').onclick = () => {
  $('#vista-auditorias').classList.add('oculto');
  $('#formulario-auditoria').classList.remove('oculto');
};
$('#btn-cancelar-auditoria').onclick = () => {
  $('#formulario-auditoria').classList.add('oculto');
  $('#vista-auditorias').classList.remove('oculto');
  $('#form-auditoria').reset();
};
$('#form-auditoria').addEventListener('submit', async (e) => {
  e.preventDefault();
  const datos = {
    motivo: $('#aud-motivo').value,
    tipo: $('#aud-tipo').value
  };
  try {
    const res = await fetchJSON('/api/auditar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos)
    });
    mostrarMensaje(res.ok
      ? 'Auditoría completada: ' + res.carpeta
      : 'Auditoría con hallazgos: ' + res.carpeta, res.ok ? 'ok' : 'error');
    $('#formulario-auditoria').classList.add('oculto');
    $('#vista-auditorias').classList.remove('oculto');
    $('#form-auditoria').reset();
    await cargarAuditorias();
  } catch (err) {
    mostrarMensaje('Error al ejecutar auditoría: ' + err.message, 'error');
  }
});

// ---------- navegación ----------
$$('.nav-btn').forEach(btn => {
  btn.onclick = () => {
    $$('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    $$('.vista').forEach(v => v.classList.add('oculto'));
    if (btn.id === 'btn-bitacora') $('#vista-bitacora').classList.remove('oculto');
    if (btn.id === 'btn-documentos') $('#vista-documentos').classList.remove('oculto');
    if (btn.id === 'btn-auditorias') $('#vista-auditorias').classList.remove('oculto');
    if (btn.id === 'btn-ayuda') $('#vista-ayuda').classList.remove('oculto');
  };
});

// ---------- selector de modo con confirmación (ADR-002 §3.5) ----------
$('#modo-select').addEventListener('change', async (e) => {
  const nuevoModo = e.target.value;
  if (!confirm('¿Actualizar el proyecto a modo ' + nuevoModo + '? Esto habilita o deshabilita capacidades y queda registrado en la bitácora.')) {
    e.target.value = proyectoActual.nivel_actual;
    return;
  }
  try {
    await fetchJSON('/api/modo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ n: proyectoActual.n, nivel: nuevoModo })
    });
    mostrarMensaje('Modo cambiado a ' + nuevoModo + '.', 'ok');
    await cargarProyecto();
  } catch (err) {
    mostrarMensaje('Error al cambiar modo: ' + err.message, 'error');
    e.target.value = proyectoActual.nivel_actual;
  }
});

// ---------- inicio ----------
cargarProyecto();

// ---------- export y compartido (ADR-002 §3.6, MEJ-001) ----------
function resumenExport(carpeta, contenido, verif) {
  const estado = (contenido.match(/\*\*Estado final:\*\* (.+)/) || [])[1] || 'sin estado';
  const cadena = (verif && verif.cadena)
    ? (verif.cadena.integra ? 'íntegra (' + verif.cadena.verificadas + '/' + verif.cadena.entradas + ')' : 'ROTA')
    : 'sin verificar';
  return 'Reporte STTM ' + carpeta +
    '\nEstado final: ' + estado +
    '\nCadena de evidencia: ' + cadena +
    '\nGenerado por STTM (Salem Traceability & Trust Method).' +
    '\nEl reporte completo viaja como archivo adjunto.';
}

function descargarReporte(carpeta, contenido) {
  // BOM UTF-8: pista para visores de Android/Windows que
  // decodifican .md como Latin-1 sin ella (mojibake observado).
  const blob = new Blob(['\ufeff' + contenido], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'STTM-reporte-' + carpeta + '.md';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
  mostrarMensaje('Reporte descargado como STTM-reporte-' + carpeta + '.md', 'ok');
}

function mostrarMenuExport(carpeta, resumen) {
  const overlay = document.createElement('div');
  overlay.className = 'overlay-copia';
  const caja = document.createElement('div');
  caja.className = 'overlay-caja';
  const t = document.createElement('h3');
  t.className = 'overlay-titulo';
  t.textContent = 'Enviar resumen del reporte';
  const p = document.createElement('p');
  p.className = 'overlay-ayuda';
  p.textContent = 'Por límites de los mensajeros solo viaja el resumen. El reporte completo se descarga con el botón ⬇ y se adjunta a mano.';
  const ta = document.createElement('textarea');
  ta.className = 'overlay-texto';
  ta.readOnly = true;
  ta.value = resumen;
  const fila = document.createElement('div');
  fila.className = 'acciones';
  const bMail = document.createElement('button');
  bMail.className = 'btn-accion';
  bMail.textContent = '✉ Email';
  bMail.onclick = () => {
    window.location.href = 'mailto:?subject=' +
      encodeURIComponent('Reporte STTM ' + carpeta) +
      '&body=' + encodeURIComponent(resumen);
  };
  const bWa = document.createElement('button');
  bWa.className = 'btn-accion';
  bWa.textContent = 'WhatsApp';
  bWa.onclick = () => {
    window.open('https://wa.me/?text=' + encodeURIComponent(resumen), '_blank');
  };
  const bCerrar = document.createElement('button');
  bCerrar.className = 'btn-accion btn-secundario';
  bCerrar.textContent = 'Cerrar';
  bCerrar.onclick = () => overlay.remove();
  fila.append(bMail, bWa, bCerrar);
  caja.append(t, p, ta, fila);
  overlay.appendChild(caja);
  document.body.appendChild(overlay);
}

async function compartirReporte(carpeta, contenido, verif) {
  const resumen = resumenExport(carpeta, contenido, verif);
  if (navigator.share) {
    try {
      const archivo = new File(['\ufeff' + contenido], 'STTM-reporte-' + carpeta + '.md',
        { type: 'text/markdown' });
      if (navigator.canShare && navigator.canShare({ files: [archivo] })) {
        await navigator.share({ files: [archivo], title: 'Reporte STTM ' + carpeta });
        return;
      }
      await navigator.share({ title: 'Reporte STTM ' + carpeta, text: resumen });
      return;
    } catch (err) {
      if (err && err.name === 'AbortError') return; // la persona canceló
      // degrada al nivel 3
    }
  }
  mostrarMenuExport(carpeta, resumen);
}

function agregarBotonesExport(cont, carpeta, contenido, verif) {
  const div = document.createElement('div');
  div.className = 'acciones';
  const bDesc = document.createElement('button');
  bDesc.className = 'btn-accion';
  bDesc.textContent = '⬇ Descargar reporte (.md)';
  bDesc.onclick = () => descargarReporte(carpeta, contenido);
  const bShare = document.createElement('button');
  bShare.className = 'btn-accion btn-secundario';
  bShare.textContent = '📤 Compartir / WhatsApp / email';
  bShare.onclick = () => compartirReporte(carpeta, contenido, verif);
  div.append(bDesc, bShare);
  cont.appendChild(div);
}
