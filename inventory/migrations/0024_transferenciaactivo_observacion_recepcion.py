from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0023_transferenciaactivo_recepcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='transferenciaactivo',
            name='observacion_recepcion',
            field=models.TextField(blank=True, null=True),
        ),
    ]
