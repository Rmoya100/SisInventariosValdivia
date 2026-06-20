"""
Comando para crear el usuario administrador inicial de forma segura.

Uso:
    python manage.py crear_admin
    python manage.py crear_admin --username jefe --password MiClaveSegura123!
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Usuario, Trabajador, Permiso


class Command(BaseCommand):
    help = 'Crea el usuario administrador inicial del sistema de inventarios.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin',  help='Nombre de usuario (default: admin)')
        parser.add_argument('--password', default=None,     help='Contraseña (si se omite, se solicitará de forma interactiva)')
        parser.add_argument('--email',    default='admin@inventario.local', help='Correo electrónico')

    def handle(self, *args, **options):
        username = options['username']
        email    = options['email']
        password = options['password']

        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'El usuario "{username}" ya existe. Operación cancelada.'))
            return

        if not password:
            import getpass
            password = getpass.getpass(f'Contraseña para "{username}": ')
            confirm  = getpass.getpass('Confirmar contraseña: ')
            if password != confirm:
                self.stderr.write(self.style.ERROR('Las contraseñas no coinciden.'))
                return

        with transaction.atomic():
            trabajador = Trabajador.objects.create(
                nombre='Admin', apellido='Sistema', correo=email
            )
            usuario = Usuario.objects.create_user(
                username=username,
                password=password,
                email=email,
                trabajador=trabajador,
                es_admin=True,
            )
            Permiso.objects.get_or_create(usuario=usuario)

        self.stdout.write(self.style.SUCCESS(
            f'✔ Usuario administrador "{username}" creado exitosamente.\n'
            f'  Accede en: http://127.0.0.1:8000/'
        ))
