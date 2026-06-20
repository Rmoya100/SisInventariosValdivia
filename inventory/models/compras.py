from django.db import models
from django.db.models import Sum
from .core import Proyecto, Bodega
from .catalogo import Proveedor, Producto


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
        from .movimientos import DetalleIngreso
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
