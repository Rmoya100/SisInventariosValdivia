import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg

from ..models import (
    Proyecto, Partida, Trabajador, TareaPlanificacion, DependenciaTarea,
    ModuloTorre, CalendarioProyecto, FeriadoCalendario,
)
from ..forms import TareaPlanificacionForm
from ..perms import user_has_custom_perm


def _check_perm(request, campo):
    if request.user.es_admin:
        return True
    return user_has_custom_perm(request.user, f'inventory.{campo}_tareaplanificacion')


# ── Helpers de calendario ──────────────────────────────────────────────────

def _dias_habil_set(cal):
    dias = {i for i, v in enumerate([
        cal.lunes, cal.martes, cal.miercoles, cal.jueves,
        cal.viernes, cal.sabado, cal.domingo,
    ]) if v}
    feriados = set(cal.feriados.values_list('fecha', flat=True))
    return dias, feriados


def _dias_habiles_entre(fecha_inicio, fecha_fin, cal):
    dias, feriados = _dias_habil_set(cal)
    count, d = 0, fecha_inicio
    while d <= fecha_fin:
        if d.weekday() in dias and d not in feriados:
            count += 1
        d += timedelta(days=1)
    return max(count, 1)


def _fecha_fin_desde_duracion(fecha_inicio, duracion, cal):
    dias, feriados = _dias_habil_set(cal)
    count, d = 0, fecha_inicio
    while True:
        if d.weekday() in dias and d not in feriados:
            count += 1
            if count >= duracion:
                return d
        d += timedelta(days=1)


def _calendario_to_dict(cal):
    return {
        'lunes': cal.lunes, 'martes': cal.martes, 'miercoles': cal.miercoles,
        'jueves': cal.jueves, 'viernes': cal.viernes, 'sabado': cal.sabado,
        'domingo': cal.domingo,
        'hora_inicio': cal.hora_inicio.strftime('%H:%M'),
        'hora_fin': cal.hora_fin.strftime('%H:%M'),
        'feriados': [
            {'id': f.pk, 'fecha': f.fecha.strftime('%Y-%m-%d'), 'nombre': f.nombre}
            for f in cal.feriados.all()
        ],
    }


def _tarea_to_dict(t, cal=None):
    predecesoras_ids = ','.join(
        str(d.tarea_predecesora_id) for d in t.predecesoras.all()
    )
    return {
        'id': str(t.idTarea),
        'name': t.nombre,
        'start': t.fecha_inicio.strftime('%Y-%m-%d'),
        'end': t.fecha_fin.strftime('%Y-%m-%d'),
        'progress': t.progreso,
        'dependencies': predecesoras_ids,
        'custom_class': 'hito-task' if t.es_hito else '',
        'nivel': t.nivel,
        'padre_id': t.padre_id,
        'wbs_orden': t.wbs_orden,
        'estado': t.estado,
        'responsable': str(t.responsable) if t.responsable else '',
        'responsable_id': t.responsable_id,
        'partida_id': t.partida_id,
        'partida_nombre': t.partida.nombre if t.partida else '',
        'modulo_torre_id': t.modulo_torre_id,
        'modulo_torre_nombre': t.modulo_torre.nombre if t.modulo_torre else '',
        'duracion': _dias_habiles_entre(t.fecha_inicio, t.fecha_fin, cal) if cal else t.duracion_dias,
        'es_hito': t.es_hito,
        'descripcion': t.descripcion or '',
    }


class PlanificacionListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'inventory/planificacion_list.html'
    context_object_name = 'proyectos'

    def get_queryset(self):
        qs = Proyecto.all_objects.all().order_by('nombre')
        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado')
        if q:
            qs = qs.filter(nombre__icontains=q)
        if estado == 'activo':
            qs = qs.filter(activo=True)
        elif estado == 'inactivo':
            qs = qs.filter(activo=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        proyectos_data = []
        for p in ctx['proyectos']:
            tareas = p.tareas_planificacion.filter(activo=True)
            count = tareas.count()
            avance = tareas.aggregate(avg=Avg('progreso'))['avg'] or 0
            proyectos_data.append({
                'proyecto': p,
                'count': count,
                'avance': round(avance, 1),
            })
        ctx['proyectos_data'] = proyectos_data
        ctx['q'] = self.request.GET.get('q', '')
        ctx['estado'] = self.request.GET.get('estado', '')
        return ctx


@login_required
def gantt_view(request, proyecto_id):
    if not _check_perm(request, 'view'):
        from django.contrib import messages
        messages.error(request, 'No tiene permiso para ver la planificación.')
        from django.shortcuts import redirect
        return redirect('planificacion_list')

    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    tareas_qs = TareaPlanificacion.objects.filter(
        proyecto=proyecto, activo=True
    ).select_related('partida', 'responsable', 'modulo_torre').prefetch_related('predecesoras')

    cal = getattr(proyecto, 'calendario', None)

    trabajadores = list(Trabajador.objects.filter(activo=True).order_by('nombre').values('codTrabajador', 'nombre', 'apellido'))
    partidas = list(Partida.objects.filter(proyecto=proyecto, activo=True).order_by('nombre').values('idPartida', 'nombre'))
    modulos = list(ModuloTorre.objects.filter(proyecto=proyecto, activo=True).order_by('nombre').values('idModuloTorre', 'nombre'))

    return render(request, 'inventory/planificacion_gantt.html', {
        'proyecto': proyecto,
        'tareas_data': [_tarea_to_dict(t, cal) for t in tareas_qs],
        'trabajadores_data': trabajadores,
        'partidas_data': partidas,
        'modulos_data': modulos,
        'calendario_json': json.dumps(_calendario_to_dict(cal)) if cal else 'null',
        'can_crear': _check_perm(request, 'add'),
        'can_editar': _check_perm(request, 'change'),
        'can_eliminar': _check_perm(request, 'delete'),
    })


@login_required
def api_tareas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    cal = getattr(proyecto, 'calendario', None)
    tareas_qs = TareaPlanificacion.objects.filter(
        proyecto=proyecto, activo=True
    ).select_related('partida', 'responsable', 'modulo_torre').prefetch_related('predecesoras')
    return JsonResponse({'tareas': [_tarea_to_dict(t, cal) for t in tareas_qs]})


@login_required
@require_POST
def api_tarea_crear(request, proyecto_id):
    if not _check_perm(request, 'add'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    data = json.loads(request.body)

    padre_id = data.get('padre_id') or None
    nivel = int(data.get('nivel', 0))

    # Calcular wbs_orden: max de hermanos + 1
    hermanos = TareaPlanificacion.objects.filter(
        proyecto=proyecto, padre_id=padre_id, activo=True
    )
    max_orden = hermanos.order_by('-wbs_orden').values_list('wbs_orden', flat=True).first()
    wbs_orden = (max_orden or 0) + 1

    try:
        fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': f'Fecha inválida: {e}'}, status=400)

    tarea = TareaPlanificacion(
        proyecto=proyecto,
        nombre=data.get('nombre', 'Nueva tarea').upper(),
        descripcion=data.get('descripcion', ''),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        progreso=int(data.get('progreso', 0)),
        es_hito=bool(data.get('es_hito', False)),
        estado=data.get('estado', 'PENDIENTE'),
        nivel=nivel,
        wbs_orden=wbs_orden,
        padre_id=padre_id,
        partida_id=data.get('partida_id') or None,
        responsable_id=data.get('responsable_id') or None,
        modulo_torre_id=data.get('modulo_torre_id') or None,
    )
    tarea.save()

    # Predecesoras
    predecesoras_ids = data.get('predecesoras', [])
    for pred_id in predecesoras_ids:
        try:
            pred = TareaPlanificacion.objects.get(pk=pred_id, proyecto=proyecto)
            DependenciaTarea.objects.get_or_create(tarea_sucesora=tarea, tarea_predecesora=pred)
        except TareaPlanificacion.DoesNotExist:
            pass

    return JsonResponse({'ok': True, 'tarea': _tarea_to_dict(
        TareaPlanificacion.objects.prefetch_related('predecesoras').select_related('partida', 'responsable', 'modulo_torre').get(pk=tarea.pk)
    )})


@login_required
@require_POST
def api_tarea_editar(request, pk):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    tarea = get_object_or_404(TareaPlanificacion, pk=pk, activo=True)
    data = json.loads(request.body)

    try:
        tarea.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        tarea.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': f'Fecha inválida: {e}'}, status=400)

    tarea.nombre = data.get('nombre', tarea.nombre).upper()
    tarea.descripcion = data.get('descripcion', tarea.descripcion)
    tarea.progreso = int(data.get('progreso', tarea.progreso))
    tarea.es_hito = bool(data.get('es_hito', tarea.es_hito))
    tarea.estado = data.get('estado', tarea.estado)
    tarea.partida_id = data.get('partida_id') or None
    tarea.responsable_id = data.get('responsable_id') or None
    tarea.padre_id = data.get('padre_id') or None
    tarea.nivel = int(data.get('nivel', tarea.nivel))
    tarea.modulo_torre_id = data.get('modulo_torre_id') or None

    if tarea.progreso >= 100:
        tarea.estado = 'COMPLETADA'

    tarea.save()

    # Actualizar predecesoras
    if 'predecesoras' in data:
        DependenciaTarea.objects.filter(tarea_sucesora=tarea).delete()
        for pred_id in data['predecesoras']:
            try:
                pred = TareaPlanificacion.objects.get(pk=pred_id, proyecto=tarea.proyecto)
                if pred.pk != tarea.pk:
                    DependenciaTarea.objects.get_or_create(tarea_sucesora=tarea, tarea_predecesora=pred)
            except TareaPlanificacion.DoesNotExist:
                pass

    return JsonResponse({'ok': True, 'tarea': _tarea_to_dict(
        TareaPlanificacion.objects.prefetch_related('predecesoras').select_related('partida', 'responsable', 'modulo_torre').get(pk=tarea.pk)
    )})


@login_required
@require_POST
def api_tarea_eliminar(request, pk):
    if not _check_perm(request, 'delete'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    tarea = get_object_or_404(TareaPlanificacion, pk=pk, activo=True)
    # Soft-delete también subtareas hijas
    TareaPlanificacion.all_objects.filter(padre=tarea).update(activo=False)
    tarea.activo = False
    tarea.save(update_fields=['activo'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_tarea_mover(request, pk):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    tarea = get_object_or_404(TareaPlanificacion, pk=pk, activo=True)
    data = json.loads(request.body)
    try:
        tarea.fecha_inicio = datetime.strptime(data['start'], '%Y-%m-%d').date()
        tarea.fecha_fin = datetime.strptime(data['end'], '%Y-%m-%d').date()
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': f'Fecha inválida: {e}'}, status=400)
    tarea.save(update_fields=['fecha_inicio', 'fecha_fin', 'fecha_modificacion'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_tarea_progreso(request, pk):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    tarea = get_object_or_404(TareaPlanificacion, pk=pk, activo=True)
    data = json.loads(request.body)
    tarea.progreso = min(100, max(0, int(data.get('progress', tarea.progreso))))
    if tarea.progreso >= 100:
        tarea.estado = 'COMPLETADA'
    tarea.save(update_fields=['progreso', 'estado', 'fecha_modificacion'])
    return JsonResponse({'ok': True})


@login_required
def api_partidas_gantt(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    partidas = list(
        Partida.objects.filter(proyecto=proyecto, activo=True)
        .order_by('nombre').values('idPartida', 'nombre')
    )
    return JsonResponse({'partidas': partidas})


@login_required
@require_POST
def api_reordenar(request, proyecto_id):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    data = json.loads(request.body)
    # data = [{'id': ..., 'wbs_orden': ..., 'nivel': ..., 'padre_id': ...}, ...]
    for item in data:
        TareaPlanificacion.objects.filter(
            pk=item['id'], proyecto_id=proyecto_id
        ).update(
            wbs_orden=item.get('wbs_orden', 0),
            nivel=item.get('nivel', 0),
            padre_id=item.get('padre_id') or None,
        )
    return JsonResponse({'ok': True})


# ── APIs de Calendario ─────────────────────────────────────────────────────

@login_required
def api_calendario_get(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    cal, _ = CalendarioProyecto.objects.get_or_create(proyecto=proyecto)
    return JsonResponse(_calendario_to_dict(cal))


@login_required
@require_POST
def api_calendario_guardar(request, proyecto_id):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    data = json.loads(request.body)
    cal, _ = CalendarioProyecto.objects.get_or_create(proyecto=proyecto)

    cal.lunes     = bool(data.get('lunes', cal.lunes))
    cal.martes    = bool(data.get('martes', cal.martes))
    cal.miercoles = bool(data.get('miercoles', cal.miercoles))
    cal.jueves    = bool(data.get('jueves', cal.jueves))
    cal.viernes   = bool(data.get('viernes', cal.viernes))
    cal.sabado    = bool(data.get('sabado', cal.sabado))
    cal.domingo   = bool(data.get('domingo', cal.domingo))

    hora_inicio = data.get('hora_inicio')
    hora_fin = data.get('hora_fin')
    if hora_inicio:
        cal.hora_inicio = datetime.strptime(hora_inicio, '%H:%M').time()
    if hora_fin:
        cal.hora_fin = datetime.strptime(hora_fin, '%H:%M').time()
    cal.save()

    if data.get('recalcular'):
        tareas = TareaPlanificacion.objects.filter(proyecto=proyecto, activo=True)
        for t in tareas:
            if t.es_hito:
                continue
            dur = _dias_habiles_entre(t.fecha_inicio, t.fecha_fin, cal)
            t.fecha_fin = _fecha_fin_desde_duracion(t.fecha_inicio, dur, cal)
            t.save(update_fields=['fecha_fin', 'fecha_modificacion'])

    cal_actualizado = CalendarioProyecto.objects.prefetch_related('feriados').get(pk=cal.pk)
    return JsonResponse({'ok': True, 'calendario': _calendario_to_dict(cal_actualizado)})


@login_required
@require_POST
def api_feriado_agregar(request, proyecto_id):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    cal, _ = CalendarioProyecto.objects.get_or_create(proyecto=proyecto)
    data = json.loads(request.body)
    try:
        fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        return JsonResponse({'error': 'Fecha inválida'}, status=400)
    nombre = data.get('nombre', '').strip() or 'Feriado'
    f, created = FeriadoCalendario.objects.get_or_create(
        calendario=cal, fecha=fecha,
        defaults={'nombre': nombre},
    )
    if not created:
        f.nombre = nombre
        f.save(update_fields=['nombre'])
    return JsonResponse({'ok': True, 'feriado': {'id': f.pk, 'fecha': f.fecha.strftime('%Y-%m-%d'), 'nombre': f.nombre}})


@login_required
@require_POST
def api_feriado_eliminar(request, feriado_id):
    if not _check_perm(request, 'change'):
        return JsonResponse({'error': 'Sin permiso'}, status=403)
    f = get_object_or_404(FeriadoCalendario, pk=feriado_id)
    f.delete()
    return JsonResponse({'ok': True})
