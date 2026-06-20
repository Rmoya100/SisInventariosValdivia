from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import (
    UnidadMedida, Producto, Proveedor, OrdenCompra, Categoria, Salida, Ingreso,
    DetalleCompra, DetalleIngreso, DetalleSalida, Trabajador, Usuario,
    Proyecto, Empresa, Transferencia, DetalleTransferencia, Bodega,
    Herramienta, Maquinaria, MantenimientoHerramienta, MantenimientoMaquinaria,
    TransferenciaActivo, ModuloTorre, Gasto, Fase, StockProyecto, Partida
)

class UppercaseMixin:
    def clean(self):
        cleaned_data = super().clean()
        for name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[name] = value.upper()
        return cleaned_data

class UsuarioRegistroForm(UppercaseMixin, forms.Form):
    nombre    = forms.CharField(label="Nombre",            widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido  = forms.CharField(label="Apellido",          widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo    = forms.EmailField(label="Correo",           widget=forms.EmailInput(attrs={'class': 'form-control'}))
    cargo     = forms.ChoiceField(label="Cargo", choices=Trabajador.CARGO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    sueldo    = forms.DecimalField(label="Sueldo", min_value=0, max_digits=12, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}))
    nombreUsu = forms.CharField(label="Nombre de Usuario", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password  = forms.CharField(label="Contraseña",        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    es_admin  = forms.BooleanField(label="Es Administrador", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    proyecto  = forms.ModelChoiceField(label="Proyecto Asignado", queryset=Proyecto.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean_nombreUsu(self):
        username = self.cleaned_data.get('nombreUsu')
        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre', '')
        apellido = cleaned_data.get('apellido', '')
        correo = cleaned_data.get('correo', '')

        if nombre and apellido:
            if Trabajador.all_objects.filter(nombre__iexact=nombre, apellido__iexact=apellido).exists():
                raise forms.ValidationError(
                    f'Ya existe un trabajador con el nombre "{nombre} {apellido}". '
                    'Si fue desactivado, puede reactivarlo desde la lista de trabajadores.'
                )

        if correo:
            if Trabajador.all_objects.filter(correo__iexact=correo).exists():
                raise forms.ValidationError(
                    f'El correo "{correo}" ya está registrado en otro trabajador.'
                )

        return cleaned_data

class UsuarioEditarForm(UppercaseMixin, forms.Form):
    nombre    = forms.CharField(label="Nombre",            widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido  = forms.CharField(label="Apellido",          widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo    = forms.EmailField(label="Correo",           widget=forms.EmailInput(attrs={'class': 'form-control'}))
    cargo     = forms.ChoiceField(label="Cargo", choices=Trabajador.CARGO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    sueldo    = forms.DecimalField(label="Sueldo", min_value=0, max_digits=12, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}))
    nombreUsu = forms.CharField(label="Nombre de Usuario", widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(
        label="Estado (activo)", required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Desmarcar para desactivar el acceso de este usuario al sistema."
    )

    def __init__(self, *args, **kwargs):
        self.usuario_id = kwargs.pop('usuario_id', None)
        self.trabajador_id = kwargs.pop('trabajador_id', None)
        super().__init__(*args, **kwargs)

    def clean_nombreUsu(self):
        username = self.cleaned_data.get('nombreUsu')
        qs = Usuario.objects.filter(username__iexact=username)
        if self.usuario_id:
            qs = qs.exclude(pk=self.usuario_id)
        if qs.exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre', '')
        apellido = cleaned_data.get('apellido', '')
        correo = cleaned_data.get('correo', '')

        if nombre and apellido:
            qs = Trabajador.all_objects.filter(nombre__iexact=nombre, apellido__iexact=apellido)
            if self.trabajador_id:
                qs = qs.exclude(pk=self.trabajador_id)
            if qs.exists():
                raise forms.ValidationError(
                    f'Ya existe otro trabajador con el nombre "{nombre} {apellido}".'
                )

        if correo:
            qs = Trabajador.all_objects.filter(correo__iexact=correo)
            if self.trabajador_id:
                qs = qs.exclude(pk=self.trabajador_id)
            if qs.exists():
                raise forms.ValidationError(
                    f'El correo "{correo}" ya está registrado en otro trabajador.'
                )

        return cleaned_data

class ProyectoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BodegaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Bodega
        fields = ['proyecto', 'nombre', 'ubicacion', 'descripcion']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PartidaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Partida
        fields = ['proyecto', 'item_serviu', 'nombre', 'descripcion', 'activo']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'item_serviu': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyecto.all_objects.all().order_by('nombre')

class CategoriaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UnidadMedidaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = ['nombre', 'abreviatura']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: KILOGRAMO'}),
            'abreviatura': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: KG'}),
        }
        labels = {
            'nombre': 'Nombre',
            'abreviatura': 'Abreviatura',
        }


class ProductoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'unidad_medida', 'nombre', 'stock_inicial']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'unidad_medida': 'Unidad de Medida',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unidad_medida'].queryset = UnidadMedida.objects.filter(activo=True).order_by('nombre')
        self.fields['unidad_medida'].empty_label = '— Seleccionar unidad —'


class ProductoCreateForm(ProductoForm):
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.none(),
        required=False,
        label='Proyecto destino (stock inicial)',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Sin stock inicial —',
        help_text='Requerido si el stock inicial es mayor a 0',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyecto.objects.filter(activo=True).order_by('nombre')

    def clean(self):
        cleaned_data = super().clean()
        stock = cleaned_data.get('stock_inicial') or 0
        proyecto = cleaned_data.get('proyecto')
        if stock > 0 and not proyecto:
            self.add_error('proyecto', 'Debes seleccionar un proyecto destino cuando el stock inicial es mayor a 0.')
        return cleaned_data


class ProductoEditForm(ProductoForm):
    bodega = forms.ModelChoiceField(
        queryset=Bodega.objects.none(),
        required=False,
        label='Asignar stock libre a bodega',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— No asignar —',
        help_text='Asigna el stock sin proyecto al proyecto de la bodega seleccionada',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = (
            Bodega.objects.filter(activo=True, proyecto__isnull=False)
            .select_related('proyecto')
            .order_by('proyecto__nombre', 'nombre')
        )
        self.fields['bodega'].queryset = qs
        self.fields['bodega'].widget.choices = (
            [('', '— No asignar —')]
            + [(b.pk, f"[{b.proyecto.nombre}]  →  {b.nombre}") for b in qs]
        )

    def clean(self):
        cleaned_data = super().clean()
        bodega = cleaned_data.get('bodega')
        if bodega and self.instance.pk:
            proyecto = bodega.proyecto
            if StockProyecto.objects.filter(producto=self.instance, proyecto=proyecto).exists():
                self.add_error(
                    'bodega',
                    f'Este producto ya tiene stock asignado al proyecto "{proyecto.nombre}".',
                )
        return cleaned_data


class ProveedorForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'contacto', 'cel_contacto', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'cel_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EmpresaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'rut', 'direccion', 'telefono', 'giro', 'logo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

def _es_admin(user) -> bool:
    """Determina si el usuario es administrador usando el mismo criterio que el resto del sistema."""
    return bool(
        getattr(user, 'es_admin', False)
        or getattr(user, 'is_superuser', False)
        or getattr(user, 'is_staff', False)
    )


class BodegaChoiceField(forms.ModelChoiceField):
    """Muestra cada bodega como '[Proyecto] → Bodega' para que el admin sepa a qué proyecto pertenece."""
    def label_from_instance(self, obj):
        if obj.proyecto:
            return f"[{obj.proyecto.nombre}]  →  {obj.nombre}"
        return obj.nombre


class OrdenCompraForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['numCompra', 'proveedor', 'bodega', 'fecha_compra', 'forma_de_pago']
        widgets = {
            'numCompra':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: OC-1024'}),
            'proveedor':    forms.Select(attrs={'class': 'form-select'}),
            'bodega':       forms.Select(attrs={'class': 'form-select'}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'forma_de_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'list': 'formas-pago-list',
                'placeholder': 'Seleccione o escriba forma de pago...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if _es_admin(self.user):
            # Admin/staff puede asignar a cualquier proyecto activo
            self.fields['bodega'] = BodegaChoiceField(
                queryset=Bodega.objects.filter(activo=True, proyecto__isnull=False)
                    .select_related('proyecto').order_by('proyecto__nombre', 'nombre'),
                widget=forms.Select(attrs={'class': 'form-select'}),
                label='Bodega destino',
                empty_label='— Seleccionar Bodega —',
                required=not bool(self.user and self.user.get_proyecto_movimiento()),
            )
        else:
            # Usuario normal: proyecto auto-derivado de su perfil en la vista
            self.fields.pop('bodega', None)

        if not self.instance.pk:
            import datetime
            self.fields['fecha_compra'].initial = datetime.date.today()

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and self.instance.estado == 'RECEPCION OK':
            raise forms.ValidationError('No se puede modificar una orden de compra con recepción completa.')
        return cleaned_data

class SalidaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Salida
        fields = ['fecha', 'modulo_torre', 'partida', 'solicitante']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'modulo_torre': forms.Select(attrs={'class': 'form-select', 'id': 'id_modulo_torre'}),
            'partida': forms.Select(attrs={'class': 'form-select', 'id': 'id_partida_salida'}),
            'solicitante': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        cargos_solicitantes = [
            'JEFE DE TERRENO',
            'ADMINISTRADOR DE OBRA',
            'ENCARGADO DE RECURSOS',
        ]
        self.fields['solicitante'].queryset = Trabajador.objects.filter(
            activo=True,
            cargo__in=cargos_solicitantes,
        ).order_by('nombre', 'apellido')

        proyecto = None
        if self.user and not _es_admin(self.user):
            proyecto = self.user.get_proyecto_movimiento()

        if proyecto:
            self.fields['modulo_torre'].queryset = ModuloTorre.objects.filter(
                activo=True, proyecto=proyecto, proyecto__activo=True
            ).order_by('nombre')
            self.fields['partida'].queryset = Partida.objects.filter(
                activo=True, proyecto=proyecto, proyecto__activo=True
            ).order_by('nombre')
        else:
            self.fields['modulo_torre'].queryset = ModuloTorre.objects.filter(activo=True).order_by('nombre')
            self.fields['partida'].queryset = Partida.objects.filter(activo=True).order_by('nombre')

        if _es_admin(self.user):
            self.fields['bodega'] = BodegaChoiceField(
                queryset=Bodega.objects.filter(activo=True, proyecto__isnull=False)
                    .select_related('proyecto').order_by('proyecto__nombre'),
                widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_bodega_salida'}),
                label='Bodega origen',
                empty_label='— Seleccionar Bodega —',
                required=not bool(self.user and self.user.get_proyecto_movimiento()),
            )

class IngresoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['fecha', 'orden_compra', 'tipo_documento', 'num_documento']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'orden_compra': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'num_documento': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orden_compra'].queryset = OrdenCompra.objects.filter(
            estado__in=['PENDIENTE', 'RECEPCION PARCIAL']
        )


class DetalleCompraForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ['producto', 'cantidad', 'precio']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DetalleIngresoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = DetalleIngreso
        fields = ['producto', 'cantidad', 'precio']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DetalleSalidaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = DetalleSalida
        fields = ['producto', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TransferenciaForm(UppercaseMixin, forms.ModelForm):
    # Admin/staff: elige bodega de origen → proyecto se deriva de ella
    bodega_origen = BodegaChoiceField(
        queryset=Bodega.objects.none(),
        required=False,
        label='Bodega de Origen',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_bodega_origen_gdi'}),
        empty_label='— Seleccionar Bodega de Origen —',
    )

    # Usuarios normales con múltiples proyectos
    proyecto_origen = forms.ModelChoiceField(
        queryset=Proyecto.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Obra de Origen'
    )

    class Meta:
        model = Transferencia
        fields = ['proyecto_origen', 'proyecto_destino', 'observacion']
        widgets = {
            'proyecto_destino': forms.Select(attrs={'class': 'form-select'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user is None:
            self.fields.pop('proyecto_origen', None)
            self.fields.pop('bodega_origen', None)
            return

        if _es_admin(self.user):
            # Admin/staff elige bodega; el proyecto se deriva de ella en clean()
            self.fields['bodega_origen'].queryset = Bodega.objects.filter(
                activo=True, proyecto__isnull=False
            ).select_related('proyecto').order_by('proyecto__nombre', 'nombre')
            self.fields['bodega_origen'].required = True
            self.fields.pop('proyecto_origen', None)
            # Reordenar: bodega_origen primero
            self.fields = {
                'bodega_origen':    self.fields['bodega_origen'],
                'proyecto_destino': self.fields['proyecto_destino'],
                'observacion':      self.fields['observacion'],
            }
            return

        # Usuario normal: sin campo bodega_origen
        self.fields.pop('bodega_origen', None)

        available_origins = Proyecto.objects.none()
        if self.user.proyecto:
            available_origins = available_origins | Proyecto.objects.filter(pk=self.user.proyecto.pk)
        available_origins = available_origins | self.user.proyectos_asignados.all()
        available_origins = available_origins.distinct().order_by('nombre')

        if available_origins.count() > 1:
            self.fields['proyecto_origen'].queryset = available_origins
            self.fields['proyecto_origen'].required = True
        else:
            self.fields.pop('proyecto_origen', None)

    def clean(self):
        cleaned_data = super().clean()
        proyecto_destino = cleaned_data.get('proyecto_destino')

        if _es_admin(self.user):
            bodega = cleaned_data.get('bodega_origen')
            if not bodega:
                raise forms.ValidationError('Debes seleccionar una bodega de origen.')
            if not bodega.proyecto:
                raise forms.ValidationError('La bodega seleccionada no tiene un proyecto asignado.')
            proyecto_origen = bodega.proyecto
        else:
            proyecto_origen = cleaned_data.get('proyecto_origen')
            if 'proyecto_origen' not in self.fields:
                if self.user and self.user.proyecto:
                    proyecto_origen = self.user.proyecto
                elif self.user and self.user.proyectos_asignados.count() == 1:
                    proyecto_origen = self.user.proyectos_asignados.first()
            if proyecto_origen is None:
                raise forms.ValidationError('Debes seleccionar una obra de origen para despachar.')

        if proyecto_destino and proyecto_origen == proyecto_destino:
            raise forms.ValidationError('La obra de origen y destino no pueden ser la misma.')

        cleaned_data['proyecto_origen'] = proyecto_origen
        return cleaned_data

class DetalleTransferenciaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = DetalleTransferencia
        fields = ['producto', 'cantidad_enviada']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_enviada': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DetalleTransferenciaRecibirForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = DetalleTransferencia
        fields = ['idDetalle', 'cantidad_recibida']
        widgets = {
            'idDetalle': forms.HiddenInput(),
            'cantidad_recibida': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TrabajadorForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'apellido', 'correo', 'cargo', 'sueldo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'sueldo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'activo': 'Estado (activo)',
        }

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre', '')
        apellido = cleaned_data.get('apellido', '')
        correo = cleaned_data.get('correo', '')
        pk = self.instance.pk

        if nombre and apellido:
            qs_nombre = Trabajador.all_objects.filter(
                nombre__iexact=nombre, apellido__iexact=apellido
            )
            if pk:
                qs_nombre = qs_nombre.exclude(pk=pk)
            if qs_nombre.exists():
                raise forms.ValidationError(
                    f'Ya existe un trabajador con el nombre "{nombre} {apellido}". '
                    'Si fue desactivado, puede reactivarlo desde la lista.'
                )

        if correo:
            qs_correo = Trabajador.all_objects.filter(correo__iexact=correo)
            if pk:
                qs_correo = qs_correo.exclude(pk=pk)
            if qs_correo.exists():
                raise forms.ValidationError(
                    f'El correo "{correo}" ya está registrado en otro trabajador.'
                )

        return cleaned_data

class ModuloTorreForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = ModuloTorre
        fields = ['proyecto', 'nombre', 'descripcion', 'activo']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyecto.all_objects.all().order_by('nombre')

class HerramientaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = ['nomHerramienta', 'codigo', 'marca', 'estado', 'observaciones', 'bodega_actual']
        widgets = {
            'nomHerramienta': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'bodega_actual': forms.Select(attrs={'class': 'form-select'}),
        }

class MaquinariaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Maquinaria
        fields = ['tipo_maquina', 'marca', 'modelo', 'patente_o_codigo', 'tipo_control', 'valor_actual', 'bodega_actual']
        widgets = {
            'tipo_maquina': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'patente_o_codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_control': forms.Select(attrs={'class': 'form-select'}),
            'valor_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'bodega_actual': forms.Select(attrs={'class': 'form-select'}),
        }

class MantenimientoHerramientaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = MantenimientoHerramienta
        fields = ['herramienta', 'proveedor', 'observaciones']
        widgets = {
            'herramienta': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RecepcionHerramientaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = MantenimientoHerramienta
        fields = ['fecha_recepcion', 'observaciones']
        widgets = {
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class MantenimientoMaquinariaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = MantenimientoMaquinaria
        fields = ['maquinaria', 'proveedor', 'valor_mantenimiento', 'observaciones']
        widgets = {
            'maquinaria': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'valor_mantenimiento': forms.NumberInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RecepcionMaquinariaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = MantenimientoMaquinaria
        fields = ['fecha_recepcion', 'observaciones']
        widgets = {
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ActualizarLecturaForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Maquinaria
        fields = ['valor_actual']
        widgets = {
            'valor_actual': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TransferenciaActivoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = TransferenciaActivo
        fields = ['bodega_origen', 'bodega_destino', 'tipo_activo', 'herramienta', 'maquinaria', 'observacion']
        widgets = {
            'bodega_origen': forms.Select(attrs={'class': 'form-select'}),
            'bodega_destino': forms.Select(attrs={'class': 'form-select'}),
            'tipo_activo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_activo'}),
            'herramienta': forms.Select(attrs={'class': 'form-select', 'id': 'id_herramienta_ta'}),
            'maquinaria': forms.Select(attrs={'class': 'form-select', 'id': 'id_maquinaria_ta'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_activo')
        herramienta = cleaned_data.get('herramienta')
        maquinaria = cleaned_data.get('maquinaria')
        origen = cleaned_data.get('bodega_origen')
        destino = cleaned_data.get('bodega_destino')

        if origen and destino and origen == destino:
            raise forms.ValidationError('La bodega de origen y destino no pueden ser la misma.')
        if tipo == 'HERRAMIENTA' and not herramienta:
            raise forms.ValidationError('Debes seleccionar una herramienta.')
        if tipo == 'MAQUINARIA' and not maquinaria:
            raise forms.ValidationError('Debes seleccionar una maquinaria.')
        return cleaned_data


class GastoForm(UppercaseMixin, forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['proyecto', 'tipo_documento', 'num_documento', 'concepto', 'fecha', 'monto', 'observaciones', 'archivo_respaldo']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'num_documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 001254'}),
            'concepto': forms.Select(attrs={'class': 'form-select', 'id': 'id_concepto'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo_respaldo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import datetime
        self.fields['proyecto'].queryset = Proyecto.objects.filter(activo=True).order_by('nombre')
        self.fields['proyecto'].required = True
        self.fields['proyecto'].empty_label = '— Seleccionar Proyecto —'
        self.fields['tipo_documento'].required = True
        self.fields['tipo_documento'].empty_label = '— Seleccionar tipo —'
        self.fields['num_documento'].required = True
        self.fields['archivo_respaldo'].required = False
        if not self.instance.pk:
            self.fields['fecha'].initial = datetime.date.today()

    def clean_archivo_respaldo(self):
        archivo = self.cleaned_data.get('archivo_respaldo')
        if archivo and hasattr(archivo, 'name'):
            ext = archivo.name.rsplit('.', 1)[-1].lower()
            if ext not in ('jpg', 'jpeg', 'png', 'webp', 'pdf'):
                raise forms.ValidationError('Solo se aceptan imágenes (JPG, PNG, WEBP) o archivos PDF.')
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede superar los 10 MB.')
        return archivo

class FaseForm(forms.ModelForm):
    class Meta:
        model = Fase
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False


DetalleCompraFormSet = forms.inlineformset_factory(
    OrdenCompra, DetalleCompra, form=DetalleCompraForm,
    extra=1, can_delete=True
)

DetalleIngresoFormSet = forms.inlineformset_factory(
    Ingreso, DetalleIngreso, form=DetalleIngresoForm,
    extra=0, can_delete=True
)

DetalleSalidaFormSet = forms.inlineformset_factory(
    Salida, DetalleSalida, form=DetalleSalidaForm,
    extra=1, can_delete=True
)

DetalleTransferenciaFormSet = forms.inlineformset_factory(
    Transferencia, DetalleTransferencia, form=DetalleTransferenciaForm,
    extra=1, can_delete=True
)

