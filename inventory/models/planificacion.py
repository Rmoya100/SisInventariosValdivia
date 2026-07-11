from django.db import models
from .base import ActiveManager
from .core import Proyecto, Partida
from .personas import Trabajador, ModuloTorre


class TareaPlanificacion(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE',  'Pendiente'),
        ('EN_CURSO',   'En curso'),
        ('COMPLETADA', 'Completada'),
        ('BLOQUEADA',  'Bloqueada'),
    ]

    idTarea    = models.AutoField(primary_key=True)
    proyecto   = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='tareas_planificacion')
    padre      = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtareas')
    wbs_orden  = models.PositiveSmallIntegerField(default=0)
    nivel      = models.PositiveSmallIntegerField(default=0)

    nombre     = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    progreso   = models.PositiveSmallIntegerField(default=0)
    es_hito    = models.BooleanField(default=False, verbose_name='Es Hito')
    estado     = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    partida      = models.ForeignKey(Partida, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_planificacion')
    responsable  = models.ForeignKey(Trabajador, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_planificacion')
    modulo_torre = models.ForeignKey(ModuloTorre, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_planificacion', verbose_name='Módulo / Torre')

    activo     = models.BooleanField(default=True)
    fecha_creacion     = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    objects     = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['proyecto', 'wbs_orden', 'nivel', 'idTarea']
        verbose_name = 'Tarea de Planificación'
        verbose_name_plural = 'Tareas de Planificación'

    def __str__(self):
        return f"[{self.proyecto.nombre}] {self.nombre}"

    @property
    def duracion_dias(self):
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return 0


class DependenciaTarea(models.Model):
    TIPO_CHOICES = [
        ('FS', 'Fin-Inicio (FS)'),
        ('SS', 'Inicio-Inicio (SS)'),
        ('FF', 'Fin-Fin (FF)'),
    ]
    tarea_sucesora    = models.ForeignKey(TareaPlanificacion, on_delete=models.CASCADE, related_name='predecesoras')
    tarea_predecesora = models.ForeignKey(TareaPlanificacion, on_delete=models.CASCADE, related_name='sucesoras')
    tipo              = models.CharField(max_length=2, choices=TIPO_CHOICES, default='FS')

    class Meta:
        unique_together = ('tarea_sucesora', 'tarea_predecesora')

    def __str__(self):
        return f"{self.tarea_predecesora} → {self.tarea_sucesora} ({self.tipo})"


class CalendarioProyecto(models.Model):
    proyecto    = models.OneToOneField(Proyecto, on_delete=models.CASCADE, related_name='calendario')
    lunes       = models.BooleanField(default=True)
    martes      = models.BooleanField(default=True)
    miercoles   = models.BooleanField(default=True)
    jueves      = models.BooleanField(default=True)
    viernes     = models.BooleanField(default=True)
    sabado      = models.BooleanField(default=False)
    domingo     = models.BooleanField(default=False)
    hora_inicio = models.TimeField(default='08:00')
    hora_fin    = models.TimeField(default='17:00')

    class Meta:
        verbose_name = 'Calendario de Proyecto'

    def __str__(self):
        return f"Calendario — {self.proyecto.nombre}"


class FeriadoCalendario(models.Model):
    calendario = models.ForeignKey(CalendarioProyecto, on_delete=models.CASCADE, related_name='feriados')
    fecha      = models.DateField()
    nombre     = models.CharField(max_length=100)

    class Meta:
        ordering = ['fecha']
        unique_together = ['calendario', 'fecha']
        verbose_name = 'Feriado'

    def __str__(self):
        return f"{self.fecha} — {self.nombre}"
