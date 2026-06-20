from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_permiso_trab_crear_permiso_trab_editar_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='producto',
            index=models.Index(fields=['nombre'], name='producto_nombre_idx'),
        ),
        migrations.AddIndex(
            model_name='proveedor',
            index=models.Index(fields=['nombre'], name='proveedor_nombre_idx'),
        ),
        migrations.AddIndex(
            model_name='ordencompra',
            index=models.Index(fields=['estado'], name='oc_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='ordencompra',
            index=models.Index(fields=['fecha_compra'], name='oc_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='ingreso',
            index=models.Index(fields=['fecha'], name='ingreso_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='salida',
            index=models.Index(fields=['fecha'], name='salida_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='transferencia',
            index=models.Index(fields=['estado'], name='transferencia_estado_idx'),
        ),
    ]
