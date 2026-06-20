from django.db import migrations


def create_permisos_and_mark_admin(apps, schema_editor):
    Usuario = apps.get_model('inventory', 'Usuario')
    Permiso = apps.get_model('inventory', 'Permiso')

    for u in Usuario.objects.all():
        # marcar es_admin True si es superuser de Django
        if getattr(u, 'is_superuser', False) and not getattr(u, 'es_admin', False):
            u.es_admin = True
            u.save(update_fields=['es_admin'])
        # crear Permiso si no existe
        if not hasattr(u, 'permisos'):
            Permiso.objects.create(usuario=u)


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_permiso'),
    ]

    operations = [
        migrations.RunPython(create_permisos_and_mark_admin, reverse_code=migrations.RunPython.noop),
    ]
