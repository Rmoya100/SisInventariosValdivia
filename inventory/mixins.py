from django.contrib.auth.mixins import PermissionRequiredMixin
from .perms import user_has_custom_perm


class AdminOrPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Permite acceso si el usuario es admin/staff/superuser
    O si tiene el permiso en el modelo Permiso personalizado.
    """
    def has_permission(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        # Admin/staff/superuser siempre tienen acceso
        if user.es_admin or user.is_superuser or user.is_staff:
            return True

        # Verificar contra el modelo Permiso personalizado
        perm = self.permission_required
        if isinstance(perm, str):
            return user_has_custom_perm(user, perm)
        # Si es una lista/tupla de permisos, basta con que tenga al menos uno
        return any(user_has_custom_perm(user, p) for p in perm)
