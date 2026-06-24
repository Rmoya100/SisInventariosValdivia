from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import AdminOrPermissionRequiredMixin as PermissionRequiredMixin
from ..perms import user_has_custom_perm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from ..models import Salida, DetalleSalida, Ingreso, DetalleIngreso, Transferencia, DetalleTransferencia, Producto, StockProyecto, Partida, ModuloTorre
from ..forms import SalidaForm, DetalleSalidaFormSet, IngresoForm, DetalleIngresoFormSet, TransferenciaForm, DetalleTransferenciaFormSet
from ..auditoria import registrar as audit

class SalidaView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_salida'
    model = Salida
    form_class = SalidaForm
    template_name = 'inventory/salida_list.html'
    success_url = reverse_lazy('salidas')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        qs = Salida.objects.all().select_related('proyecto', 'modulo_torre', 'solicitante')
        if self.request.user.proyecto and not self.request.user.es_admin:
            qs = qs.filter(proyecto=self.request.user.proyecto)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalles'] = DetalleSalidaFormSet(self.request.POST)
        else:
            context['detalles'] = DetalleSalidaFormSet()

        productos = list(Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual'))

        if self.request.user.es_admin:
            from ..models import Bodega as _Bodega
            # Pasar datos de bodegas y stocks por proyecto para actualización JS
            context['bodegas_info_json'] = [
                {'id': b.idBodega, 'proyecto_id': b.proyecto_id, 'proyecto_nombre': b.proyecto.nombre}
                for b in _Bodega.objects.filter(activo=True, proyecto__isnull=False).select_related('proyecto')
            ]
            stocks_por_proyecto = {}
            for sp in StockProyecto.objects.values('proyecto_id', 'producto_id', 'cantidad'):
                pid = str(sp['proyecto_id'])
                prod_id = str(sp['producto_id'])
                if pid not in stocks_por_proyecto:
                    stocks_por_proyecto[pid] = {}
                stocks_por_proyecto[pid][prod_id] = sp['cantidad']
            context['stocks_por_proyecto_json'] = stocks_por_proyecto

            # Partidas y módulos/torres por proyecto (para filtrado JS al cambiar bodega)
            partidas_por_proyecto = {}
            for p in Partida.objects.filter(activo=True, proyecto__activo=True).values('idPartida', 'nombre', 'proyecto_id'):
                pid = str(p['proyecto_id'])
                partidas_por_proyecto.setdefault(pid, []).append({'id': p['idPartida'], 'nombre': p['nombre']})
            context['partidas_por_proyecto_json'] = partidas_por_proyecto

            modulos_por_proyecto = {}
            for m in ModuloTorre.objects.filter(activo=True, proyecto__activo=True).values('idModuloTorre', 'nombre', 'proyecto_id'):
                pid = str(m['proyecto_id'])
                modulos_por_proyecto.setdefault(pid, []).append({'id': m['idModuloTorre'], 'nombre': m['nombre']})
            context['modulos_por_proyecto_json'] = modulos_por_proyecto

            context['is_admin_salida'] = True
            for prod in productos:
                prod['stock_disponible'] = prod['stock_actual']
            context['proyecto_stock_label'] = 'Global'
        else:
            proyecto = self.request.user.get_proyecto_movimiento()
            if proyecto:
                stock_map = {
                    s['producto_id']: s['cantidad']
                    for s in StockProyecto.objects.filter(proyecto=proyecto).values('producto_id', 'cantidad')
                }
                for prod in productos:
                    prod['stock_disponible'] = stock_map.get(prod['cod_prod'], 0)
                context['proyecto_stock_label'] = proyecto.nombre
            else:
                for prod in productos:
                    prod['stock_disponible'] = prod['stock_actual']
                context['proyecto_stock_label'] = 'Global'

        context['productos_data'] = productos

        q = self.request.GET.get('q')
        salidas = self.get_queryset()
        if q:
            salidas = salidas.filter(
                Q(modulo_torre__nombre__icontains=q) |
                Q(numSalida__icontains=q) |
                Q(solicitante__nombre__icontains=q) |
                Q(solicitante__apellido__icontains=q)
            )

        from django.core.paginator import Paginator
        paginator = Paginator(salidas.order_by('-numSalida'), 25)
        page_obj = paginator.get_page(self.request.GET.get('page', 1))
        context['salidas'] = page_obj
        context['page_obj'] = page_obj
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalles = context['detalles']

        if self.request.user.es_admin:
            bodega = form.cleaned_data.get('bodega') or self.request.user.get_bodega_movimiento()
            proyecto = bodega.proyecto if bodega else self.request.user.get_proyecto_movimiento()
        else:
            proyecto = self.request.user.get_proyecto_movimiento()
            bodega = self.request.user.get_bodega_movimiento()

        if not proyecto:
            messages.error(self.request, 'El usuario no tiene un proyecto asignado para registrar la salida.')
            return self.render_to_response(self.get_context_data(form=form))
        if not bodega:
            messages.error(self.request, f'El proyecto {proyecto.nombre} no tiene una bodega activa asignada.')
            return self.render_to_response(self.get_context_data(form=form))

        if detalles.is_valid():
            from ..models import StockProyecto
            # Recopilar cantidades agrupadas por producto
            cantidades_solicitadas = {}
            for form_det in detalles.forms:
                if form_det.cleaned_data and not form_det.cleaned_data.get('DELETE', False):
                    prod = form_det.cleaned_data.get('producto')
                    cant = form_det.cleaned_data.get('cantidad', 0)
                    if prod and cant > 0:
                        cantidades_solicitadas[prod] = cantidades_solicitadas.get(prod, 0) + cant

            # Validar stock para cada producto agrupado
            hay_error_stock = False
            for prod, cant_req in cantidades_solicitadas.items():
                stock_val = 0
                if proyecto:
                    stock_proj = StockProyecto.objects.filter(producto=prod, proyecto=proyecto).first()
                    if stock_proj:
                        stock_val = stock_proj.cantidad
                else:
                    # Si no hay obra asignada, usar stock general
                    stock_val = prod.stock_actual

                if stock_val < cant_req:
                    messages.error(
                        self.request,
                        f"Stock insuficiente para {prod.nombre}. Stock disponible: {stock_val}. Solicitado: {cant_req}."
                    )
                    hay_error_stock = True
            
            if hay_error_stock:
                return self.render_to_response(self.get_context_data(form=form))

            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.proyecto = proyecto
                self.object.bodega = bodega
                self.object.save()
                detalles.instance = self.object
                instances = detalles.save(commit=False)
                for instance in instances:
                    instance.save()
                for instance in detalles.deleted_objects:
                    instance.delete()
                audit(
                    usuario=self.request.user,
                    tipo_accion='SALIDA_CREAR',
                    objeto_id=self.object.numSalida,
                    modulo='Salidas',
                    accion=f'Salida #{self.object.numSalida} — {proyecto.nombre} — {sum(cantidades_solicitadas.values())} unidades',
                    bodega=bodega,
                    datos={
                        'salida_id': self.object.numSalida,
                        'proyecto': proyecto.nombre,
                        'bodega': getattr(bodega, 'nombre', None),
                        'productos': [
                            {'nombre': p.nombre, 'cantidad': c}
                            for p, c in cantidades_solicitadas.items()
                        ],
                    },
                )
                messages.success(self.request, 'Salida y detalles guardados con éxito.')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class SalidaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_salida'
    model = Salida
    form_class = SalidaForm
    template_name = 'inventory/salida_form.html'
    success_url = reverse_lazy('salidas')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'bodega' in form.fields:
            form.fields['bodega'].disabled = True
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proyecto = self.object.proyecto
        productos = list(Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual'))
        if proyecto:
            stock_map = {
                s['producto_id']: s['cantidad']
                for s in StockProyecto.objects.filter(proyecto=proyecto).values('producto_id', 'cantidad')
            }
            for prod in productos:
                prod['stock_disponible'] = stock_map.get(prod['cod_prod'], 0)
        else:
            for prod in productos:
                prod['stock_disponible'] = prod['stock_actual']
        context['productos_data'] = productos
        context['proyecto_stock_label'] = proyecto.nombre if proyecto else 'Global'
        context['detalles_iniciales_json'] = [
            {
                'id': d.idDetalle,
                'producto_id': d.producto_id,
                'nombre': d.producto.nombre,
                'cantidad': float(d.cantidad),
            }
            for d in self.object.detalles.select_related('producto').all()
        ]
        return context

    def form_valid(self, form):
        from decimal import Decimal, InvalidOperation
        total_forms = int(self.request.POST.get('detalles-TOTAL_FORMS', 0))
        existing_ids = set(
            DetalleSalida.objects.filter(salida=self.object).values_list('idDetalle', flat=True)
        )
        existing_map = {d.idDetalle: d.cantidad for d in DetalleSalida.objects.filter(idDetalle__in=existing_ids)}
        submitted_ids, items = set(), []

        for i in range(total_forms):
            detail_id   = self.request.POST.get(f'detalles-{i}-id', '').strip()
            producto_id = self.request.POST.get(f'detalles-{i}-producto', '').strip()
            cant_str    = self.request.POST.get(f'detalles-{i}-cantidad', '').strip()
            if not producto_id or not cant_str:
                continue
            try:
                cantidad = Decimal(cant_str)
            except InvalidOperation:
                continue
            if cantidad <= 0:
                continue
            item = {
                'id': int(detail_id) if detail_id else None,
                'producto_id': int(producto_id),
                'cantidad': cantidad,
            }
            if item['id']:
                submitted_ids.add(item['id'])
            items.append(item)

        if not items:
            messages.error(self.request, 'Debe incluir al menos un producto en la salida.')
            return self.render_to_response(self.get_context_data(form=form))

        proyecto = self.object.proyecto
        if proyecto:
            incrementos = {}
            for item in items:
                old_qty = existing_map.get(item['id'], Decimal('0')) if item['id'] else Decimal('0')
                diff = item['cantidad'] - old_qty
                if diff > 0:
                    incrementos[item['producto_id']] = incrementos.get(item['producto_id'], Decimal('0')) + diff
            hay_error = False
            for prod_id, diff in incrementos.items():
                sp = StockProyecto.objects.filter(producto_id=prod_id, proyecto=proyecto).first()
                stock_val = sp.cantidad if sp else 0
                if stock_val < diff:
                    prod_obj = Producto.objects.get(pk=prod_id)
                    messages.error(
                        self.request,
                        f"Stock insuficiente para {prod_obj.nombre}. Disponible: {stock_val}. Incremento: {diff}."
                    )
                    hay_error = True
            if hay_error:
                return self.render_to_response(self.get_context_data(form=form))

        with transaction.atomic():
            self.object = form.save()
            for det in DetalleSalida.objects.filter(idDetalle__in=(existing_ids - submitted_ids)):
                det.delete()
            for item in items:
                if item['id'] and item['id'] in existing_ids:
                    det = DetalleSalida.objects.get(idDetalle=item['id'])
                    det.producto_id = item['producto_id']
                    det.cantidad    = item['cantidad']
                    det.save()
                else:
                    DetalleSalida.objects.create(
                        salida=self.object,
                        producto_id=item['producto_id'],
                        cantidad=item['cantidad'],
                    )
        audit(
            usuario=self.request.user,
            tipo_accion='SALIDA_EDITAR',
            objeto_id=self.object.numSalida,
            modulo='Salidas',
            accion=f'Salida #{self.object.numSalida} editada — {self.object.proyecto.nombre if self.object.proyecto else "S/P"}',
            bodega=self.object.bodega,
            datos={'salida_id': self.object.numSalida},
        )
        messages.success(self.request, f'Salida #{self.object.numSalida} actualizada con éxito.')
        return redirect(self.success_url)


class IngresoView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_ingreso'
    model = Ingreso
    form_class = IngresoForm
    template_name = 'inventory/ingreso_list.html'
    success_url = reverse_lazy('ingresos')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        qs = Ingreso.objects.all().select_related('orden_compra__proveedor')
        if self.request.user.proyecto and not self.request.user.es_admin:
            qs = qs.filter(proyecto=self.request.user.proyecto)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalles'] = DetalleIngresoFormSet(self.request.POST)
        else:
            context['detalles'] = DetalleIngresoFormSet()

        context['productos_data'] = list(
            Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual')
        )
            
        q = self.request.GET.get('q')
        ingresos = self.get_queryset()
        if q:
            ingresos = ingresos.filter(Q(orden_compra__numCompra__icontains=q) | Q(tipo_documento__icontains=q) | Q(num_documento__icontains=q) | Q(numIngreso__icontains=q))

        from django.core.paginator import Paginator
        paginator = Paginator(ingresos.order_by('numIngreso'), 25)
        page_obj = paginator.get_page(self.request.GET.get('page', 1))
        context['ingresos'] = page_obj
        context['page_obj'] = page_obj
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalles = context['detalles']
        orden_compra = form.cleaned_data.get('orden_compra')
        proyecto = (orden_compra.proyecto if orden_compra and orden_compra.proyecto_id else None) or self.request.user.get_proyecto_movimiento()
        bodega = (orden_compra.bodega if orden_compra and orden_compra.bodega_id else None)
        if not bodega and not orden_compra and self.request.user.es_admin:
            bodega = form.cleaned_data.get('bodega')
            if not bodega:
                messages.error(self.request, 'Debe seleccionar una bodega de destino.')
                return self.render_to_response(self.get_context_data(form=form))
            if not proyecto and bodega:
                proyecto = bodega.proyecto
        if not bodega and proyecto:
            bodega = proyecto.bodegas.filter(activo=True).order_by('pk').first()

        if not proyecto:
            messages.error(self.request, 'El usuario no tiene un proyecto asignado para registrar el ingreso.')
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
                    instance.save() # En models.py -> save() se actualiza el stock
                for instance in detalles.deleted_objects:
                    instance.delete()
                audit(
                    usuario=self.request.user,
                    tipo_accion='INGRESO_CREAR',
                    objeto_id=self.object.numIngreso,
                    modulo='Ingresos',
                    accion=f'Ingreso #{self.object.numIngreso} — OC {orden_compra.numCompra if orden_compra else "S/N"} — {proyecto.nombre}',
                    bodega=bodega,
                    datos={
                        'ingreso_id': self.object.numIngreso,
                        'orden_compra': orden_compra.numCompra if orden_compra else None,
                        'proyecto': proyecto.nombre,
                        'tipo_documento': self.object.tipo_documento,
                        'num_documento': self.object.num_documento,
                        'productos': [
                            {'nombre': inst.producto.nombre, 'cantidad': inst.cantidad, 'precio': float(inst.precio)}
                            for inst in instances
                        ],
                    },
                )
                messages.success(self.request, 'Ingreso y detalles guardados con éxito.')
            else:
                return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)


class IngresoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_ingreso'
    model = Ingreso
    form_class = IngresoForm
    template_name = 'inventory/ingreso_form.html'
    success_url = reverse_lazy('ingresos')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object.orden_compra_id:
            from ..models import OrdenCompra
            form.fields['orden_compra'].queryset = (
                form.fields['orden_compra'].queryset |
                OrdenCompra.objects.filter(pk=self.object.orden_compra_id)
            )
        form.fields['orden_compra'].disabled = True
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos_data'] = list(
            Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual')
        )
        context['detalles_iniciales_json'] = [
            {
                'id': d.idDetalle,
                'producto_id': d.producto_id,
                'nombre': d.producto.nombre,
                'cantidad': d.cantidad,
                'precio': float(d.precio),
            }
            for d in self.object.detalles.select_related('producto').all()
        ]
        return context

    def form_valid(self, form):
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        total_forms = int(self.request.POST.get('detalles-TOTAL_FORMS', 0))
        existing_ids = set(
            DetalleIngreso.objects.filter(ingreso=self.object).values_list('idDetalle', flat=True)
        )
        submitted_ids = set()
        items = []

        for i in range(total_forms):
            detail_id  = self.request.POST.get(f'detalles-{i}-id', '').strip()
            producto_id = self.request.POST.get(f'detalles-{i}-producto', '').strip()
            cantidad_str = self.request.POST.get(f'detalles-{i}-cantidad', '').strip()
            precio_str   = self.request.POST.get(f'detalles-{i}-precio', '').strip()
            if not producto_id or not cantidad_str:
                continue
            try:
                cantidad = float(cantidad_str)
                precio   = float(precio_str) if precio_str else 0.0
            except ValueError:
                continue
            if cantidad <= 0:
                continue
            item = {
                'id': int(detail_id) if detail_id else None,
                'producto_id': int(producto_id),
                'cantidad': cantidad,
                'precio': precio,
            }
            if item['id']:
                submitted_ids.add(item['id'])
            items.append(item)

        if not items:
            messages.error(self.request, 'Debe incluir al menos un producto en el ingreso.')
            return self.render_to_response(self.get_context_data(form=form))

        with transaction.atomic():
            self.object = form.save()

            for det in DetalleIngreso.objects.filter(idDetalle__in=(existing_ids - submitted_ids)):
                det.delete()

            for item in items:
                if item['id'] and item['id'] in existing_ids:
                    det = DetalleIngreso.objects.get(idDetalle=item['id'])
                    det.producto_id = item['producto_id']
                    det.cantidad    = item['cantidad']
                    det.precio      = item['precio']
                    det.subtotal    = item['cantidad'] * item['precio']
                    det.save()
                else:
                    DetalleIngreso.objects.create(
                        ingreso=self.object,
                        producto_id=item['producto_id'],
                        cantidad=item['cantidad'],
                        precio=item['precio'],
                        subtotal=item['cantidad'] * item['precio'],
                    )

        audit(
            usuario=self.request.user,
            tipo_accion='INGRESO_EDITAR',
            objeto_id=self.object.numIngreso,
            modulo='Ingresos',
            accion=f'Ingreso #{self.object.numIngreso} editado — {self.object.proyecto.nombre if self.object.proyecto else "S/P"}',
            bodega=self.object.bodega,
            datos={'ingreso_id': self.object.numIngreso},
        )
        messages.success(self.request, f'Ingreso #{self.object.numIngreso} actualizado con éxito.')
        return redirect(self.success_url)


class TransferenciaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_transferencia'
    model = Transferencia
    template_name = 'inventory/transferencia_list.html'
    context_object_name = 'transferencias'

    def get_queryset(self):
        qs = super().get_queryset().select_related('proyecto_origen', 'proyecto_destino')
        if self.request.user.proyecto and not self.request.user.es_admin:
            qs = qs.filter(Q(proyecto_origen=self.request.user.proyecto) | Q(proyecto_destino=self.request.user.proyecto))
        
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(proyecto_origen__nombre__icontains=q) | Q(proyecto_destino__nombre__icontains=q))
        return qs

class TransferenciaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_transferencia'
    model = Transferencia
    form_class = TransferenciaForm
    template_name = 'inventory/transferencia_form.html'
    success_url = reverse_lazy('transferencias')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalles'] = DetalleTransferenciaFormSet(self.request.POST, prefix='detalles')
        else:
            context['detalles'] = DetalleTransferenciaFormSet(prefix='detalles')

        # Para usuarios normales, mostrar stock de su proyecto
        proyecto_origen = self.request.user.get_proyecto_movimiento() if not self.request.user.es_admin else None
        productos = list(Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual'))
        if proyecto_origen:
            stock_map = {
                s['producto_id']: s['cantidad']
                for s in StockProyecto.objects.filter(proyecto=proyecto_origen).values('producto_id', 'cantidad')
            }
            for prod in productos:
                prod['stock_origen'] = stock_map.get(prod['cod_prod'], 0)
        else:
            for prod in productos:
                prod['stock_origen'] = prod['stock_actual']
        context['productos_data'] = productos
        context['proyecto_origen_nombre'] = proyecto_origen.nombre if proyecto_origen else None

        # Bodegas con su proyecto para el selector admin (lista Python, no JSON string)
        from ..models import Bodega as _Bodega
        context['bodegas_info_json'] = [
            {'id': b.idBodega, 'proyecto_id': b.proyecto_id, 'proyecto_nombre': b.proyecto.nombre}
            for b in _Bodega.objects.filter(activo=True, proyecto__isnull=False).select_related('proyecto')
        ]
        # Stock por proyecto — claves como strings para que coincidan con JSON (siempre son strings en JS)
        stocks_por_proyecto = {}
        for sp in StockProyecto.objects.values('proyecto_id', 'producto_id', 'cantidad'):
            pid = str(sp['proyecto_id'])
            prod_id = str(sp['producto_id'])
            if pid not in stocks_por_proyecto:
                stocks_por_proyecto[pid] = {}
            stocks_por_proyecto[pid][prod_id] = sp['cantidad']
        context['stocks_por_proyecto_json'] = stocks_por_proyecto
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalles = context['detalles']
        if detalles.is_valid():
            # Obtener el origen
            proyecto_origen = form.cleaned_data.get('proyecto_origen')
            if not proyecto_origen:
                # Si es nulo y el usuario tiene obra por defecto
                proyecto_origen = self.request.user.proyecto

            if proyecto_origen:
                from ..models import StockProyecto
                # Agrupar cantidades a transferir
                cantidades_solicitadas = {}
                for form_det in detalles.forms:
                    if form_det.cleaned_data and not form_det.cleaned_data.get('DELETE', False):
                        prod = form_det.cleaned_data.get('producto')
                        cant = form_det.cleaned_data.get('cantidad_enviada', 0)
                        if prod and cant > 0:
                            cantidades_solicitadas[prod] = cantidades_solicitadas.get(prod, 0) + cant

                hay_error_stock = False
                for prod, cant_req in cantidades_solicitadas.items():
                    stock_val = 0
                    stock_proj = StockProyecto.objects.filter(producto=prod, proyecto=proyecto_origen).first()
                    if stock_proj:
                        stock_val = stock_proj.cantidad

                    if stock_val < cant_req:
                        messages.error(
                            self.request,
                            f"Stock insuficiente en origen ({proyecto_origen.nombre}) para {prod.nombre}. Stock disponible: {stock_val}. Solicitado: {cant_req}."
                        )
                        hay_error_stock = True

                if hay_error_stock:
                    return self.render_to_response(self.get_context_data(form=form))

            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.usuario_despacha = self.request.user
                if not self.object.proyecto_origen and proyecto_origen:
                    self.object.proyecto_origen = proyecto_origen
                self.object.save()
                detalles.instance = self.object
                instances = detalles.save(commit=False)
                for instance in instances:
                    instance.save()
                self.object.actualizar_estado()
            audit(
                usuario=self.request.user,
                tipo_accion='TRANSFERENCIA_DESPACHAR',
                objeto_id=self.object.idTransferencia,
                modulo='Transferencias',
                accion=f'GDI #{self.object.idTransferencia} — {self.object.proyecto_origen.nombre} → {self.object.proyecto_destino.nombre}',
                bodega=self.object.proyecto_origen.bodegas.filter(activo=True).order_by('pk').first() if self.object.proyecto_origen else None,
                datos={
                    'transferencia_id': self.object.idTransferencia,
                    'origen': self.object.proyecto_origen.nombre,
                    'destino': self.object.proyecto_destino.nombre,
                    'productos': [
                        {'nombre': inst.producto.nombre, 'enviada': inst.cantidad_enviada}
                        for inst in instances
                    ],
                },
            )
            messages.success(self.request, 'Transferencia creada con éxito.')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class TransferenciaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_transferencia'
    model = Transferencia
    form_class = TransferenciaForm
    template_name = 'inventory/transferencia_form.html'
    success_url = reverse_lazy('transferencias')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalles'] = DetalleTransferenciaFormSet(self.request.POST, instance=self.object, prefix='detalles')
        else:
            context['detalles'] = DetalleTransferenciaFormSet(instance=self.object, prefix='detalles')

        # Para usuarios normales, mostrar stock de su proyecto (o el de la GDI editada)
        proyecto_origen = (getattr(self, 'object', None) and self.object.proyecto_origen) or (
            self.request.user.get_proyecto_movimiento() if not self.request.user.es_admin else None
        )
        productos = list(Producto.objects.all().order_by('nombre').values('cod_prod', 'nombre', 'stock_actual'))
        if proyecto_origen:
            stock_map = {
                s['producto_id']: s['cantidad']
                for s in StockProyecto.objects.filter(proyecto=proyecto_origen).values('producto_id', 'cantidad')
            }
            for prod in productos:
                prod['stock_origen'] = stock_map.get(prod['cod_prod'], 0)
        else:
            for prod in productos:
                prod['stock_origen'] = prod['stock_actual']
        context['productos_data'] = productos
        context['proyecto_origen_nombre'] = proyecto_origen.nombre if proyecto_origen else None

        from ..models import Bodega as _Bodega
        context['bodegas_info_json'] = [
            {'id': b.idBodega, 'proyecto_id': b.proyecto_id, 'proyecto_nombre': b.proyecto.nombre}
            for b in _Bodega.objects.filter(activo=True, proyecto__isnull=False).select_related('proyecto')
        ]
        stocks_por_proyecto = {}
        for sp in StockProyecto.objects.values('proyecto_id', 'producto_id', 'cantidad'):
            pid = str(sp['proyecto_id'])
            prod_id = str(sp['producto_id'])
            if pid not in stocks_por_proyecto:
                stocks_por_proyecto[pid] = {}
            stocks_por_proyecto[pid][prod_id] = sp['cantidad']
        context['stocks_por_proyecto_json'] = stocks_por_proyecto
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalles = context['detalles']
        if detalles.is_valid():
            proyecto_origen = form.cleaned_data.get('proyecto_origen') or self.object.proyecto_origen
            
            if proyecto_origen:
                from ..models import StockProyecto, DetalleTransferencia
                # Agrupar cantidades solicitadas vs actuales ya restadas en BD
                cantidades_solicitadas = {}
                for form_det in detalles.forms:
                    if form_det.cleaned_data:
                        prod = form_det.cleaned_data.get('producto')
                        cant = form_det.cleaned_data.get('cantidad_enviada', 0)
                        is_delete = form_det.cleaned_data.get('DELETE', False)
                        if prod:
                            # Si ya existía el detalle, parte del stock ya se descontó
                            original_cant = 0
                            if form_det.instance and form_det.instance.pk:
                                original_cant = DetalleTransferencia.objects.get(pk=form_det.instance.pk).cantidad_enviada

                            diff = (0 if is_delete else cant) - original_cant
                            if diff > 0:
                                cantidades_solicitadas[prod] = cantidades_solicitadas.get(prod, 0) + diff

                hay_error_stock = False
                for prod, cant_diff in cantidades_solicitadas.items():
                    stock_val = 0
                    stock_proj = StockProyecto.objects.filter(producto=prod, proyecto=proyecto_origen).first()
                    if stock_proj:
                        stock_val = stock_proj.cantidad

                    # Comparar con la diferencia incremental
                    if stock_val < cant_diff:
                        messages.error(
                            self.request,
                            f"Stock insuficiente en origen ({proyecto_origen.nombre}) para {prod.nombre}. Stock disponible: {stock_val}. Incremento solicitado: {cant_diff}."
                        )
                        hay_error_stock = True

                if hay_error_stock:
                    return self.render_to_response(self.get_context_data(form=form))

            with transaction.atomic():
                self.object = form.save()
                detalles.instance = self.object
                instances = detalles.save(commit=False)
                for instance in instances:
                    # Encontrar el valor anterior para ajustar en StockProyecto
                    # Ya que el model DetalleTransferencia.save por defecto solo resta en la creación,
                    # manejemos el ajuste manual aquí si es una actualización.
                    if instance.pk:
                        original = DetalleTransferencia.objects.get(pk=instance.pk)
                        diff = instance.cantidad_enviada - original.cantidad_enviada
                        if diff != 0 and proyecto_origen:
                            from django.db.models import F
                            stock_orig, _ = StockProyecto.objects.get_or_create(producto=instance.producto, proyecto=proyecto_origen)
                            StockProyecto.objects.filter(pk=stock_orig.pk).update(cantidad=F('cantidad') - diff)
                    instance.save()
                # Eliminar detalles marcados para borrado
                for instance in detalles.deleted_objects:
                    instance.delete()
                self.object.actualizar_estado()
            audit(
                usuario=self.request.user,
                tipo_accion='TRANSFERENCIA_EDITAR',
                objeto_id=self.object.idTransferencia,
                modulo='Transferencias',
                accion=f'GDI #{self.object.idTransferencia} editada — {self.object.proyecto_origen.nombre} → {self.object.proyecto_destino.nombre}',
                bodega=self.object.proyecto_origen.bodegas.filter(activo=True).order_by('pk').first() if self.object.proyecto_origen else None,
                datos={
                    'transferencia_id': self.object.idTransferencia,
                    'origen': self.object.proyecto_origen.nombre,
                    'destino': self.object.proyecto_destino.nombre,
                },
            )
            messages.success(self.request, 'Transferencia actualizada con éxito.')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

@login_required
def recibir_transferencia(request, pk):
    transferencia = get_object_or_404(Transferencia, pk=pk)
    
    if not (request.user.es_admin or user_has_custom_perm(request.user, 'inventory.change_transferencia')):
        messages.error(request, 'No tienes permiso para recibir transferencias.')
        return redirect('index')

    from ..forms import DetalleTransferenciaRecibirForm
    from django.forms import modelformset_factory
    
    DetalleRecibirFormSet = modelformset_factory(
        DetalleTransferencia,
        form=DetalleTransferenciaRecibirForm,
        extra=0
    )

    if request.method == 'POST':
        formset = DetalleRecibirFormSet(request.POST, queryset=transferencia.detalles.all())
        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                for instance in instances:
                    # Encontrar el valor anterior de cantidad_recibida en la BD para ajustar la diferencia
                    original = DetalleTransferencia.objects.get(pk=instance.pk)
                    diff = instance.cantidad_recibida - original.cantidad_recibida
                    
                    if diff != 0:
                        from django.db.models import F
                        from ..models import StockProyecto
                        stock_dest, _ = StockProyecto.objects.get_or_create(
                            producto=instance.producto,
                            proyecto=transferencia.proyecto_destino
                        )
                        StockProyecto.objects.filter(pk=stock_dest.pk).update(cantidad=F('cantidad') + diff)
                    
                    instance.save(update_fields=['cantidad_recibida'])
                
                transferencia.usuario_recibe = request.user
                transferencia.actualizar_estado()
                transferencia.save(update_fields=['usuario_recibe'])
            audit(
                usuario=request.user,
                tipo_accion='TRANSFERENCIA_RECIBIR',
                objeto_id=transferencia.idTransferencia,
                modulo='Transferencias',
                accion=f'GDI #{transferencia.idTransferencia} recibida ({transferencia.estado}) — {transferencia.proyecto_destino.nombre}',
                bodega=transferencia.proyecto_destino.bodegas.filter(activo=True).order_by('pk').first() if transferencia.proyecto_destino else None,
                datos={
                    'transferencia_id': transferencia.idTransferencia,
                    'origen': transferencia.proyecto_origen.nombre,
                    'destino': transferencia.proyecto_destino.nombre,
                    'estado': transferencia.estado,
                    'productos': [
                        {
                            'nombre': d.producto.nombre,
                            'enviada': d.cantidad_enviada,
                            'recibida': d.cantidad_recibida,
                        }
                        for d in transferencia.detalles.select_related('producto')
                    ],
                },
            )
            messages.success(request, 'Recepción registrada con éxito.')
            return redirect('transferencias')
    else:
        formset = DetalleRecibirFormSet(queryset=transferencia.detalles.all())

    return render(request, 'inventory/transferencia_recibir.html', {'transferencia': transferencia, 'formset': formset})

@login_required
def trazabilidad_list(request):
    from django.core.paginator import Paginator
    from ..models import Bodega

    if not (request.user.es_admin or user_has_custom_perm(request.user, 'inventory.view_producto')):
        messages.error(request, 'No tienes permisos para ver esto.')
        return redirect('index')

    product_id = request.GET.get('producto', '').strip()
    bodega_id  = request.GET.get('bodega_id', '').strip()
    desde      = request.GET.get('desde', '').strip()
    hasta      = request.GET.get('hasta', '').strip()

    productos = Producto.objects.all().order_by('nombre')
    bodegas   = Bodega.objects.order_by('nombre')

    ingresos = DetalleIngreso.objects.select_related(
        'producto', 'ingreso', 'ingreso__proyecto', 'ingreso__bodega', 'ingreso__orden_compra'
    )
    salidas = DetalleSalida.objects.select_related(
        'producto', 'salida', 'salida__proyecto', 'salida__bodega', 'salida__modulo_torre'
    )
    transferencias = DetalleTransferencia.objects.select_related(
        'producto', 'transferencia',
        'transferencia__proyecto_origen', 'transferencia__proyecto_destino',
    )

    if product_id:
        ingresos       = ingresos.filter(producto_id=product_id)
        salidas        = salidas.filter(producto_id=product_id)
        transferencias = transferencias.filter(producto_id=product_id)

    if bodega_id:
        ingresos = ingresos.filter(ingreso__bodega_id=bodega_id)
        salidas  = salidas.filter(salida__bodega_id=bodega_id)
        from ..models import Proyecto
        pids = list(Proyecto.objects.filter(bodegas__pk=bodega_id).values_list('pk', flat=True))
        transferencias = transferencias.filter(
            Q(transferencia__proyecto_origen_id__in=pids) |
            Q(transferencia__proyecto_destino_id__in=pids)
        )

    if desde:
        ingresos       = ingresos.filter(ingreso__fecha__gte=desde)
        salidas        = salidas.filter(salida__fecha__gte=desde)
        transferencias = transferencias.filter(transferencia__fecha_despacho__gte=desde)
    if hasta:
        ingresos       = ingresos.filter(ingreso__fecha__lte=hasta)
        salidas        = salidas.filter(salida__fecha__lte=hasta)
        transferencias = transferencias.filter(transferencia__fecha_despacho__lte=hasta)

    movimientos = []
    for d in ingresos:
        movimientos.append({
            'fecha':    d.ingreso.fecha,
            'tipo':     'INGRESO',
            'producto': d.producto.nombre,
            'bodega':   d.ingreso.bodega.nombre if d.ingreso.bodega else (d.ingreso.proyecto.nombre if d.ingreso.proyecto else '—'),
            'cantidad': d.cantidad,
            'doc_num':  d.ingreso.numIngreso,
            'ref_principal': f'OC {d.ingreso.orden_compra.numCompra}' if d.ingreso.orden_compra else f'Ingreso #{d.ingreso.numIngreso}',
            'ref_extra': f'{d.ingreso.tipo_documento} · N° {d.ingreso.num_documento}',
        })
    for d in salidas:
        modulo = str(d.salida.modulo_torre) if d.salida.modulo_torre else None
        movimientos.append({
            'fecha':    d.salida.fecha,
            'tipo':     'SALIDA',
            'producto': d.producto.nombre,
            'bodega':   d.salida.bodega.nombre if d.salida.bodega else (d.salida.proyecto.nombre if d.salida.proyecto else '—'),
            'cantidad': d.cantidad,
            'doc_num':  d.salida.numSalida,
            'ref_principal': modulo or f'Salida #{d.salida.numSalida}',
            'ref_extra': f'Módulo: {modulo}' if modulo else '',
        })
    for d in transferencias:
        t = d.transferencia
        if d.cantidad_enviada > 0:
            movimientos.append({
                'fecha':    t.fecha_despacho,
                'tipo':     'GDI_ENVIO',
                'producto': d.producto.nombre,
                'bodega':   t.proyecto_origen.nombre,
                'cantidad': d.cantidad_enviada,
                'doc_num':  t.idTransferencia,
                'ref_principal': t.proyecto_destino.nombre,
                'ref_extra': f'Estado: {t.get_estado_display()}',
            })
        if d.cantidad_recibida > 0:
            movimientos.append({
                'fecha':    t.fecha_despacho,
                'tipo':     'GDI_RECEP',
                'producto': d.producto.nombre,
                'bodega':   t.proyecto_destino.nombre,
                'cantidad': d.cantidad_recibida,
                'doc_num':  t.idTransferencia,
                'ref_principal': t.proyecto_origen.nombre,
                'ref_extra': f'Estado: {t.get_estado_display()}',
            })

    movimientos.sort(key=lambda m: m['fecha'], reverse=True)

    paginator = Paginator(movimientos, 50)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'inventory/reporte_trazabilidad_producto_list.html', {
        'page_obj':         page_obj,
        'paginator':        paginator,
        'productos':        productos,
        'bodegas':          bodegas,
        'producto_id':      product_id,
        'filtro_bodega_id': bodega_id,
        'filtro_desde':     desde,
        'filtro_hasta':     hasta,
        'total':            len(movimientos),
    })


@login_required
def api_stock_disponible(request):
    """Retorna el stock disponible de un producto para el proyecto del usuario actual."""
    producto_id = request.GET.get('producto_id')
    if not producto_id:
        return JsonResponse({'error': 'producto_id requerido'}, status=400)

    try:
        producto = Producto.objects.get(pk=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    proyecto = request.user.get_proyecto_movimiento()
    if proyecto and not request.user.es_admin:
        sp = StockProyecto.objects.filter(producto=producto, proyecto=proyecto).first()
        stock = sp.cantidad if sp else 0
        label = proyecto.nombre
    else:
        stock = producto.stock_actual
        label = 'Global'

    return JsonResponse({'stock': stock, 'label': label, 'producto': producto.nombre})


@login_required
def api_partidas_por_proyecto(request):
    proyecto_id = request.GET.get('proyecto_id')
    if not proyecto_id:
        return JsonResponse({'partidas': []})
    partidas = list(
        Partida.objects.filter(activo=True, proyecto_id=proyecto_id, proyecto__activo=True)
        .order_by('nombre').values('idPartida', 'nombre')
    )
    return JsonResponse({'partidas': partidas})


@login_required
def api_modulos_torre_por_proyecto(request):
    proyecto_id = request.GET.get('proyecto_id')
    if not proyecto_id:
        return JsonResponse({'modulos_torre': []})
    modulos = list(
        ModuloTorre.objects.filter(activo=True, proyecto_id=proyecto_id, proyecto__activo=True)
        .order_by('nombre').values('idModuloTorre', 'nombre')
    )
    return JsonResponse({'modulos_torre': modulos})
