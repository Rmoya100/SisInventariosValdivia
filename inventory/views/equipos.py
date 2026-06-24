import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import modelformset_factory
from ..decorators import permission_required
from ..perms import user_has_custom_perm
from django.db.models import Q
from ..models import (
    Herramienta, MantenimientoHerramienta, Maquinaria, MantenimientoMaquinaria,
    TransferenciaActivo, DetalleTransferenciaActivo
)
from ..forms import (
    HerramientaForm, MantenimientoHerramientaForm, RecepcionHerramientaForm,
    MaquinariaForm, ActualizarLecturaForm, MantenimientoMaquinariaForm, RecepcionMaquinariaForm,
    TransferenciaActivoForm, DetalleTransferenciaActivoFormSet, DetalleTransferenciaActivoRecibirForm
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


class TransferenciaActivoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_transferenciaactivo'
    model = TransferenciaActivo
    template_name = 'inventory/transferencia_activos_list.html'
    context_object_name = 'transferencias'

    def get_queryset(self):
        return TransferenciaActivo.objects.select_related(
            'bodega_origen', 'bodega_destino', 'usuario_despacha', 'usuario_recibe'
        ).prefetch_related('detalles_activos__herramienta', 'detalles_activos__maquinaria').order_by('-fecha_despacho')


def _activos_json():
    herramientas = list(Herramienta.objects.select_related('bodega_actual').values(
        'idHerramienta', 'nomHerramienta', 'codigo', 'bodega_actual_id', 'en_reparacion'
    ))
    maquinarias = list(Maquinaria.objects.select_related('bodega_actual').values(
        'idMaquinaria', 'patente_o_codigo', 'tipo_maquina', 'bodega_actual_id', 'en_reparacion'
    ))
    return herramientas, maquinarias


@login_required
@permission_required('inventory.add_transferenciaactivo', raise_exception=True)
def transferencia_activo_crear(request):
    herramientas, maquinarias = _activos_json()
    if request.method == 'POST':
        form = TransferenciaActivoForm(request.POST)
        formset = DetalleTransferenciaActivoFormSet(request.POST, prefix='detalles')
        if form.is_valid() and formset.is_valid():
            bodega_origen = form.cleaned_data['bodega_origen']
            # Validate each asset belongs to origin warehouse
            hay_error = False
            for f in formset.forms:
                if not f.cleaned_data or f.cleaned_data.get('DELETE'):
                    continue
                tipo = f.cleaned_data.get('tipo_activo')
                herr = f.cleaned_data.get('herramienta')
                maq = f.cleaned_data.get('maquinaria')
                activo = herr if tipo == 'HERRAMIENTA' else maq
                if activo and activo.bodega_actual != bodega_origen:
                    f.add_error(None, f'"{activo}" no está en la bodega de origen ({bodega_origen}).')
                    hay_error = True
                if activo and activo.en_reparacion:
                    f.add_error(None, f'"{activo}" está en reparación y no puede ser transferida.')
                    hay_error = True
            if hay_error:
                return render(request, 'inventory/transferencia_activos_form.html', {
                    'form': form, 'detalles': formset,
                    'herramientas_json': herramientas, 'maquinarias_json': maquinarias,
                    'titulo': 'Nueva GDI de Activos',
                })
            ta = form.save(commit=False)
            ta.usuario_despacha = request.user
            ta.estado = 'EN TRANSITO'
            ta.save()
            formset.instance = ta
            formset.save()
            messages.success(request, f'GDI #{ta.idTransferencia} creada. Quedó en tránsito.')
            return redirect('transferencias_activos')
    else:
        form = TransferenciaActivoForm()
        formset = DetalleTransferenciaActivoFormSet(prefix='detalles')
    return render(request, 'inventory/transferencia_activos_form.html', {
        'form': form, 'detalles': formset,
        'herramientas_json': herramientas, 'maquinarias_json': maquinarias,
        'titulo': 'Nueva GDI de Activos',
    })


@login_required
@permission_required('inventory.change_transferenciaactivo', raise_exception=True)
def transferencia_activo_editar(request, pk):
    ta = get_object_or_404(TransferenciaActivo, pk=pk)
    if ta.estado == 'RECEPCION OK':
        messages.warning(request, f'La GDI #{ta.idTransferencia} ya fue completamente recepcionada y no puede editarse.')
        return redirect('transferencias_activos')
    herramientas, maquinarias = _activos_json()
    if request.method == 'POST':
        form = TransferenciaActivoForm(request.POST, instance=ta)
        formset = DetalleTransferenciaActivoFormSet(request.POST, instance=ta, prefix='detalles')
        if form.is_valid() and formset.is_valid():
            bodega_origen = form.cleaned_data['bodega_origen']
            hay_error = False
            for f in formset.forms:
                if not f.cleaned_data or f.cleaned_data.get('DELETE'):
                    continue
                tipo = f.cleaned_data.get('tipo_activo')
                herr = f.cleaned_data.get('herramienta')
                maq = f.cleaned_data.get('maquinaria')
                activo = herr if tipo == 'HERRAMIENTA' else maq
                if activo and activo.bodega_actual != bodega_origen:
                    f.add_error(None, f'"{activo}" no está en la bodega de origen ({bodega_origen}).')
                    hay_error = True
            if hay_error:
                return render(request, 'inventory/transferencia_activos_form.html', {
                    'form': form, 'detalles': formset, 'ta': ta,
                    'herramientas_json': herramientas, 'maquinarias_json': maquinarias,
                    'titulo': f'Editar GDI #{ta.idTransferencia}',
                })
            form.save()
            formset.save()
            messages.success(request, f'GDI #{ta.idTransferencia} actualizada.')
            return redirect('transferencias_activos')
    else:
        form = TransferenciaActivoForm(instance=ta)
        formset = DetalleTransferenciaActivoFormSet(instance=ta, prefix='detalles')
    return render(request, 'inventory/transferencia_activos_form.html', {
        'form': form, 'detalles': formset, 'ta': ta,
        'herramientas_json': herramientas, 'maquinarias_json': maquinarias,
        'titulo': f'Editar GDI #{ta.idTransferencia}',
    })


@login_required
@permission_required('inventory.change_transferenciaactivo', raise_exception=True)
def recibir_transferencia_activo(request, pk):
    ta = get_object_or_404(TransferenciaActivo, pk=pk)
    if ta.estado == 'RECEPCION OK':
        messages.warning(request, f'La GDI #{ta.idTransferencia} ya fue completamente recepcionada.')
        return redirect('transferencias_activos')

    detalles = ta.detalles_activos.select_related('herramienta', 'maquinaria').all()
    RecibirFormSet = modelformset_factory(
        DetalleTransferenciaActivo,
        form=DetalleTransferenciaActivoRecibirForm,
        extra=0,
    )

    if request.method == 'POST':
        formset = RecibirFormSet(request.POST, queryset=detalles)
        if formset.is_valid():
            for f in formset.forms:
                detalle = f.save(commit=False)
                if detalle.recibido:
                    activo = detalle.herramienta if detalle.tipo_activo == 'HERRAMIENTA' else detalle.maquinaria
                    if activo:
                        activo.bodega_actual = ta.bodega_destino
                        activo.save(update_fields=['bodega_actual'])
                detalle.save()

            ta.usuario_recibe = request.user
            ta.fecha_recepcion = datetime.date.today()
            ta.observacion_recepcion = request.POST.get('observacion_recepcion', '').strip() or None
            ta.save(update_fields=['usuario_recibe', 'fecha_recepcion', 'observacion_recepcion'])
            ta.actualizar_estado()
            messages.success(request, f'GRI registrada para GDI #{ta.idTransferencia}. Estado: {ta.get_estado_display()}.')
            return redirect('transferencias_activos')
    else:
        formset = RecibirFormSet(queryset=detalles)

    return render(request, 'inventory/transferencia_activo_recibir.html', {
        'ta': ta, 'formset': formset, 'detalles': detalles,
        'formset_zip': list(zip(formset.forms, detalles)),
    })
