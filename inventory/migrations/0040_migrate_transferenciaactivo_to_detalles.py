from django.db import migrations


def crear_detalles_desde_legacy(apps, schema_editor):
    TransferenciaActivo = apps.get_model('inventory', 'TransferenciaActivo')
    DetalleTransferenciaActivo = apps.get_model('inventory', 'DetalleTransferenciaActivo')

    for ta in TransferenciaActivo.objects.exclude(tipo_activo=None):
        recibido = ta.estado == 'RECEPCION OK'
        DetalleTransferenciaActivo.objects.create(
            transferencia=ta,
            tipo_activo=ta.tipo_activo,
            herramienta=ta.herramienta if ta.tipo_activo == 'HERRAMIENTA' else None,
            maquinaria=ta.maquinaria if ta.tipo_activo == 'MAQUINARIA' else None,
            recibido=recibido,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0039_add_detalle_transferencia_activo'),
    ]

    operations = [
        migrations.RunPython(crear_detalles_desde_legacy, migrations.RunPython.noop),
    ]
