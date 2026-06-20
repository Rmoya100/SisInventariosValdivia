from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0027_fix_must_change_password_existing_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Quitar el campo antiguo (TextField sin estructura)
        migrations.RemoveField(
            model_name='historialmovimiento',
            name='detalles',
        ),
        # Ampliar max_length del campo accion (descripción legible)
        migrations.AlterField(
            model_name='historialmovimiento',
            name='accion',
            field=models.CharField(max_length=500),
        ),
        # Permitir blank en la FK de usuario
        migrations.AlterField(
            model_name='historialmovimiento',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Tipo de acción con choices
        migrations.AddField(
            model_name='historialmovimiento',
            name='tipo_accion',
            field=models.CharField(
                choices=[
                    ('INGRESO_CREAR',           'Ingreso creado'),
                    ('SALIDA_CREAR',            'Salida creada'),
                    ('TRANSFERENCIA_DESPACHAR', 'Transferencia despachada'),
                    ('TRANSFERENCIA_RECIBIR',   'Transferencia recibida'),
                    ('TRANSFERENCIA_EDITAR',    'Transferencia editada'),
                    ('ORDEN_CREAR',             'Orden de compra creada'),
                    ('ORDEN_EDITAR',            'Orden de compra editada'),
                ],
                max_length=40,
                default='INGRESO_CREAR',
            ),
            preserve_default=False,
        ),
        # ID del documento relacionado
        migrations.AddField(
            model_name='historialmovimiento',
            name='objeto_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        # Datos estructurados del evento (reemplaza detalles TextField)
        migrations.AddField(
            model_name='historialmovimiento',
            name='datos',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
