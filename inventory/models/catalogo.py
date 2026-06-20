from django.db import models
from django.db.models import Sum
from .base import ActiveManager
from .core import Proyecto


class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    abreviatura = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"


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
    class Meta:
        ordering = ['nombre']


class Categoria(models.Model):
    idCategoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    cod_prod = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    unidad_medida = models.ForeignKey(
        UnidadMedida, on_delete=models.PROTECT, null=True, blank=True,
        related_name='productos', verbose_name='Unidad de Medida'
    )
    nombre = models.CharField(max_length=255, unique=True)
    stock_inicial = models.IntegerField(default=0)
    stock_actual = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']

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
        ordering = ['producto__nombre']

    def __str__(self):
        return f"{self.producto.nombre} en {self.proyecto.nombre}: {self.cantidad}"
