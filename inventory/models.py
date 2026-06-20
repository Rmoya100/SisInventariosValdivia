import threading
from django.db import models
from django.db.models import Sum, F
from django.contrib.auth.models import AbstractUser

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)

class Proveedor(models.Model):
    codProveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50)
    contacto = models.CharField(max_length=255)
    cel_contacto = models.CharField(max_length=50)
    correo = models.EmailField()
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    idCategoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

class Proyecto(models.Model):
    idProyecto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

class Empresa(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    rut = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    giro = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='empresa_logos/', blank=True, null=True)

    def __str__(self):
        return self.nombre or 'Empresa'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class Bodega(models.Model):
    idBodega = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True, related_name='bodegas')
    nombre = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    cod_prod = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    stock_inicial = models.IntegerField(default=0)
    stock_actual = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def actualizar_stock(self):
        ingresos = self.detalleingreso_set.aggregate(total=Sum('cantidad'))['total'] or 0
        salidas = self.detallesalida_set.aggregate(total=Sum('cantidad'))['total'] or 0
        nuevo_stock = self.stock_inicial + ingresos - salidas
        if self.stock_actual != nuevo_stock:
            self.stock_actual = nuevo_stock
            Producto.all_objects.filter(pk=self.pk).update(stock_actual=nuevo_stock)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            Producto.all_objects.filter(pk=self.pk).update(stock_actual=self.stock_inicial)

    def __str__(self):
        return self.nombre

class StockProyecto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stocks_proyecto')
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='inventario')
    cantidad = models.IntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'proyecto')

    def __str__(self):
        return f"{self.producto.nombre} en {self.proyecto.nombre}: {self.cantidad}"

class OrdenCompra(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('RECEPCION PARCIAL', 'Recepción Parcial'),
        ('RECEPCION OK', 'Recepción OK'),
    ]
    idCompra = models.AutoField(primary_key=True)
    numCompra = models.CharField(max_length=100, unique=True, verbose_name="Número de Orden")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_compra')
    fecha_compra = models.DateField()
    forma_de_pago = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    def actualizar_estado(self):
        total_pedido = self.detalles.aggregate(total=Sum('cantidad'))['total'] or 0
        total_recibido = DetalleIngreso.objects.filter(ingreso__orden_compra=self).aggregate(total=Sum('cantidad'))['total'] or 0
        
        if total_recibido == 0:
            nuevo_estado = 'PENDIENTE'
        elif total_recibido < total_pedido:
            nuevo_estado = 'RECEPCION PARCIAL'
        else:
            nuevo_estado = 'RECEPCION OK'
            
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            OrdenCompra.objects.filter(pk=self.pk).update(estado=nuevo_estado)

    def __str__(self):
        return f"Orden {self.numCompra} - {self.proveedor} ({self.estado})"

class DetalleCompra(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle {self.idDetalle} - Orden {self.orden_compra.numCompra}"

class Ingreso(models.Model):
    numIngreso = models.AutoField(primary_key=True)
    fecha = models.DateField()
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingresos')
    tipo_documento = models.CharField(max_length=100)
    num_documento = models.CharField(max_length=100)

    def __str__(self):
        return f"Ingreso {self.numIngreso}"

class DetalleIngreso(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    ingreso = models.ForeignKey(Ingreso, on_delete=models.CASCADE, related_name='detalles')
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if self.producto:
            if is_new:
                Producto.all_objects.filter(pk=self.producto.pk).update(stock_actual=F('stock_actual') + self.cantidad)
            else:
                self.producto.actualizar_stock()
            
            proyecto = self.ingreso.proyecto
            if proyecto:
                stock_proj, _ = StockProyecto.objects.get_or_create(producto=self.producto, proyecto=proyecto)
                if is_new:
                    StockProyecto.objects.filter(pk=stock_proj.pk).update(cantidad=F('cantidad') + self.cantidad)
                else:
                    total_ing = DetalleIngreso.objects.filter(producto=self.producto, ingreso__proyecto=proyecto).aggregate(total=Sum('cantidad'))['total'] or 0
                    total_sal = DetalleSalida.objects.filter(producto=self.producto, salida__proyecto=proyecto).aggregate(total=Sum('cantidad'))['total'] or 0
                    StockProyecto.objects.filter(pk=stock_proj.pk).update(cantidad=total_ing - total_sal)
                    
        if self.ingreso and self.ingreso.orden_compra:
            self.ingreso.orden_compra.actualizar_estado()

    def delete(self, *args, **kwargs):
        prod = self.producto
        cant = self.cantidad
        ing = self.ingreso
        super().delete(*args, **kwargs)
        
        if prod:
            Producto.all_objects.filter(pk=prod.pk).update(stock_actual=F('stock_actual') - cant)
            if ing.proyecto:
                StockProyecto.objects.filter(producto=prod, proyecto=ing.proyecto).update(cantidad=F('cantidad') - cant)
        if ing and ing.orden_compra:
            ing.orden_compra.actualizar_estado()

    def __str__(self):
        return f"Detalle Ingreso {self.idDetalle}"

class Salida(models.Model):
    numSalida = models.AutoField(primary_key=True)
    fecha = models.DateField()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas')
    modulo_torre = models.ForeignKey('ModuloTorre', on_delete=models.PROTECT, null=True, blank=True, related_name='salidas')
    solicitante = models.ForeignKey('Trabajador', on_delete=models.PROTECT, null=True, blank=True, related_name='salidas_solicitadas')

    def __str__(self):
        return f"Salida {self.numSalida}"

class DetalleSalida(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    salida = models.ForeignKey(Salida, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if self.producto:
            if is_new:
                Producto.all_objects.filter(pk=self.producto.pk).update(stock_actual=F('stock_actual') - self.cantidad)
            else:
                self.producto.actualizar_stock()
                
            proyecto = self.salida.proyecto
            if proyecto:
                stock_proj, _ = StockProyecto.objects.get_or_create(producto=self.producto, proyecto=proyecto)
                if is_new:
                    StockProyecto.objects.filter(pk=stock_proj.pk).update(cantidad=F('cantidad') - self.cantidad)
                else:
                    total_ing = DetalleIngreso.objects.filter(producto=self.producto, ingreso__proyecto=proyecto).aggregate(total=Sum('cantidad'))['total'] or 0
                    total_sal = DetalleSalida.objects.filter(producto=self.producto, salida__proyecto=proyecto).aggregate(total=Sum('cantidad'))['total'] or 0
                    StockProyecto.objects.filter(pk=stock_proj.pk).update(cantidad=total_ing - total_sal)

    def delete(self, *args, **kwargs):
        prod = self.producto
        cant = self.cantidad
        sal = self.salida
        super().delete(*args, **kwargs)
        if prod:
            Producto.all_objects.filter(pk=prod.pk).update(stock_actual=F('stock_actual') + cant)
            if sal.proyecto:
                StockProyecto.objects.filter(producto=prod, proyecto=sal.proyecto).update(cantidad=F('cantidad') + cant)

    def __str__(self):
        return f"Detalle Salida {self.idDetalle}"

class Transferencia(models.Model):
    ESTADO_CHOICES = [
        ('EN TRANSITO', 'En Tránsito'),
        ('RECEPCION PARCIAL', 'Recepción Parcial'),
        ('RECEPCION OK', 'Recepción OK'),
    ]
    idTransferencia = models.AutoField(primary_key=True)
    proyecto_origen = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='despachos')
    proyecto_destino = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='recepciones')
    usuario_despacha = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='transferencias_enviadas')
    usuario_recibe = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_recibidas')
    fecha_despacho = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN TRANSITO')
    observacion = models.TextField(blank=True, null=True)

    def actualizar_estado(self):
        detalles = self.detalles.all()
        total_enviado = sum(d.cantidad_enviada for d in detalles)
        total_recibido = sum(d.cantidad_recibida for d in detalles)
        
        if total_recibido == 0:
            nuevo_estado = 'EN TRANSITO'
        elif total_recibido < total_enviado:
            nuevo_estado = 'RECEPCION PARCIAL'
        else:
            nuevo_estado = 'RECEPCION OK'
            
        if self.estado != nuevo_estado:
            self.estado = nuevo_estado
            Transferencia.objects.filter(pk=self.pk).update(estado=nuevo_estado)

    def __str__(self):
        return f"GDI {self.idTransferencia}: {self.proyecto_origen} -> {self.proyecto_destino}"

    def proximo_paso(self):
        if self.estado == 'RECEPCION OK': return 'GRI completa'
        if self.estado == 'RECEPCION PARCIAL': return 'Completar GRI'
        return 'Esperando GRI'

class DetalleTransferencia(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    transferencia = models.ForeignKey(Transferencia, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_enviada = models.IntegerField()
    cantidad_recibida = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.producto:
            origen = self.transferencia.proyecto_origen
            stock_orig, _ = StockProyecto.objects.get_or_create(producto=self.producto, proyecto=origen)
            StockProyecto.objects.filter(pk=stock_orig.pk).update(cantidad=F('cantidad') - self.cantidad_enviada)

    def delete(self, *args, **kwargs):
        prod = self.producto
        cant_env = self.cantidad_enviada
        cant_rec = self.cantidad_recibida
        transf = self.transferencia
        super().delete(*args, **kwargs)
        origen = transf.proyecto_origen
        StockProyecto.objects.filter(producto=prod, proyecto=origen).update(cantidad=F('cantidad') + cant_env)
        if cant_rec > 0:
            destino = transf.proyecto_destino
            StockProyecto.objects.filter(producto=prod, proyecto=destino).update(cantidad=F('cantidad') - cant_rec)

    def __str__(self):
        return f"GDI {self.transferencia.idTransferencia} - {self.producto.nombre}"

class Trabajador(models.Model):
    CARGO_CHOICES = [
        ('JEFE DE TERRENO', 'Jefe de Terreno'),
        ('ADMINISTRADOR DE OBRA', 'Administrador de obra'),
        ('ENCARGADO DE RECURSOS', 'Encargado de recursos'),
        ('BODEGUERO', 'Bodeguero'),
        ('OTRO', 'Otro'),
    ]
    codTrabajador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    correo = models.EmailField()
    cargo = models.CharField(max_length=100, choices=CARGO_CHOICES, default='OTRO')
    sueldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class ModuloTorre(models.Model):
    idModuloTorre = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    codUsuario = models.AutoField(primary_key=True)
    trabajador = models.OneToOneField(Trabajador, on_delete=models.CASCADE, null=True, blank=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.SET_NULL, null=True, blank=True, help_text="Proyecto por defecto")
    proyectos_asignados = models.ManyToManyField(Proyecto, related_name='usuarios_asignados', blank=True, help_text="Otros proyectos")
    es_admin = models.BooleanField(default=False)

    def get_proyecto_movimiento(self):
        if self.proyecto:
            return self.proyecto
        return self.proyectos_asignados.first()

    def get_bodega_movimiento(self):
        proyecto = self.get_proyecto_movimiento()
        if not proyecto:
            return None
        return proyecto.bodegas.filter(activo=True).order_by('pk').first()

    def __str__(self):
        return self.username


class Permiso(models.Model):
    idPermiso = models.AutoField(primary_key=True)

    # Categorías
    cat_ver = models.BooleanField(default=True)
    cat_crear = models.BooleanField(default=True)
    cat_editar = models.BooleanField(default=True)
    cat_eliminar = models.BooleanField(default=True)

    # Productos
    prod_ver = models.BooleanField(default=True)
    prod_crear = models.BooleanField(default=True)
    prod_editar = models.BooleanField(default=True)
    prod_eliminar = models.BooleanField(default=True)

    # Proveedores / Compras
    prov_ver = models.BooleanField(default=True)
    prov_crear = models.BooleanField(default=True)
    prov_editar = models.BooleanField(default=True)
    prov_eliminar = models.BooleanField(default=True)

    ord_ver = models.BooleanField(default=True)
    ord_crear = models.BooleanField(default=True)
    ord_editar = models.BooleanField(default=True)
    ord_eliminar = models.BooleanField(default=True)

    # Ingresos / Salidas
    ing_ver = models.BooleanField(default=True)
    ing_crear = models.BooleanField(default=True)
    ing_editar = models.BooleanField(default=True)
    ing_eliminar = models.BooleanField(default=True)

    sal_ver = models.BooleanField(default=True)
    sal_crear = models.BooleanField(default=True)
    sal_editar = models.BooleanField(default=True)
    sal_eliminar = models.BooleanField(default=True)

    # Proyectos
    pro_ver = models.BooleanField(default=True)
    pro_crear = models.BooleanField(default=True)
    pro_editar = models.BooleanField(default=True)
    pro_eliminar = models.BooleanField(default=True)

    # Trabajadores
    trab_ver = models.BooleanField(default=True)
    trab_crear = models.BooleanField(default=True)
    trab_editar = models.BooleanField(default=True)
    trab_eliminar = models.BooleanField(default=True)

    # Transferencias
    tra_ver = models.BooleanField(default=True)
    tra_crear = models.BooleanField(default=True)
    tra_recibir = models.BooleanField(default=True)
    tra_eliminar = models.BooleanField(default=True)

    # Equipos / Activos
    herr_ver = models.BooleanField(default=True)
    herr_crear = models.BooleanField(default=True)
    herr_editar = models.BooleanField(default=True)
    herr_eliminar = models.BooleanField(default=True)

    maq_ver = models.BooleanField(default=True)
    maq_crear = models.BooleanField(default=True)
    maq_editar = models.BooleanField(default=True)
    maq_eliminar = models.BooleanField(default=True)

    gdi_ver = models.BooleanField(default=True)
    gdi_crear = models.BooleanField(default=True)
    gdi_editar = models.BooleanField(default=True)
    gdi_eliminar = models.BooleanField(default=True)

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='permisos')

    def __str__(self):
        return f"Permisos de {self.usuario.username}"

class Herramienta(models.Model):
    ESTADO_CHOICES = [('BUENO', 'Bueno'), ('REGULAR', 'Regular'), ('MALO', 'Malo')]
    idHerramienta = models.AutoField(primary_key=True)
    nomHerramienta = models.CharField(max_length=255, verbose_name="Nombre Herramienta")
    codigo = models.CharField(max_length=100, unique=True)
    marca = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='BUENO')
    observaciones = models.TextField(blank=True, null=True)
    bodega_actual = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='herramientas')
    en_reparacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.nomHerramienta} ({self.codigo})"

class MantenimientoHerramienta(models.Model):
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='mantenimientos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_envio = models.DateField(auto_now_add=True)
    fecha_recepcion = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Mantenimiento: {self.herramienta.nomHerramienta} - {self.proveedor.nombre}"

class Maquinaria(models.Model):
    TIPO_CONTROL_CHOICES = [('HORAS', 'Horómetro'), ('KILOMETROS', 'Kilometraje')]
    TIPO_MAQUINA_CHOICES = [
        ('MANITOU', 'Manitou'), ('BOBCAT_S650', 'Bobcat S-650'), 
        ('BOBCAT_S770', 'Bobcat S770'), ('GRUA_HORQUILLA', 'Grúa Horquilla'), ('CAMION', 'Camión')
    ]
    idMaquinaria = models.AutoField(primary_key=True)
    tipo_maquina = models.CharField(max_length=50, choices=TIPO_MAQUINA_CHOICES)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    patente_o_codigo = models.CharField(max_length=100, unique=True)
    tipo_control = models.CharField(max_length=20, choices=TIPO_CONTROL_CHOICES)
    valor_actual = models.IntegerField(default=0)
    ultimo_mantenimiento = models.IntegerField(default=0)
    bodega_actual = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='maquinarias')
    en_reparacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def alerta_mantenimiento(self):
        if self.tipo_control == 'HORAS':
            return self.valor_actual >= (self.ultimo_mantenimiento + 200)
        elif self.tipo_control == 'KILOMETROS':
            return self.valor_actual >= (self.ultimo_mantenimiento + 9000)
        return False

    def __str__(self):
        return f"{self.get_tipo_maquina_display()} - {self.patente_o_codigo}"

class MantenimientoMaquinaria(models.Model):
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.CASCADE, related_name='mantenimientos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_envio = models.DateField(auto_now_add=True)
    fecha_recepcion = models.DateField(null=True, blank=True)
    valor_mantenimiento = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Mantenimiento: {self.maquinaria.patente_o_codigo} - {self.proveedor.nombre}"

class TransferenciaActivo(models.Model):
    ESTADO_CHOICES = [('EN TRANSITO', 'En Tránsito'), ('RECEPCION OK', 'Recepción OK')]
    TIPO_ACTIVO_CHOICES = [('HERRAMIENTA', 'Herramienta'), ('MAQUINARIA', 'Maquinaria')]
    idTransferencia = models.AutoField(primary_key=True)
    bodega_origen = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='despachos_activos')
    bodega_destino = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='recepciones_activos')
    usuario_despacha = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_despacho = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN TRANSITO')
    tipo_activo = models.CharField(max_length=20, choices=TIPO_ACTIVO_CHOICES)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, null=True, blank=True)
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.CASCADE, null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"GDI {self.idTransferencia}: {self.bodega_origen} -> {self.bodega_destino}"

class HistorialMovimiento(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100)
    detalles = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.fecha} - {self.usuario} - {self.accion}"
