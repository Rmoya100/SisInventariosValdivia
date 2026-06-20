from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class EnforceReLoginAfterRestartMiddleware(MiddlewareMixin):
    """Invalidate authenticated sessions if the server was restarted.

    On each process start we set a new `SITE_SERVER_START_ID` in cache.
    Sessions store the start id at login in `_server_start_id`. If they
    do not match the current start id, the middleware logs out the user
    and asks them to re-authenticate.
    """

    CACHE_KEY = 'SITE_SERVER_START_ID'

    def process_request(self, request):
        try:
            current = cache.get(self.CACHE_KEY)
        except Exception:
            current = None

        if request.user.is_authenticated:
            session_val = request.session.get('_server_start_id')
            if current is None:
                # Cache lost the marker (first request after process start) — generate a new one
                try:
                    import uuid
                    current = uuid.uuid4().hex
                    cache.set(self.CACHE_KEY, current, None)
                except Exception:
                    current = None

            if current is not None:
                if session_val is None:
                    # Primera petición tras el login — registrar el ID del proceso actual
                    try:
                        request.session['_server_start_id'] = current
                    except Exception:
                        pass
                elif session_val != current:
                    # Sesión anterior a un reinicio del servidor — forzar re-login
                    logout(request)
                    try:
                        messages.info(request, 'Debes iniciar sesión nuevamente (servidor reiniciado).')
                    except Exception:
                        pass


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """
    Si el usuario tiene must_change_password=True, fuerza la redirección
    al formulario de cambio de contraseña de primer ingreso en cada request.
    Permite acceso únicamente a login, logout y primer_ingreso_password.
    Omite la verificación para superusuarios y administradores del sistema.
    """
    _ALLOWED_URL_NAMES = {'login', 'logout', 'primer_ingreso_password'}

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        if request.user.is_superuser or getattr(request.user, 'es_admin', False):
            return None
        if not getattr(request.user, 'must_change_password', False):
            return None
        try:
            url_name = request.resolver_match.url_name if request.resolver_match else None
        except Exception:
            url_name = None
        if url_name not in self._ALLOWED_URL_NAMES:
            return redirect(reverse('primer_ingreso_password'))
