from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..decorators import permission_required
from ..perms import user_has_custom_perm
from django.db.models import Q
from ..models import Herramienta, MantenimientoHerramienta, Maquinaria, MantenimientoMaquinaria, TransferenciaActivo
from ..forms import (
    HerramientaForm, MantenimientoHerramientaForm, RecepcionHerramientaForm,
    MaquinariaForm, ActualizarLecturaForm, MantenimientoMaquinariaForm, RecepcionMaquinariaForm,
    TransferenciaActivoForm
)

def _can(user, perm: str) -> bool:
    return user.es_admin or user.is_superuser or user.is_staff or user_has_custom_perm(user, perm)

@login_required
@permission_required('inventory.view_herramienta', raise_exception=True)
def herramientas_view(request):
    herramientas = Herramienta.objects.select_related('bodega_actual').filter(activo=True)
    q = request.GET.get('q')
    if q:
        herramientas = herramientas.filter(Q(nomHerramienta__icontains=q) | Q(codigo__icontains=q) | Q(marca__icontains=q))
    
    if request.method == 'POST' and _can(request.user, 'inventory.add_herramienta'):
        form = HerramientaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Herramienta guardada con éxito.')
            return redirect('herramientas')
        else:
            messages.error(request, 'Error al guardar la herramienta. Revisa los datos.')
    else:
        form = HerramientaForm()
        
    return render(request, 'inventory/herramientas_list.html', {
        'herramientas': herramientas,
        'form': form
    })

@login_required
@permission_required('inventory.change_herramienta', raise_exception=True)
def herramienta_editar(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    if request.method == 'POST':
        form = HerramientaForm(request.POST, instance=herramienta)
        if form.is_valid():
            form.save()
            messages.success(request, f'Herramienta "{herramienta.nomHerramienta}" actualizada.')
            return redirect('herramientas')
    else:
        form = HerramientaForm(instance=herramienta)
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Editar Herramienta: {herramienta.nomHerramienta}',
        'url_volver': reverse_lazy('herramientas')
    })

@login_required
@permission_required('inventory.delete_herramienta', raise_exception=True)
def herramienta_eliminar(request, pk):
    herramienta = get_object_or_404(Herramienta, pk=pk)
    if request.method == 'POST':
        nombre = herramienta.nomHerramienta
        herramienta.activo = False
        herramienta.save()
        messages.success(request, f'Herramienta "{nombre}" desactivada.')
        return redirect('herramientas')
    return render(request, 'inventory/confirmar_eliminar.html', {
        'objeto': herramienta,
        'titulo': 'Desactivar Herramienta',
        'url_volver': reverse_lazy('herramientas')
    })

@login_required
@permission_required('inventory.view_mantenimientoherramienta', raise_exception=True)
def mantenimiento_herramienta_view(request):
    mantenimientos = MantenimientoHerramienta.objects.select_related('herramienta', 'proveedor').order_by('-fecha_envio')
    if request.method == 'POST' and _can(request.user, 'inventory.add_mantenimientoherramienta'):
        form = MantenimientoHerramientaForm(request.POST)
        if form.is_valid():
            mant = form.save()
            mant.herramienta.en_reparacion = True
            mant.herramienta.save(update_fields=['en_reparacion'])
            messages.success(request, f'Herramienta enviada a reparación con proveedor {mant.proveedor}.')
            return redirect('mantenimiento_herramientas')
        else:
            messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = MantenimientoHerramientaForm()
    return render(request, 'inventory/mantenimiento_herramientas.html', {
        'mantenimientos': mantenimientos, 'form': form
    })

@login_required
@permission_required('inventory.change_mantenimientoherramienta', raise_exception=True)
def recibir_herramienta_mantenimiento(request, pk):
    mant = get_object_or_404(MantenimientoHerramienta, pk=pk)
    if mant.fecha_recepcion:
        messages.warning(request, 'Esta herramienta ya fue recepcionada.')
        return redirect('mantenimiento_herramientas')
    if request.method == 'POST':
        form = RecepcionHerramientaForm(request.POST, instance=mant)
        if form.is_valid():
            form.save()
            mant.herramienta.en_reparacion = False
            mant.herramienta.save(update_fields=['en_reparacion'])
            messages.success(request, f'Herramienta "{mant.herramienta.nomHerramienta}" recepcionada correctamente.')
            return redirect('mantenimiento_herramientas')
    else:
        form = RecepcionHerramientaForm(instance=mant)
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Recepcionar: {mant.herramienta.nomHerramienta}',
        'url_volver': reverse_lazy('mantenimiento_herramientas')
    })


@login_required
@permission_required('inventory.view_maquinaria', raise_exception=True)
def maquinaria_view(request):
    maquinarias = Maquinaria.objects.select_related('bodega_actual').filter(activo=True)
    q = request.GET.get('q')
    if q:
        maquinarias = maquinarias.filter(Q(marca__icontains=q) | Q(patente_o_codigo__icontains=q) | Q(modelo__icontains=q))
    
    if request.method == 'POST' and _can(request.user, 'inventory.add_maquinaria'):
        form = MaquinariaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maquinaria guardada con éxito.')
            return redirect('maquinarias')
        else:
            messages.error(request, 'Error al guardar la maquinaria. Revisa los datos.')
    else:
        form = MaquinariaForm()
        
    maquinarias_alerta = [m for m in maquinarias if m.alerta_mantenimiento()]
    return render(request, 'inventory/maquinarias_list.html', {
        'maquinarias': maquinarias,
        'maquinarias_alerta': maquinarias_alerta,
        'form': form
    })

@login_required
@permission_required('inventory.change_maquinaria', raise_exception=True)
def maquinaria_editar(request, pk):
    maquinaria = get_object_or_404(Maquinaria, pk=pk)
    if request.method == 'POST':
        form = MaquinariaForm(request.POST, instance=maquinaria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Maquinaria "{maquinaria.patente_o_codigo}" actualizada.')
            return redirect('maquinarias')
    else:
        form = MaquinariaForm(instance=maquinaria)
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Editar Maquinaria: {maquinaria.patente_o_codigo}',
        'url_volver': reverse_lazy('maquinarias')
    })

@login_required
@permission_required('inventory.delete_maquinaria', raise_exception=True)
def maquinaria_eliminar(request, pk):
    maquinaria = get_object_or_404(Maquinaria, pk=pk)
    if request.method == 'POST':
        codigo = maquinaria.patente_o_codigo
        maquinaria.activo = False
        maquinaria.save()
        messages.success(request, f'Maquinaria "{codigo}" desactivada.')
        return redirect('maquinarias')
    return render(request, 'inventory/confirmar_eliminar.html', {
        'objeto': maquinaria,
        'titulo': 'Desactivar Maquinaria',
        'url_volver': reverse_lazy('maquinarias')
    })

@login_required
@permission_required('inventory.change_maquinaria', raise_exception=True)
def actualizar_lectura_maquinaria(request, pk):
    maquinaria = get_object_or_404(Maquinaria, pk=pk)
    unidad = 'horas' if maquinaria.tipo_control == 'HORAS' else 'km'
    if request.method == 'POST':
        form = ActualizarLecturaForm(request.POST, instance=maquinaria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lectura de {maquinaria.patente_o_codigo} actualizada a {maquinaria.valor_actual} {unidad}.')
            return redirect('maquinarias')
    else:
        form = ActualizarLecturaForm(instance=maquinaria)
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Actualizar Lectura ({unidad}): {maquinaria.patente_o_codigo}',
        'url_volver': reverse_lazy('maquinarias')
    })

@login_required
@permission_required('inventory.view_mantenimientomaquinaria', raise_exception=True)
def mantenimiento_maquinaria_view(request):
    mantenimientos = MantenimientoMaquinaria.objects.select_related('maquinaria', 'proveedor').order_by('-fecha_envio')
    if request.method == 'POST' and _can(request.user, 'inventory.add_mantenimientomaquinaria'):
        form = MantenimientoMaquinariaForm(request.POST)
        if form.is_valid():
            mant = form.save(commit=False)
            mant.save()
            maq = mant.maquinaria
            maq.ultimo_mantenimiento = mant.valor_mantenimiento
            maq.en_reparacion = True
            maq.save(update_fields=['ultimo_mantenimiento', 'en_reparacion'])
            messages.success(request, f'Maquinaria enviada a mantenimiento con {mant.proveedor}.')
            return redirect('mantenimiento_maquinarias')
        else:
            messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = MantenimientoMaquinariaForm()
    return render(request, 'inventory/mantenimiento_maquinarias.html', {
        'mantenimientos': mantenimientos, 'form': form
    })

@login_required
@permission_required('inventory.change_mantenimientomaquinaria', raise_exception=True)
def recibir_maquinaria_mantenimiento(request, pk):
    mant = get_object_or_404(MantenimientoMaquinaria, pk=pk)
    if mant.fecha_recepcion:
        messages.warning(request, 'Esta maquinaria ya fue recepcionada.')
        return redirect('mantenimiento_maquinarias')
    if request.method == 'POST':
        form = RecepcionMaquinariaForm(request.POST, instance=mant)
        if form.is_valid():
            form.save()
            mant.maquinaria.en_reparacion = False
            mant.maquinaria.save(update_fields=['en_reparacion'])
            messages.success(request, f'Maquinaria "{mant.maquinaria.patente_o_codigo}" recepcionada.')
            return redirect('mantenimiento_maquinarias')
    else:
        form = RecepcionMaquinariaForm(instance=mant)
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Recepcionar Maquinaria: {mant.maquinaria.patente_o_codigo}',
        'url_volver': reverse_lazy('mantenimiento_maquinarias')
    })


@login_required
@permission_required('inventory.view_transferenciaactivo', raise_exception=True)
def transferencia_activo_view(request):
    transferencias = TransferenciaActivo.objects.select_related(
        'bodega_origen', 'bodega_destino', 'herramienta', 'maquinaria', 'usuario_despacha', 'usuario_recibe'
    ).order_by('-fecha_despacho')
    if request.method == 'POST' and _can(request.user, 'inventory.add_transferenciaactivo'):
        form = TransferenciaActivoForm(request.POST)
        if form.is_valid():
            ta = form.save(commit=False)
            ta.usuario_despacha = request.user
            ta.estado = 'EN TRANSITO'
            ta.save()
            messages.success(request, f'GDI #{ta.idTransferencia} registrada. Quedó en tránsito hasta ser recepcionada.')
            return redirect('transferencias_activos')
        else:
            messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = TransferenciaActivoForm()
    return render(request, 'inventory/transferencia_activos.html', {
        'transferencias': transferencias, 'form': form
    })


@login_required
@permission_required('inventory.change_transferenciaactivo', raise_exception=True)
def recibir_transferencia_activo(request, pk):
    import datetime
    ta = get_object_or_404(TransferenciaActivo, pk=pk)
    if ta.estado == 'RECEPCION OK':
        messages.warning(request, f'La GDI #{ta.idTransferencia} ya fue recepcionada.')
        return redirect('transferencias_activos')
    if request.method == 'POST':
        if ta.tipo_activo == 'HERRAMIENTA' and ta.herramienta:
            ta.herramienta.bodega_actual = ta.bodega_destino
            ta.herramienta.save(update_fields=['bodega_actual'])
        elif ta.tipo_activo == 'MAQUINARIA' and ta.maquinaria:
            ta.maquinaria.bodega_actual = ta.bodega_destino
            ta.maquinaria.save(update_fields=['bodega_actual'])
        ta.estado = 'RECEPCION OK'
        ta.usuario_recibe = request.user
        ta.fecha_recepcion = datetime.date.today()
        ta.observacion_recepcion = request.POST.get('observacion_recepcion', '').strip() or None
        ta.save(update_fields=['estado', 'usuario_recibe', 'fecha_recepcion', 'observacion_recepcion'])
        activo = ta.herramienta.nomHerramienta if ta.herramienta else ta.maquinaria.patente_o_codigo
        messages.success(request, f'GRI registrada: "{activo}" ahora está en {ta.bodega_destino}.')
        return redirect('transferencias_activos')
    return render(request, 'inventory/transferencia_activo_recibir.html', {'ta': ta})
