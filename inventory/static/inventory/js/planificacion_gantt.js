/* planificacion_gantt.js — Módulo Gantt tipo MS Project */
'use strict';

let ganttInstance = null;
let allTareas = [];
let collapsedIds = new Set();

const ROW_HEIGHT = 38;

/* ──────────────────────────────────────────────────────────────
   INICIALIZACIÓN
   ────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    const rawTareas   = JSON.parse(document.getElementById('tareas-data').textContent || '[]');
    const trabajadores = JSON.parse(document.getElementById('trabajadores-data').textContent || '[]');
    const partidas    = JSON.parse(document.getElementById('partidas-data').textContent || '[]');
    const modulos     = JSON.parse(document.getElementById('modulos-data').textContent || '[]');

    poblarSelects(trabajadores, partidas, rawTareas);
    poblarSelectModulos(modulos);
    cargarGantt(rawTareas);
});

/* ──────────────────────────────────────────────────────────────
   POBLAR SELECTS DEL MODAL
   ────────────────────────────────────────────────────────────── */
function poblarSelects(trabajadores, partidas, tareas) {
    const selResp = document.getElementById('m-responsable');
    trabajadores.forEach(t => {
        selResp.add(new Option(`${t.nombre} ${t.apellido}`, t.codTrabajador));
    });

    const selPartida = document.getElementById('m-partida');
    partidas.forEach(p => {
        selPartida.add(new Option(p.nombre, p.idPartida));
    });
}

function poblarSelectModulos(modulos) {
    const selModal  = document.getElementById('m-modulo');
    const selFiltro = document.getElementById('filtro-modulo');
    modulos.forEach(m => {
        selModal.add(new Option(m.nombre, m.idModuloTorre));
        selFiltro.add(new Option(m.nombre, m.idModuloTorre));
    });
}

function filtrarPorModulo(moduloId) {
    const tareasFiltradas = moduloId
        ? allTareas.filter(t => String(t.modulo_torre_id) === String(moduloId))
        : allTareas;
    renderizarWBS(tareasFiltradas);
    renderizarFrappe(tareasFiltradas);
}

function fmtFecha(iso) {
    if (!iso) return '';
    const [, m, d] = iso.split('-');
    return `${d}/${m}`;
}

function poblarSelectTareas(tareas, excluirId) {
    const padre = document.getElementById('m-padre');
    const predContainer = document.getElementById('m-predecesoras-container');
    padre.innerHTML = '<option value="">— Tarea raíz —</option>';
    predContainer.innerHTML = '';

    const disponibles = tareas.filter(t => String(t.id) !== String(excluirId));

    if (!disponibles.length) {
        predContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem;">Sin tareas disponibles</span>';
        return;
    }

    disponibles.forEach(t => {
        const indent = '  '.repeat(t.nivel);
        const optP = new Option(`${indent}${t.name}`, t.id);
        padre.add(optP);

        const div = document.createElement('div');
        div.className = 'form-check mb-0';
        div.innerHTML = `<input class="form-check-input pred-check" type="checkbox" value="${t.id}" id="pred-${t.id}">
            <label class="form-check-label" for="pred-${t.id}" style="font-size:0.8rem; cursor:pointer;">${escapeHtml(t.name)}</label>`;
        predContainer.appendChild(div);
    });
}

/* ──────────────────────────────────────────────────────────────
   CARGAR / RECARGAR GANTT
   ────────────────────────────────────────────────────────────── */
function cargarGantt(tareas) {
    allTareas = tareas;
    renderizarWBS(tareas);
    renderizarFrappe(tareas);
}

function recargarDesdeServidor() {
    fetch(URLS.tareas)
        .then(r => r.json())
        .then(data => {
            allTareas = data.tareas;
            poblarSelectTareas(allTareas, null);
            renderizarWBS(allTareas);
            renderizarFrappe(allTareas);
        })
        .catch(err => console.error('Error cargando tareas:', err));
}

/* ──────────────────────────────────────────────────────────────
   TABLA WBS IZQUIERDA
   ────────────────────────────────────────────────────────────── */
function renderizarWBS(tareas) {
    const tbody = document.getElementById('wbs-tbody');
    tbody.innerHTML = '';

    const ordenado = ordenarWBS(tareas);

    ordenado.forEach(t => {
        const tr = document.createElement('tr');
        tr.dataset.id = t.id;
        tr.dataset.padre = t.padre_id || '';
        tr.dataset.nivel = t.nivel;
        tr.className = `wbs-nivel-${t.nivel}`;

        if (collapsedIds.has(String(t.padre_id))) {
            tr.classList.add('row-hidden');
        }

        const tieneHijos = tareas.some(x => String(x.padre_id) === String(t.id));

        const collapseBtn = tieneHijos
            ? `<span class="toggle-collapse" data-id="${t.id}" onclick="toggleCollapse('${t.id}')">
                 <i class="fa-solid ${collapsedIds.has(String(t.id)) ? 'fa-chevron-right' : 'fa-chevron-down'}"></i>
               </span>`
            : '<span style="display:inline-block;width:14px;"></span>';

        const hitoIcon = t.es_hito ? '<i class="fa-solid fa-diamond text-warning me-1" title="Hito"></i>' : '';
        const indent = `<span class="wbs-indent">${collapseBtn}${hitoIcon}${escapeHtml(t.name)}</span>`;

        const modNombre = t.modulo_torre_nombre || '—';
        const modCorto  = modNombre.length > 9 ? modNombre.slice(0, 8) + '…' : modNombre;

        tr.innerHTML = `
            <td class="ps-2 wbs-nombre" title="${escapeHtml(t.name)}">${indent}</td>
            <td title="${escapeHtml(modNombre)}">${escapeHtml(modCorto)}</td>
            <td>${fmtFecha(t.start)}</td>
            <td>${fmtFecha(t.end)}</td>
            <td>${t.duracion}d</td>
            <td>
                <div class="d-flex align-items-center gap-1">
                    <div class="progress" style="width:38px;height:5px;">
                        <div class="progress-bar bg-primary" style="width:${t.progress}%"></div>
                    </div>
                    <span style="font-size:.7rem;">${t.progress}%</span>
                </div>
            </td>
            <td class="text-center">
                ${CAN_EDITAR ? `<button class="btn-editar-tarea" onclick="abrirModalEditar('${t.id}')" title="Editar tarea"><i class="fa-solid fa-pen-to-square" style="font-size:.8rem;"></i></button>` : ''}
            </td>`;
        tbody.appendChild(tr);
    });

    sincronizarAlturaGantt(ordenado.filter(t => !collapsedIds.has(String(t.padre_id))).length);
}

function ordenarWBS(tareas) {
    const mapa = {};
    tareas.forEach(t => { mapa[t.id] = { ...t, hijos: [] }; });
    const raices = [];
    tareas.forEach(t => {
        if (t.padre_id && mapa[t.padre_id]) {
            mapa[t.padre_id].hijos.push(mapa[t.id]);
        } else {
            raices.push(mapa[t.id]);
        }
    });
    raices.sort((a, b) => a.wbs_orden - b.wbs_orden);
    const resultado = [];
    function recorrer(nodos) {
        nodos.sort((a, b) => a.wbs_orden - b.wbs_orden).forEach(n => {
            resultado.push(n);
            if (n.hijos.length) recorrer(n.hijos);
        });
    }
    recorrer(raices);
    return resultado;
}

function sincronizarAlturaGantt(filas) {
    const panel = document.getElementById('gantt-chart-panel');
    const minAltura = Math.max(200, filas * ROW_HEIGHT + 60);
    panel.style.minHeight = minAltura + 'px';
}

function toggleCollapse(id) {
    if (collapsedIds.has(String(id))) {
        collapsedIds.delete(String(id));
    } else {
        collapsedIds.add(String(id));
    }
    renderizarWBS(allTareas);
    const visibles = allTareas.filter(t => !colapsadoOculto(t));
    renderizarFrappe(visibles);
}

function colapsadoOculto(t) {
    if (!t.padre_id) return false;
    if (collapsedIds.has(String(t.padre_id))) return true;
    const padre = allTareas.find(x => String(x.id) === String(t.padre_id));
    return padre ? colapsadoOculto(padre) : false;
}

/* ──────────────────────────────────────────────────────────────
   FRAPPE-GANTT
   ────────────────────────────────────────────────────────────── */
function renderizarFrappe(tareas) {
    const visibles = tareas.filter(t => !colapsadoOculto(t));

    if (!visibles.length) {
        document.getElementById('gantt').innerHTML = '';
        ganttInstance = null;
        return;
    }

    const tasks = visibles.map(t => ({
        id: String(t.id),
        name: t.name,
        start: t.start,
        end: t.end,
        progress: t.progress,
        dependencies: t.dependencies || '',
        custom_class: t.custom_class || '',
    }));

    const vistaActual = ganttInstance ? ganttInstance.view_is('Day') ? 'Day'
        : ganttInstance.view_is('Month') ? 'Month' : 'Week' : 'Week';

    ganttInstance = new Gantt('#gantt', tasks, {
        view_mode: vistaActual,
        date_format: 'YYYY-MM-DD',
        row_height: ROW_HEIGHT,
        bar_height: 20,
        padding: 9,
        language: 'es',
        on_click(task) {
            if (CAN_EDITAR) abrirModalEditar(task.id);
        },
        on_date_change(task, start, end) {
            const fmt = d => d.toISOString().slice(0, 10);
            postJSON(URLS.mover(task.id), { start: fmt(start), end: fmt(end) })
                .then(() => actualizarTareaLocal(task.id, { start: fmt(start), end: fmt(end) }));
        },
        on_progress_change(task, progress) {
            postJSON(URLS.progreso(task.id), { progress: Math.round(progress) })
                .then(() => actualizarTareaLocal(task.id, { progress: Math.round(progress) }));
        },
    });
}

/* ──────────────────────────────────────────────────────────────
   CAMBIO DE VISTA (ZOOM)
   ────────────────────────────────────────────────────────────── */
function cambiarVista(modo) {
    document.querySelectorAll('.btn-zoom').forEach(b => b.classList.remove('active'));
    const ids = { Day: 'zoom-dia', Week: 'zoom-semana', Month: 'zoom-mes' };
    document.getElementById(ids[modo])?.classList.add('active');
    if (ganttInstance) ganttInstance.change_view_mode(modo);
}

/* ──────────────────────────────────────────────────────────────
   MODAL — ABRIR / POBLAR
   ────────────────────────────────────────────────────────────── */
function abrirModalNuevo(esHito) {
    limpiarModal();
    document.getElementById('tareaModalLabel').textContent = esHito ? 'Nuevo Hito' : 'Nueva Tarea';
    document.getElementById('m-hito').checked = esHito;
    document.getElementById('btn-eliminar-tarea').style.display = 'none';

    fetch(URLS.tareas)
        .then(r => r.json())
        .then(data => { allTareas = data.tareas || []; })
        .catch(() => {})
        .finally(() => {
            poblarSelectTareas(allTareas, null);
            new bootstrap.Modal(document.getElementById('tareaModal')).show();
        });
}

function abrirModalEditar(id) {
    fetch(URLS.tareas)
        .then(r => r.json())
        .then(data => {
            allTareas = data.tareas || [];
            const t = allTareas.find(x => String(x.id) === String(id));
            if (!t) return;

            limpiarModal();
            document.getElementById('tareaModalLabel').textContent = 'Editar Tarea';
            document.getElementById('m-id').value = t.id;
            document.getElementById('m-nombre').value = t.name;
            document.getElementById('m-inicio').value = t.start;
            document.getElementById('m-fin').value = t.end;
            document.getElementById('m-progreso').value = t.progress;
            document.getElementById('m-progreso-val').textContent = t.progress;
            document.getElementById('m-estado').value = t.estado;
            document.getElementById('m-hito').checked = t.es_hito;
            document.getElementById('m-descripcion').value = t.descripcion || '';

            poblarSelectTareas(allTareas, id);

            if (t.padre_id) document.getElementById('m-padre').value = t.padre_id;

            const preds = t.dependencies ? t.dependencies.split(',').map(s => s.trim()).filter(Boolean) : [];
            document.querySelectorAll('.pred-check').forEach(cb => {
                cb.checked = preds.includes(String(cb.value));
            });

            if (t.responsable_id) document.getElementById('m-responsable').value = t.responsable_id;
            if (t.partida_id) document.getElementById('m-partida').value = t.partida_id;
            if (t.modulo_torre_id) document.getElementById('m-modulo').value = t.modulo_torre_id;

            if (CAN_ELIMINAR) document.getElementById('btn-eliminar-tarea').style.display = '';

            new bootstrap.Modal(document.getElementById('tareaModal')).show();
        });
}

function limpiarModal() {
    ['m-id','m-nombre','m-inicio','m-fin','m-descripcion'].forEach(id => {
        document.getElementById(id).value = '';
    });
    document.getElementById('m-progreso').value = 0;
    document.getElementById('m-progreso-val').textContent = '0';
    document.getElementById('m-estado').value = 'PENDIENTE';
    document.getElementById('m-hito').checked = false;
    document.getElementById('m-padre').value = '';
    document.getElementById('m-responsable').value = '';
    document.getElementById('m-partida').value = '';
    document.getElementById('m-modulo').value = '';
    document.querySelectorAll('.pred-check').forEach(cb => { cb.checked = false; });
    document.getElementById('btn-eliminar-tarea').style.display = 'none';
}

/* Cuando el usuario elige una partida, auto-rellena el nombre */
function onPartidaChange() {
    const sel = document.getElementById('m-partida');
    const nombre = document.getElementById('m-nombre');
    if (sel.value && !nombre.value.trim()) {
        nombre.value = sel.options[sel.selectedIndex].text;
    }
}

/* ──────────────────────────────────────────────────────────────
   MODAL — GUARDAR
   ────────────────────────────────────────────────────────────── */
function guardarTarea() {
    const id = document.getElementById('m-id').value;
    const nombre = document.getElementById('m-nombre').value.trim();
    const inicio = document.getElementById('m-inicio').value;
    const fin    = document.getElementById('m-fin').value;

    if (!nombre) { alert('El nombre es obligatorio.'); return; }
    if (!inicio || !fin) { alert('Las fechas son obligatorias.'); return; }
    if (inicio > fin) { alert('La fecha de inicio debe ser anterior a la fecha fin.'); return; }

    const predSel = Array.from(document.querySelectorAll('.pred-check:checked')).map(cb => cb.value);
    const padreId = document.getElementById('m-padre').value || null;
    const nivel   = padreId ? (allTareas.find(t => String(t.id) === String(padreId))?.nivel ?? 0) + 1 : 0;

    const payload = {
        nombre:        nombre,
        descripcion:   document.getElementById('m-descripcion').value,
        fecha_inicio:  inicio,
        fecha_fin:     fin,
        progreso:      parseInt(document.getElementById('m-progreso').value) || 0,
        es_hito:       document.getElementById('m-hito').checked,
        estado:        document.getElementById('m-estado').value,
        padre_id:      padreId,
        nivel:         nivel,
        predecesoras:  predSel,
        responsable_id:  document.getElementById('m-responsable').value || null,
        partida_id:      document.getElementById('m-partida').value || null,
        modulo_torre_id: document.getElementById('m-modulo').value || null,
    };

    const url = id ? URLS.editar(id) : URLS.crear;

    postJSON(url, payload)
        .then(data => {
            if (data.ok) {
                bootstrap.Modal.getInstance(document.getElementById('tareaModal')).hide();
                recargarDesdeServidor();
            } else {
                alert('Error: ' + (data.error || 'No se pudo guardar.'));
            }
        })
        .catch(() => alert('Error de conexión.'));
}

/* ──────────────────────────────────────────────────────────────
   ELIMINAR TAREA
   ────────────────────────────────────────────────────────────── */
function eliminarTarea() {
    const id = document.getElementById('m-id').value;
    if (!id) return;
    if (!confirm('¿Eliminar esta tarea? También se eliminarán sus subtareas.')) return;

    postJSON(URLS.eliminar(id), {})
        .then(data => {
            if (data.ok) {
                bootstrap.Modal.getInstance(document.getElementById('tareaModal')).hide();
                recargarDesdeServidor();
            } else {
                alert('Error: ' + (data.error || 'No se pudo eliminar.'));
            }
        })
        .catch(() => alert('Error de conexión.'));
}

/* ──────────────────────────────────────────────────────────────
   ACTUALIZACIÓN LOCAL (sin re-fetch completo)
   ────────────────────────────────────────────────────────────── */
function actualizarTareaLocal(id, cambios) {
    allTareas = allTareas.map(t => {
        if (String(t.id) !== String(id)) return t;
        const updated = { ...t };
        if (cambios.start) { updated.start = cambios.start; }
        if (cambios.end)   { updated.end   = cambios.end;   }
        if (cambios.progress !== undefined) updated.progress = cambios.progress;
        return updated;
    });
    renderizarWBS(allTareas);
}

/* ──────────────────────────────────────────────────────────────
   UTILIDADES
   ────────────────────────────────────────────────────────────── */
function postJSON(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF,
        },
        body: JSON.stringify(data),
    }).then(r => r.json());
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str || ''));
    return d.innerHTML;
}
