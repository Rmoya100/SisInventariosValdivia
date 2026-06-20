from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0029_alter_historialmovimiento_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='historialmovimiento',
            name='bodega',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='historial',
                to='inventory.bodega',
            ),
        ),
    ]
