import logging
from .models import HistorialMovimiento

logger = logging.getLogger(__name__)


def registrar(usuario, tipo_accion, objeto_id, modulo, accion, datos=None, bodega=None):
    """
    Registra una entrada en el historial de auditoría.
    Captura excepciones silenciosamente para no interrumpir la lógica de negocio.
    """
    try:
        HistorialMovimiento.objects.create(
            usuario=usuario,
            tipo_accion=tipo_accion,
            objeto_id=objeto_id,
            modulo=modulo,
            accion=accion,
            datos=datos or {},
            bodega=bodega,
        )
    except Exception:
        logger.exception(
            "Error al registrar auditoría: tipo=%s objeto=%s accion=%s",
            tipo_accion, objeto_id, accion,
        )
