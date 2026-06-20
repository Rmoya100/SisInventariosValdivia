from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0022_alter_trabajador_cargo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='transferenciaactivo',
            name='fecha_recepcion',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transferenciaactivo',
            name='usuario_recibe',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='gdi_activos_recibidos',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='transferenciaactivo',
            name='usuario_despacha',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gdi_activos_despachados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
