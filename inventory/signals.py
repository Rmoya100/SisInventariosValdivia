from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.core.cache import cache


@receiver(user_logged_in)
def set_session_server_id(sender, user, request, **kwargs):
    """Store the current server start id in the user's session on login."""
    server_id = cache.get('SITE_SERVER_START_ID')
    if server_id is None:
        import uuid
        server_id = uuid.uuid4().hex
        cache.set('SITE_SERVER_START_ID', server_id, None)
    try:
        request.session['_server_start_id'] = server_id
    except Exception:
        pass


@receiver(user_logged_in)
def forzar_sesion_unica(sender, user, request, **kwargs):
    """Al iniciar sesión, invalida cualquier sesión anterior del mismo usuario."""
    from django.contrib.sessions.models import Session
    from .models import SesionActiva

    nueva_key = request.session.session_key
    try:
        registro = SesionActiva.objects.get(usuario=user)
        if registro.session_key and registro.session_key != nueva_key:
            Session.objects.filter(session_key=registro.session_key).delete()
        registro.session_key = nueva_key
        registro.save(update_fields=['session_key'])
    except SesionActiva.DoesNotExist:
        SesionActiva.objects.create(usuario=user, session_key=nueva_key)


@receiver(user_logged_out)
def limpiar_sesion_activa(sender, user, request, **kwargs):
    """Al cerrar sesión, elimina el registro de sesión activa."""
    if user and user.is_authenticated:
        from .models import SesionActiva
        SesionActiva.objects.filter(usuario=user).delete()

