from django.db import models
from django.contrib.auth.models import AbstractUser
from .base import ActiveManager
from .core import Proyecto


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
    proyecto = models.ForeignKey(Proyecto, on_delete=models.SET_NULL, null=True, blank=True, related_name='modulos_torre')
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


class Usuario(AbstractUser):
    codUsuario = models.AutoField(primary_key=True)
    trabajador = models.OneToOneField(Trabajador, on_delete=models.CASCADE, null=True, blank=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.SET_NULL, null=True, blank=True, help_text="Proyecto por defecto")
    proyectos_asignados = models.ManyToManyField(Proyecto, related_name='usuarios_asignados', blank=True, help_text="Otros proyectos")
    es_admin = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)

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

    # Mantención Herramientas
    mant_herr_ver = models.BooleanField(default=True)
    mant_herr_crear = models.BooleanField(default=True)
    mant_herr_editar = models.BooleanField(default=True)
    mant_herr_eliminar = models.BooleanField(default=True)

    # Reparación Maquinaria
    mant_maq_ver = models.BooleanField(default=True)
    mant_maq_crear = models.BooleanField(default=True)
    mant_maq_editar = models.BooleanField(default=True)
    mant_maq_eliminar = models.BooleanField(default=True)

    # Gastos
    gasto_ver = models.BooleanField(default=True)
    gasto_crear = models.BooleanField(default=True)
    gasto_editar = models.BooleanField(default=True)
    gasto_eliminar = models.BooleanField(default=True)

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='permisos')

    def __str__(self):
        return f"Permisos de {self.usuario.username}"


class SesionActiva(models.Model):
    """Registra la única sesión activa por usuario para forzar sesión única."""
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='sesion_activa'
    )
    session_key = models.CharField(max_length=40)

    def __str__(self):
        return f"Sesión de {self.usuario.username}"
