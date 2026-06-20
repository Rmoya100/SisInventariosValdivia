from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import AdminOrPermissionRequiredMixin as PermissionRequiredMixin
from django.db.models import Q
from django.db.models import Sum
from ..models import Producto, Categoria, Bodega, StockProyecto, UnidadMedida
from ..forms import ProductoForm, ProductoCreateForm, ProductoEditForm, CategoriaForm, BodegaForm, UnidadMedidaForm

class ProductoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_producto'
    model = Producto
    template_name = 'inventory/producto_list.html'
    context_object_name = 'productos'

    def get_queryset(self):
        qs = super().get_queryset().select_related('categoria')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(categoria__nombre__icontains=q))
        return qs

class ProductoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_producto'
    model = Producto
    form_class = ProductoCreateForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('productos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Producto'
        context['url_volver'] = reverse_lazy('productos')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        proyecto = form.cleaned_data.get('proyecto')
        if proyecto and self.object.stock_inicial > 0:
            StockProyecto.objects.create(
                producto=self.object,
                proyecto=proyecto,
                cantidad=self.object.stock_inicial,
            )
        return response

class ProductoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_producto'
    model = Producto
    form_class = ProductoEditForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('productos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Producto'
        context['url_volver'] = reverse_lazy('productos')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.actualizar_stock()
        bodega = form.cleaned_data.get('bodega')
        if bodega:
            producto = self.object
            proyecto = bodega.proyecto
            stock_asignado = producto.stocks_proyecto.aggregate(total=Sum('cantidad'))['total'] or 0
            stock_libre = producto.stock_actual - stock_asignado
            StockProyecto.objects.create(
                producto=producto,
                proyecto=proyecto,
                cantidad=max(0, stock_libre),
            )
        return response

class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_producto'
    model = Producto
    success_url = reverse_lazy('productos')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Desactivar Producto'
        context['url_volver'] = reverse_lazy('productos')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save()
        messages.success(self.request, 'Producto desactivado correctamente.')
        return redirect(self.success_url)

class CategoriaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_categoria'
    model = Categoria
    template_name = 'inventory/categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs

class CategoriaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('categorias')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Categoría'
        context['url_volver'] = reverse_lazy('categorias')
        return context

class CategoriaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('categorias')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Categoría'
        context['url_volver'] = reverse_lazy('categorias')
        return context

class CategoriaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_categoria'
    model = Categoria
    success_url = reverse_lazy('categorias')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Desactivar Categoría'
        context['url_volver'] = reverse_lazy('categorias')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save()
        messages.success(self.request, 'Categoría desactivada correctamente.')
        return redirect(self.success_url)

class BodegaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_bodega'
    model = Bodega
    template_name = 'inventory/bodega_list.html'
    context_object_name = 'bodegas'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs

class BodegaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_bodega'
    model = Bodega
    form_class = BodegaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('bodegas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Bodega'
        context['url_volver'] = reverse_lazy('bodegas')
        return context

class BodegaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_bodega'
    model = Bodega
    form_class = BodegaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('bodegas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Bodega'
        context['url_volver'] = reverse_lazy('bodegas')
        return context

class BodegaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_bodega'
    model = Bodega
    success_url = reverse_lazy('bodegas')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Desactivar Bodega'
        context['url_volver'] = reverse_lazy('bodegas')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save()
        messages.success(self.request, 'Bodega desactivada correctamente.')
        return redirect(self.success_url)


class UnidadMedidaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_unidadmedida'
    model = UnidadMedida
    template_name = 'inventory/unidad_medida_list.html'
    context_object_name = 'unidades'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(abreviatura__icontains=q))
        return qs


class UnidadMedidaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_unidadmedida'
    model = UnidadMedida
    form_class = UnidadMedidaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('unidades_medida')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Unidad de Medida'
        context['url_volver'] = reverse_lazy('unidades_medida')
        return context


class UnidadMedidaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_unidadmedida'
    model = UnidadMedida
    form_class = UnidadMedidaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('unidades_medida')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Unidad de Medida'
        context['url_volver'] = reverse_lazy('unidades_medida')
        return context


class UnidadMedidaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'inventory.delete_unidadmedida'
    model = UnidadMedida
    success_url = reverse_lazy('unidades_medida')
    template_name = 'inventory/confirmar_eliminar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objeto'] = self.object
        context['titulo'] = 'Desactivar Unidad de Medida'
        context['url_volver'] = reverse_lazy('unidades_medida')
        return context

    def form_valid(self, form):
        self.object.activo = False
        self.object.save()
        messages.success(self.request, 'Unidad de medida desactivada correctamente.')
        return redirect(self.success_url)
