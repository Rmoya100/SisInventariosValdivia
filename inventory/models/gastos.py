from django.db import models
from .base import ActiveManager
from .core import Proyecto
from .equipos import Maquinaria
from .personas import Trabajador, ModuloTorre


class Fase(models.Model):
    idFase = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Gasto(models.Model):
    CONCEPTO_CHOICES = [
        ('PETROLEO', 'Petroleo'),
        ('BENCINA', 'Bencina'),
        ('MANO_OBRA', 'Mano de obra'),
        ('SUELDOS', 'Sueldos'),
        ('OTRO', 'Otro'),
    ]

    TIPO_DOC_CHOICES = [
        ('FACTURA', 'Factura'),
        ('BOLETA', 'Boleta'),
    ]

    idGasto = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Proyecto',
    )
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOC_CHOICES,
        null=True,
        blank=True,
        verbose_name='Tipo Documento',
    )
    num_documento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='N° Documento',
    )
    concepto = models.CharField(max_length=30, choices=CONCEPTO_CHOICES)
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    maquinaria = models.ForeignKey(
        Maquinaria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Vehiculo / Maquinaria',
    )
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Trabajador',
    )
    modulo_torre = models.ForeignKey(
        ModuloTorre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Modulo / Torre',
    )
    fase = models.ForeignKey(
        Fase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gastos',
        verbose_name='Fase',
    )
    observaciones = models.TextField(blank=True, null=True)
    archivo_respaldo = models.FileField(
        upload_to='gastos_respaldo/',
        null=True,
        blank=True,
        verbose_name='Boleta / Factura',
    )
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-fecha', '-idGasto']

    def __str__(self):
        return f"{self.get_concepto_display()} - {self.fecha} - ${self.monto}"
