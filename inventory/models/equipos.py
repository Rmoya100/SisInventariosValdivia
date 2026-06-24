from django.db import models
from .base import ActiveManager
from .core import Bodega
from .catalogo import Proveedor
from .personas import Usuario


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
    ESTADO_CHOICES = [
        ('EN TRANSITO', 'En Tránsito'),
        ('RECEPCION PARCIAL', 'Recepción Parcial'),
        ('RECEPCION OK', 'Recepción OK'),
    ]
    TIPO_ACTIVO_CHOICES = [('HERRAMIENTA', 'Herramienta'), ('MAQUINARIA', 'Maquinaria')]
    idTransferencia = models.AutoField(primary_key=True)
    bodega_origen = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='despachos_activos')
    bodega_destino = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='recepciones_activos')
    usuario_despacha = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='gdi_activos_despachados')
    fecha_despacho = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN TRANSITO')
    # Legacy fields kept for backward compat with old single-asset records
    tipo_activo = models.CharField(max_length=20, choices=TIPO_ACTIVO_CHOICES, null=True, blank=True)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, null=True, blank=True)
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.CASCADE, null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    usuario_recibe = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='gdi_activos_recibidos')
    fecha_recepcion = models.DateField(null=True, blank=True)
    observacion_recepcion = models.TextField(blank=True, null=True)

    def actualizar_estado(self):
        detalles = self.detalles_activos.all()
        if not detalles.exists():
            return
        total = detalles.count()
        recibidos = detalles.filter(recibido=True).count()
        if recibidos == 0:
            nuevo = 'EN TRANSITO'
        elif recibidos < total:
            nuevo = 'RECEPCION PARCIAL'
        else:
            nuevo = 'RECEPCION OK'
        if self.estado != nuevo:
            self.estado = nuevo
            self.save(update_fields=['estado'])

    def __str__(self):
        return f"GDI {self.idTransferencia}: {self.bodega_origen} -> {self.bodega_destino}"


class DetalleTransferenciaActivo(models.Model):
    TIPO_ACTIVO_CHOICES = [('HERRAMIENTA', 'Herramienta'), ('MAQUINARIA', 'Maquinaria')]
    transferencia = models.ForeignKey(TransferenciaActivo, on_delete=models.CASCADE, related_name='detalles_activos')
    tipo_activo = models.CharField(max_length=20, choices=TIPO_ACTIVO_CHOICES)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.SET_NULL, null=True, blank=True, related_name='detalles_transferencia')
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.SET_NULL, null=True, blank=True, related_name='detalles_transferencia')
    recibido = models.BooleanField(default=False)

    def get_activo_display(self):
        if self.tipo_activo == 'HERRAMIENTA' and self.herramienta:
            return self.herramienta.nomHerramienta
        if self.tipo_activo == 'MAQUINARIA' and self.maquinaria:
            return str(self.maquinaria)
        return '—'

    def get_codigo_display(self):
        if self.tipo_activo == 'HERRAMIENTA' and self.herramienta:
            return self.herramienta.codigo
        if self.tipo_activo == 'MAQUINARIA' and self.maquinaria:
            return self.maquinaria.patente_o_codigo
        return '—'

    def __str__(self):
        return f"Detalle GDI {self.transferencia_id}: {self.get_activo_display()}"
