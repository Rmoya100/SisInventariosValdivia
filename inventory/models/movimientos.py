from django.db import models
from django.db.models import Sum, F
from .core import Proyecto, Bodega, Partida
from .catalogo import Producto, StockProyecto
from .compras import OrdenCompra
from .personas import Trabajador, ModuloTorre, Usuario


class Ingreso(models.Model):
    numIngreso = models.AutoField(primary_key=True)
    fecha = models.DateField()
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, null=True, blank=True)
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
    modulo_torre = models.ForeignKey(ModuloTorre, on_delete=models.PROTECT, null=True, blank=True, related_name='salidas')
    partida = models.ForeignKey(Partida, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas')
    solicitante = models.ForeignKey(Trabajador, on_delete=models.PROTECT, null=True, blank=True, related_name='salidas_solicitadas')

    def __str__(self):
        return f"Salida {self.numSalida}"


class DetalleSalida(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    salida = models.ForeignKey(Salida, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)

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
    usuario_despacha = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='transferencias_enviadas')
    usuario_recibe = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_recibidas')
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

    def proximo_paso(self):
        if self.estado == 'RECEPCION OK': return 'GRI completa'
        if self.estado == 'RECEPCION PARCIAL': return 'Completar GRI'
        return 'Esperando GRI'

    def __str__(self):
        return f"GDI {self.idTransferencia}: {self.proyecto_origen} -> {self.proyecto_destino}"


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

