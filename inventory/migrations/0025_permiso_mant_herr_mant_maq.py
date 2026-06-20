from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0024_transferenciaactivo_observacion_recepcion'),
    ]

    operations = [
        migrations.AddField(model_name='permiso', name='mant_herr_ver',      field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_herr_crear',     field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_herr_editar',    field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_herr_eliminar',  field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_maq_ver',        field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_maq_crear',      field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_maq_editar',     field=models.BooleanField(default=True)),
        migrations.AddField(model_name='permiso', name='mant_maq_eliminar',   field=models.BooleanField(default=True)),
    ]
