from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from ..mixins import AdminOrPermissionRequiredMixin as PermissionRequiredMixin
from ..models import Gasto, Fase, Proyecto, DetalleIngreso
from ..forms import GastoForm, FaseForm


class GastoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_gasto'
    model = Gasto
    template_name = 'inventory/gasto_list.html'
    context_object_name = 'gastos'
    paginate_by = 25

    def get_queryset(self):
        qs = Gasto.objects.select_related('maquinaria', 'trabajador', 'modulo_torre', 'fase', 'proyecto').filter(activo=True)
        q = self.request.GET.get('q')
        concepto = self.request.GET.get('concepto')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        modulo_torre = self.request.GET.get('modulo_torre')
        fase = self.request.GET.get('fase')
        proyecto = self.request.GET.get('proyecto')

        if q:
            qs = qs.filter(
                Q(observaciones__icontains=q)
                | Q(maquinaria__patente_o_codigo__icontains=q)
                | Q(maquinaria__marca__icontains=q)
                | Q(maquinaria__modelo__icontains=q)
                | Q(trabajador__nombre__icontains=q)
                | Q(trabajador__apellido__icontains=q)
            )
        if concepto:
            qs = qs.filter(concepto=concepto)
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if modulo_torre:
            qs = qs.filter(modulo_torre_id=modulo_torre)
        if fase:
            qs = qs.filter(fase_id=fase)
        if proyecto:
            qs = qs.filter(proyecto_id=proyecto)
        return qs

    def get_context_data(self, **kwargs):
        from ..models import ModuloTorre
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['conceptos'] = Gasto.CONCEPTO_CHOICES
        context['total_gastos'] = queryset.aggregate(total=Sum('monto'))['total'] or 0
        context['modulos_torre'] = ModuloTorre.objects.filter(activo=True)
        context['fases'] = Fase.objects.filter(activo=True)
        context['proyectos'] = Proyecto.objects.filter(activo=True)
        return context


class GastoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_gasto'
    model = Gasto
    form_class = GastoForm
    template_name = 'inventory/gasto_form.html'
    success_url = reverse_lazy('gastos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Gasto'
        context['url_volver'] = reverse_lazy('gastos')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Gasto registrado correctamente.')
        return super().form_valid(form)


class GastoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_gasto'
    model = Gasto
    form_class = GastoForm
    template_name = 'inventory/gasto_form.html'
    success_url = reverse_lazy('gastos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Gasto'
        context['url_volver'] = reverse_lazy('gastos')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Gasto actualizado correctamente.')
        return super().form_valid(form)


class GastoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_gasto'
    model = Gasto
    success_url = reverse_lazy('gastos')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Eliminar Gasto'
        context['url_volver'] = reverse_lazy('gastos')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save(update_fields=['activo'])
        messages.success(self.request, 'Gasto eliminado correctamente.')
        return redirect(self.success_url)


class FaseListView(LoginRequiredMixin, ListView):
    model = Fase
    template_name = 'inventory/fase_list.html'
    context_object_name = 'fases'
    paginate_by = 25

    def get_queryset(self):
        qs = Fase.all_objects.all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        return qs


class FaseCreateView(LoginRequiredMixin, CreateView):
    model = Fase
    form_class = FaseForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('fases')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Fase'
        context['url_volver'] = reverse_lazy('fases')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Fase creada correctamente.')
        return super().form_valid(form)


class FaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Fase
    form_class = FaseForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('fases')

    def get_queryset(self):
        return Fase.all_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Fase'
        context['url_volver'] = reverse_lazy('fases')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Fase actualizada correctamente.')
        return super().form_valid(form)


class ResumenGastosProyectoView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'inventory.view_gasto'
    template_name = 'inventory/resumen_gastos_proyecto.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        proyectos = Proyecto.objects.filter(activo=True).order_by('nombre')
        resumen = []

        for proyecto in proyectos:
            # Gasto en materiales: suma de subtotales de ingresos recepcionados
            materiales = DetalleIngreso.objects.filter(
                ingreso__proyecto=proyecto
            ).aggregate(total=Sum('subtotal'))['total'] or 0

            # Gastos manuales agrupados por concepto
            gastos_qs = Gasto.objects.filter(proyecto=proyecto, activo=True)
            totales_concepto = {
                choice[0]: 0 for choice in Gasto.CONCEPTO_CHOICES
            }
            for gasto in gastos_qs.values('concepto').annotate(total=Sum('monto')):
                totales_concepto[gasto['concepto']] = gasto['total'] or 0

            total_manuales = sum(totales_concepto.values())
            total_proyecto = materiales + total_manuales

            resumen.append({
                'proyecto': proyecto,
                'materiales': materiales,
                'petroleo': totales_concepto.get('PETROLEO', 0),
                'bencina': totales_concepto.get('BENCINA', 0),
                'mano_obra': totales_concepto.get('MANO_OBRA', 0),
                'sueldos': totales_concepto.get('SUELDOS', 0),
                'otros': totales_concepto.get('OTRO', 0),
                'total_manuales': total_manuales,
                'total': total_proyecto,
            })

        context['resumen'] = resumen
        context['gran_total'] = sum(r['total'] for r in resumen)
        return context
