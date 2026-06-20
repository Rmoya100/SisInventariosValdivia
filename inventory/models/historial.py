from django.db import models
from .core import Bodega
from .personas import Usuario


class HistorialMovimiento(models.Model):
    TIPO_CHOICES = [
        ('INGRESO_CREAR',           'Ingreso creado'),
        ('SALIDA_CREAR',            'Salida creada'),
        ('TRANSFERENCIA_DESPACHAR', 'Transferencia despachada'),
        ('TRANSFERENCIA_RECIBIR',   'Transferencia recibida'),
        ('TRANSFERENCIA_EDITAR',    'Transferencia editada'),
        ('ORDEN_CREAR',             'Orden de compra creada'),
        ('ORDEN_EDITAR',            'Orden de compra editada'),
    ]

    fecha       = models.DateTimeField(auto_now_add=True)
    usuario     = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    bodega      = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, related_name='historial')
    tipo_accion = models.CharField(max_length=40, choices=TIPO_CHOICES)
    modulo      = models.CharField(max_length=100)
    objeto_id   = models.PositiveIntegerField(null=True, blank=True)
    accion      = models.CharField(max_length=500)
    datos       = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Historial de movimiento'
        verbose_name_plural = 'Historial de movimientos'

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y %H:%M} — {self.get_tipo_accion_display()}: {self.accion[:60]}"
