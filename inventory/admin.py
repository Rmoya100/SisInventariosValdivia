from django.contrib import admin
from .models import Empresa, Proyecto, Partida, ModuloTorre


class PartidaInline(admin.TabularInline):
    model = Partida
    extra = 1
    fields = ('nombre', 'descripcion', 'item_serviu', 'activo')
    ordering = ('nombre',)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono')


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('idProyecto', 'nombre', 'activo')
    list_filter = ('activo',)
    inlines = [PartidaInline]


@admin.register(ModuloTorre)
class ModuloTorreAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proyecto', 'activo')
    list_filter = ('proyecto', 'activo')
    ordering = ('proyecto__nombre', 'nombre')
