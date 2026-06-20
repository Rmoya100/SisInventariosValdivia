from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from ..mixins import AdminOrPermissionRequiredMixin as PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from ..decorators import permission_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from ..models import Usuario, Trabajador, Proyecto, Permiso, Empresa, ModuloTorre, Partida
from ..forms import UsuarioRegistroForm, UsuarioEditarForm, TrabajadorForm, ProyectoForm, EmpresaForm, ModuloTorreForm, PartidaForm

class UsuarioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_usuario'
    model = Usuario
    template_name = 'inventory/usuarios_list.html'
    context_object_name = 'usuarios'
    paginate_by = 25

    def get_queryset(self):
        qs = Usuario.objects.all().order_by('username')
        estado = self.request.GET.get('estado')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(trabajador__nombre__icontains=q) | Q(trabajador__apellido__icontains=q))
        if estado == 'activo':
            qs = qs.filter(is_active=True)
        elif estado == 'inactivo':
            qs = qs.filter(is_active=False)
        return qs

@login_required
@permission_required('inventory.change_usuario', raise_exception=True)
def editar_permisos(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)
    permiso_obj, _ = Permiso.objects.get_or_create(usuario=usuario_obj)
    modulos = [
        {'id': 'cat', 'nombre': 'Categorías'},
        {'id': 'prod', 'nombre': 'Productos'},
        {'id': 'prov', 'nombre': 'Proveedores'},
        {'id': 'ord', 'nombre': 'Órdenes de Compra'},
        {'id': 'ing', 'nombre': 'Ingresos'},
        {'id': 'sal', 'nombre': 'Salidas'},
        {'id': 'pro', 'nombre': 'Proyectos'},
        {'id': 'trab', 'nombre': 'Trabajadores'},
        {'id': 'tra', 'nombre': 'Transferencias'},
        {'id': 'herr', 'nombre': 'Herramientas'},
        {'id': 'mant_herr', 'nombre': 'Mantención Herramientas'},
        {'id': 'maq', 'nombre': 'Maquinaria'},
        {'id': 'mant_maq', 'nombre': 'Reparación Maquinaria'},
        {'id': 'gdi', 'nombre': 'GDI Activos'},
        {'id': 'gasto', 'nombre': 'Control de Gastos'},
    ]

    if request.method == 'POST':
        usuario_obj.es_admin = 'es_admin' in request.POST
        proyecto_id = request.POST.get('proyecto')
        proyectos_asignados_ids = request.POST.getlist('proyectos_asignados')
        if proyecto_id:
            usuario_obj.proyecto_id = proyecto_id
        else:
            usuario_obj.proyecto = None

        permiso_fields = [
            'cat_ver', 'cat_crear', 'cat_editar', 'cat_eliminar',
            'prod_ver', 'prod_crear', 'prod_editar', 'prod_eliminar',
            'prov_ver', 'prov_crear', 'prov_editar', 'prov_eliminar',
            'ord_ver', 'ord_crear', 'ord_editar', 'ord_eliminar',
            'ing_ver', 'ing_crear', 'ing_editar', 'ing_eliminar',
            'sal_ver', 'sal_crear', 'sal_editar', 'sal_eliminar',
            'pro_ver', 'pro_crear', 'pro_editar', 'pro_eliminar',
            'trab_ver', 'trab_crear', 'trab_editar', 'trab_eliminar',
            'tra_ver', 'tra_crear', 'tra_recibir', 'tra_eliminar',
            'herr_ver', 'herr_crear', 'herr_editar', 'herr_eliminar',
            'mant_herr_ver', 'mant_herr_crear', 'mant_herr_editar', 'mant_herr_eliminar',
            'maq_ver', 'maq_crear', 'maq_editar', 'maq_eliminar',
            'mant_maq_ver', 'mant_maq_crear', 'mant_maq_editar', 'mant_maq_eliminar',
            'gdi_ver', 'gdi_crear', 'gdi_editar', 'gdi_eliminar',
            'gasto_ver', 'gasto_crear', 'gasto_editar', 'gasto_eliminar',
        ]

        for field_name in permiso_fields:
            setattr(permiso_obj, field_name, field_name in request.POST)

        usuario_obj.save()
        usuario_obj.proyectos_asignados.set(proyectos_asignados_ids)
        permiso_obj.save()

        if usuario_obj.pk == request.user.pk:
            request.session.pop('_user_perms_cache', None)

        messages.success(request, f'Permisos de {usuario_obj.username} actualizados correctamente.')
        return redirect('usuarios_list')

    return render(request, 'inventory/usuarios_permisos.html', {
        'u': usuario_obj,
        'p': permiso_obj,
        'modulos': modulos,
        'proyectos': Proyecto.objects.all(),
        'proyectos_asignados_ids': list(usuario_obj.proyectos_asignados.values_list('pk', flat=True)),
    })

@login_required
@permission_required('inventory.add_usuario', raise_exception=True)
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    trabajador = Trabajador.objects.create(
                        nombre=form.cleaned_data['nombre'],
                        apellido=form.cleaned_data['apellido'],
                        correo=form.cleaned_data['correo'],
                        cargo=form.cleaned_data.get('cargo', 'OTRO'),
                        sueldo=form.cleaned_data.get('sueldo') or 0,
                    )
                    usuario = Usuario.objects.create_user(
                        username=form.cleaned_data['nombreUsu'],
                        password=form.cleaned_data['password'],
                        trabajador=trabajador,
                        es_admin=form.cleaned_data['es_admin'],
                        proyecto=form.cleaned_data['proyecto'],
                        must_change_password=True,
                    )
                    messages.success(request, f'Usuario {usuario.username} creado. Al primer ingreso deberá cambiar su contraseña.')
                    return redirect('usuarios_list')
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
    else:
        form = UsuarioRegistroForm()
    
    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': 'Crear Nuevo Usuario',
        'url_volver': reverse_lazy('usuarios_list')
    })

@login_required
@permission_required('inventory.change_usuario', raise_exception=True)
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    trabajador = usuario.trabajador

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, usuario_id=usuario.pk, trabajador_id=trabajador.pk if trabajador else None)
        if form.is_valid():
            try:
                with transaction.atomic():
                    if trabajador:
                        trabajador.nombre = form.cleaned_data['nombre']
                        trabajador.apellido = form.cleaned_data['apellido']
                        trabajador.correo = form.cleaned_data['correo']
                        trabajador.cargo = form.cleaned_data.get('cargo', trabajador.cargo)
                        trabajador.sueldo = form.cleaned_data.get('sueldo') or trabajador.sueldo
                        trabajador.activo = form.cleaned_data.get('is_active', True)
                        trabajador.save()

                    usuario.username = form.cleaned_data['nombreUsu']
                    usuario.is_active = form.cleaned_data.get('is_active', True)
                    usuario.save()
                    messages.success(request, f'Usuario {usuario.username} actualizado con éxito.')
                    return redirect('usuarios_list')
            except Exception as e:
                messages.error(request, f'Error al editar usuario: {str(e)}')
    else:
        initial_data = {
            'nombreUsu': usuario.username,
            'is_active': usuario.is_active,
        }
        if trabajador:
            initial_data.update({
                'nombre': trabajador.nombre,
                'apellido': trabajador.apellido,
                'correo': trabajador.correo,
                'cargo': trabajador.cargo,
                'sueldo': trabajador.sueldo,
            })
        form = UsuarioEditarForm(initial=initial_data, usuario_id=usuario.pk, trabajador_id=trabajador.pk if trabajador else None)

    return render(request, 'inventory/form.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario.username}',
        'url_volver': reverse_lazy('usuarios_list')
    })

@login_required
@permission_required('inventory.change_empresa', raise_exception=True)
def empresa_configuracion(request):
    empresa, _ = Empresa.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos de la empresa actualizados correctamente.')
            return redirect('empresa_configuracion')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'inventory/empresa_form.html', {
        'form': form,
        'titulo': 'Configuración de la Empresa',
        'url_volver': reverse_lazy('index')
    })

@login_required
@permission_required('inventory.change_usuario', raise_exception=True)
def cambiar_password(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        nueva_pass = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')

        if nueva_pass and nueva_pass == confirm_pass:
            usuario_obj.set_password(nueva_pass)
            usuario_obj.must_change_password = False
            usuario_obj.save()

            if request.user.pk == usuario_obj.pk:
                logout(request)

            messages.success(request, 'Contraseña modificada correctamente.')
            return redirect('login')
        else:
            messages.error(request, 'Las contraseñas no coinciden o están vacías.')

    return render(request, 'inventory/usuarios_password.html', {'u': usuario_obj})


@login_required
def primer_ingreso_password(request):
    if not request.user.must_change_password:
        messages.info(request, 'Para cambiar tu contraseña, solicítalo al administrador.')
        return redirect('index')

    if request.method == 'POST':
        nueva_pass = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')

        if nueva_pass and nueva_pass == confirm_pass:
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            try:
                validate_password(nueva_pass, request.user)
                request.user.set_password(nueva_pass)
                request.user.must_change_password = False
                request.user.save()
                messages.success(request, 'Contraseña actualizada. Por favor inicia sesión nuevamente.')
                logout(request)
                return redirect('login')
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)
        else:
            messages.error(request, 'Las contraseñas no coinciden o están vacías.')

    return render(request, 'inventory/primer_ingreso_password.html')

class TrabajadorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_trabajador'
    model = Trabajador
    template_name = 'inventory/trabajador_list.html'
    context_object_name = 'trabajadores'
    paginate_by = 25

    def get_queryset(self):
        qs = Trabajador.all_objects.order_by('nombre', 'apellido')
        q = self.request.GET.get('q')
        estado = self.request.GET.get('estado')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(correo__icontains=q) | Q(cargo__icontains=q))
        if estado == 'activo':
            qs = qs.filter(activo=True)
        elif estado == 'inactivo':
            qs = qs.filter(activo=False)
        return qs

class TrabajadorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_trabajador'
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('trabajadores_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Trabajador'
        context['url_volver'] = reverse_lazy('trabajadores_list')
        return context

class TrabajadorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_trabajador'
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('trabajadores_list')

    def get_queryset(self):
        return Trabajador.all_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Trabajador'
        context['url_volver'] = reverse_lazy('trabajadores_list')
        return context

class ModuloTorreListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_salida'
    model = ModuloTorre
    template_name = 'inventory/modulo_torre_list.html'
    context_object_name = 'modulos_torre'
    paginate_by = 25

    def get_queryset(self):
        qs = ModuloTorre.all_objects.all().select_related('proyecto').order_by('nombre')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q) | Q(proyecto__nombre__icontains=q))
        return qs

class ModuloTorreCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_salida'
    model = ModuloTorre
    form_class = ModuloTorreForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('modulos_torre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Modulo Torre'
        context['url_volver'] = reverse_lazy('modulos_torre')
        return context

class ModuloTorreUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_salida'
    model = ModuloTorre
    form_class = ModuloTorreForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('modulos_torre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Modulo Torre'
        context['url_volver'] = reverse_lazy('modulos_torre')
        return context

class PartidaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_proyecto'
    model = Partida
    template_name = 'inventory/partida_list.html'
    context_object_name = 'partidas'
    paginate_by = 25

    def get_queryset(self):
        qs = Partida.all_objects.all().select_related('proyecto').order_by('proyecto__nombre', 'nombre')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(proyecto__nombre__icontains=q))
        return qs

class PartidaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_proyecto'
    model = Partida
    form_class = PartidaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('partidas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Partida'
        context['url_volver'] = reverse_lazy('partidas')
        return context

class PartidaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_proyecto'
    model = Partida
    form_class = PartidaForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('partidas')

    def get_queryset(self):
        return Partida.all_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Partida'
        context['url_volver'] = reverse_lazy('partidas')
        return context

class ProyectoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'inventory.view_proyecto'
    model = Proyecto
    template_name = 'inventory/proyecto_list.html'
    context_object_name = 'proyectos'
    paginate_by = 25

class ProyectoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'inventory.add_proyecto'
    model = Proyecto
    form_class = ProyectoForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('proyectos')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Proyecto'
        context['url_volver'] = reverse_lazy('proyectos')
        return context

class ProyectoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'inventory.change_proyecto'
    model = Proyecto
    form_class = ProyectoForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('proyectos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Proyecto'
        context['url_volver'] = reverse_lazy('proyectos')
        return context

@login_required
def get_proyectos_usuario(request):
    proyectos = []
    if request.user.proyecto:
        proyectos.append({'id': request.user.proyecto.pk, 'nombre': request.user.proyecto.nombre})
    for p in request.user.proyectos_asignados.all():
        if p.pk != (request.user.proyecto.pk if request.user.proyecto else None):
            proyectos.append({'id': p.pk, 'nombre': p.nombre})
    return JsonResponse({'proyectos': proyectos})
