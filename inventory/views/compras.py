import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import AdminOrPermissionRequiredMixin as PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from ..models import Producto, Proveedor, OrdenCompra, Bodega
from ..forms import ProveedorForm, OrdenCompraForm, DetalleCompraFormSet
from ..auditoria import registrar as audit

class ProveedorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_proveedor'
    model = Proveedor
    template_name = 'inventory/proveedor_list.html'
    context_object_name = 'proveedores'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codProveedor__icontains=q))
        return qs

class ProveedorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_proveedor'
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('proveedores')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Proveedor'
        context['url_volver'] = reverse_lazy('proveedores')
        return context

class ProveedorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_proveedor'
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('proveedores')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Proveedor'
        context['url_volver'] = reverse_lazy('proveedores')
        return context

class ProveedorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_proveedor'
    model = Proveedor
    success_url = reverse_lazy('proveedores')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Desactivar Proveedor'
        context['url_volver'] = reverse_lazy('proveedores')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save()
        messages.success(self.request, 'Proveedor desactivado correctamente.')
        return redirect(self.success_url)

class OrdenCompraView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_ordencompra'
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'inventory/orden_list.html'
    success_url = reverse_lazy('ordenes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        qs = OrdenCompra.objects.all().select_related('proveedor')
        if self.request.user.proyecto and not self.request.user.es_admin:
            qs = qs.filter(proyecto=self.request.user.proyecto)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalles'] = DetalleCompraFormSet(self.request.POST, prefix='detalles')
        else:
            context['detalles'] = DetalleCompraFormSet(prefix='detalles')

        context['modo_edicion'] = False
        for _p in Producto.objects.all():
            _p.actualizar_stock()
        context['productos_data'] = list(
            Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual')
        )

        q = self.request.GET.get('q')
        ordenes = self.get_queryset()
        if q:
            ordenes = ordenes.filter(Q(proveedor__nombre__icontains=q) | Q(numCompra__icontains=q))

        context['ordenes'] = ordenes
        return context

    def form_valid(self, form):
        detalles = DetalleCompraFormSet(self.request.POST, prefix='detalles')
        from ..forms import _es_admin
        if _es_admin(self.request.user):
            bodega = form.cleaned_data.get('bodega') or self.request.user.get_bodega_movimiento()
            proyecto = bodega.proyecto if bodega else self.request.user.get_proyecto_movimiento()
        else:
            proyecto = self.request.user.get_proyecto_movimiento()
            bodega = self.request.user.get_bodega_movimiento()

        if not proyecto:
            messages.error(self.request, 'Debes seleccionar un proyecto para registrar la orden de compra.')
            return self.render_to_response(self.get_context_data(form=form))
        if not bodega:
            messages.error(self.request, f'El proyecto {proyecto.nombre} no tiene una bodega activa asignada.')
            return self.render_to_response(self.get_context_data(form=form))

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.proyecto = proyecto
            self.object.bodega = bodega

            if detalles.is_valid():
                self.object.save()
                detalles.instance = self.object
                instances = detalles.save(commit=False)
                for instance in instances:
                    instance.subtotal = instance.cantidad * instance.precio
                    instance.save()
                for instance in detalles.deleted_objects:
                    instance.delete()
                self.object.actualizar_estado()
                audit(
                    usuario=self.request.user,
                    tipo_accion='ORDEN_CREAR',
                    objeto_id=self.object.idCompra,
                    modulo='Ordenes de Compra',
                    accion=f'OC {self.object.numCompra} — {self.object.proveedor.nombre} — {proyecto.nombre}',
                    bodega=bodega,
                    datos={
                        'compra_id': self.object.idCompra,
                        'num_compra': self.object.numCompra,
                        'proveedor': self.object.proveedor.nombre,
                        'proyecto': proyecto.nombre,
                        'forma_pago': self.object.forma_de_pago,
                        'productos': [
                            {'nombre': inst.producto.nombre, 'cantidad': inst.cantidad, 'precio': float(inst.precio)}
                            for inst in instances
                        ],
                    },
                )
                messages.success(self.request, 'Orden de compra guardada con éxito.')
            else:
                return self.render_to_response(self.get_context_data(form=form))
        return redirect(self.success_url)


class OrdenCompraUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_ordencompra'
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'inventory/orden_list.html'
    success_url = reverse_lazy('ordenes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.estado == 'RECEPCION OK':
            messages.warning(request, 'No se puede editar una orden de compra con recepción completa.')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modo_edicion'] = True
        if self.request.POST:
            context['detalles'] = DetalleCompraFormSet(self.request.POST, instance=self.object, prefix='detalles')
        else:
            context['detalles'] = DetalleCompraFormSet(instance=self.object, prefix='detalles')
        # Ensure stock_actual is up-to-date before sending product data
        for _p in Producto.objects.all():
            _p.actualizar_stock()
        context['productos_data'] = list(
            Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual')
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalles = context['detalles']
        from ..forms import _es_admin
        with transaction.atomic():
            self.object = form.save(commit=False)
            # Para admin: actualizar bodega si cambió el proyecto
            if _es_admin(self.request.user):
                bodega = form.cleaned_data.get('bodega') or self.object.bodega or self.request.user.get_bodega_movimiento()
                if bodega:
                    self.object.bodega = bodega
                    self.object.proyecto = bodega.proyecto
            detalles.instance = self.object
            if detalles.is_valid():
                self.object.save()
                instances = detalles.save(commit=False)
                for instance in instances:
                    instance.subtotal = instance.cantidad * instance.precio
                    instance.save()
                for instance in detalles.deleted_objects:
                    instance.delete()
                self.object.actualizar_estado()
                audit(
                    usuario=self.request.user,
                    tipo_accion='ORDEN_EDITAR',
                    objeto_id=self.object.idCompra,
                    modulo='Ordenes de Compra',
                    accion=f'OC {self.object.numCompra} modificada — {self.object.proveedor.nombre}',
                    bodega=self.object.bodega,
                    datos={
                        'compra_id': self.object.idCompra,
                        'num_compra': self.object.numCompra,
                    },
                )
                messages.success(self.request, 'Orden modificada con éxito.')
            else:
                return self.render_to_response(self.get_context_data(form=form))
        return redirect(self.success_url)

@login_required
def get_orden_compra_detalle(request, orden_id):
    from ..models import DetalleIngreso
    from django.db.models import Sum

    orden = get_object_or_404(OrdenCompra, pk=orden_id)
    detalles = orden.detalles.select_related('producto').all()

    # Cantidades ya recibidas por producto en ingresos previos de esta OC
    recibidos = {
        r['producto_id']: r['total']
        for r in DetalleIngreso.objects.filter(
            ingreso__orden_compra=orden
        ).values('producto_id').annotate(total=Sum('cantidad'))
    }

    data = []
    for d in detalles:
        saldo = max(0, d.cantidad - recibidos.get(d.producto.pk, 0))
        if saldo > 0:
            data.append({
                'producto_id': d.producto.pk,
                'nombre': d.producto.nombre,
                'cantidad': saldo,
                'precio': float(d.precio),
            })

    return JsonResponse(data, safe=False)
