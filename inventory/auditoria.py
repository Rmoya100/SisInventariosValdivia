import json
import logging
from decimal import Decimal
from .models import HistorialMovimiento

logger = logging.getLogger(__name__)


def _serializable(datos):
    """Convert Decimal (and other non-JSON-native types) to float recursively."""
    if isinstance(datos, dict):
        return {k: _serializable(v) for k, v in datos.items()}
    if isinstance(datos, (list, tuple)):
        return [_serializable(v) for v in datos]
    if isinstance(datos, Decimal):
        return float(datos)
    return datos


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
            datos=_serializable(datos or {}),
            bodega=bodega,
        )
    except Exception:
        logger.exception(
            "Error al registrar auditoría: tipo=%s objeto=%s accion=%s",
            tipo_accion, objeto_id, accion,
        )
