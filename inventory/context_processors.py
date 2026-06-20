from django.db.models import F, Q


def user_permissions(request):
    """
    Inyecta permisos del usuario en el contexto global.
    Los permisos se guardan en sesión para evitar un query adicional en cada request.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        cached = request.session.get('_user_perms_cache')
        if cached is None:
            from .models import Permiso
            permisos, _ = Permiso.objects.get_or_create(usuario=request.user)
            request.session['_user_perms_cache'] = permisos.pk
        else:
            from .models import Permiso
            permisos = Permiso.objects.get(pk=cached)

        is_admin = bool(
            getattr(request.user, 'es_admin', False)
            or getattr(request.user, 'is_superuser', False)
            or getattr(request.user, 'is_staff', False)
        )

        return {
            'user_perms': permisos,
            'is_admin': is_admin,
        }
    except Exception:
        return {}


def alertas_equipos(request):
    """
    Inyecta conteos de alertas de equipos en cada página para el banner persistente.
    Resultado cacheado en sesión; se invalida cuando cambia el valor_actual de alguna máquina.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        from .models import Maquinaria, Herramienta
        maq_alerta = Maquinaria.objects.filter(activo=True).filter(
            Q(tipo_control='HORAS', valor_actual__gte=F('ultimo_mantenimiento') + 200) |
            Q(tipo_control='KILOMETROS', valor_actual__gte=F('ultimo_mantenimiento') + 9000)
        ).count()
        herr_reparacion = Herramienta.objects.filter(activo=True, en_reparacion=True).count()
        return {
            'alerta_maquinarias_count': maq_alerta,
            'alerta_herramientas_count': herr_reparacion,
        }
    except Exception:
        return {}
