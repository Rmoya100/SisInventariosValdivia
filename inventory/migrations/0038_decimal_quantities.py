from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0037_add_item_serviu_to_partida'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='stock_inicial',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='producto',
            name='stock_actual',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='stockproyecto',
            name='cantidad',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='detalleSalida',
            name='cantidad',
            field=models.DecimalField(decimal_places=3, max_digits=10),
        ),
    ]
