from django.db import migrations, models
import django.db.models.deletion


def migrar_salidas_a_catalogos(apps, schema_editor):
    Salida = apps.get_model('inventory', 'Salida')
    ModuloTorre = apps.get_model('inventory', 'ModuloTorre')
    Trabajador = apps.get_model('inventory', 'Trabajador')

    for salida in Salida.objects.all():
        modulo_texto = (getattr(salida, 'modulo_torre_texto', '') or '').strip()
        if modulo_texto:
            modulo, _ = ModuloTorre.objects.get_or_create(
                nombre=modulo_texto,
                defaults={'descripcion': '', 'activo': True},
            )
            salida.modulo_torre_id = modulo.pk

        solicitante_texto = (getattr(salida, 'solicitante_texto', '') or '').strip()
        if solicitante_texto:
            partes = solicitante_texto.split()
            nombre = partes[0]
            apellido = ' '.join(partes[1:]) if len(partes) > 1 else '-'
            trabajador = Trabajador.objects.filter(
                nombre__iexact=nombre,
                apellido__iexact=apellido,
            ).first()
            if trabajador is None:
                trabajador = Trabajador.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    correo='sin-correo@example.com',
                    cargo='OTRO',
                    sueldo=0,
                )
            salida.solicitante_id = trabajador.pk

        salida.save(update_fields=['modulo_torre', 'solicitante'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_ingreso_bodega_ordencompra_bodega_salida_bodega'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModuloTorre',
            fields=[
                ('idModuloTorre', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='trabajador',
            name='cargo',
            field=models.CharField(choices=[('JEFE DE TERRENO', 'Jefe de Terreno'), ('ADMINISTRADOR DE OBRA', 'Administrador de obra'), ('ENCARGADO DE RECURSOS', 'Encargado de recursos'), ('OTRO', 'Otro')], default='OTRO', max_length=100),
        ),
        migrations.AddField(
            model_name='trabajador',
            name='sueldo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RenameField(
            model_name='salida',
            old_name='modulo_torre',
            new_name='modulo_torre_texto',
        ),
        migrations.RenameField(
            model_name='salida',
            old_name='solicitante',
            new_name='solicitante_texto',
        ),
        migrations.AddField(
            model_name='salida',
            name='modulo_torre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='salidas', to='inventory.modulotorre'),
        ),
        migrations.AddField(
            model_name='salida',
            name='solicitante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='salidas_solicitadas', to='inventory.trabajador'),
        ),
        migrations.RunPython(migrar_salidas_a_catalogos, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='salida',
            name='modulo_torre_texto',
        ),
        migrations.RemoveField(
            model_name='salida',
            name='solicitante_texto',
        ),
    ]
