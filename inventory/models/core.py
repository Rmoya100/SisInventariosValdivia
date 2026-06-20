from django.db import models
from .base import ActiveManager


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


class Proyecto(models.Model):
    idProyecto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


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


class Partida(models.Model):
    idPartida = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, null=True, blank=True, related_name='partidas')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['nombre']
        unique_together = ('nombre', 'proyecto')

    def __str__(self):
        return self.nombre

