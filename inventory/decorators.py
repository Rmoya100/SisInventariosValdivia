from functools import wraps
from django.core.exceptions import PermissionDenied
from .perms import user_has_custom_perm


def permission_or_admin(perm):
    """
    Permite acceso si el usuario es admin/staff/superuser
    O si tiene el permiso en el modelo Permiso personalizado.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied

            if user.es_admin or user.is_superuser or user.is_staff:
                return view_func(request, *args, **kwargs)

            if user_has_custom_perm(user, perm):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied
        return _wrapped
    return decorator


def permission_required(perm, login_url=None, raise_exception=False):
    """Alias para mantener compatibilidad con la firma estándar de Django."""
    return permission_or_admin(perm)
