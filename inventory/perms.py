"""
Puente entre los nombres de permisos de Django ('inventory.view_X') y los campos
booleanos del modelo Permiso personalizado (tra_ver, prod_ver, etc.).

Esto permite que los mixins y decoradores verifiquen ambos sistemas.
"""

# Mapeo: nombre Django → campo en el modelo Permiso
PERM_MAP: dict[str, str] = {
    # Categorías
    'inventory.view_categoria':             'cat_ver',
    'inventory.add_categoria':              'cat_crear',
    'inventory.change_categoria':           'cat_editar',
    'inventory.delete_categoria':           'cat_eliminar',
    # Unidades de Medida (reutilizan permisos de categoría)
    'inventory.view_unidadmedida':          'cat_ver',
    'inventory.add_unidadmedida':           'cat_crear',
    'inventory.change_unidadmedida':        'cat_editar',
    'inventory.delete_unidadmedida':        'cat_eliminar',
    # Productos
    'inventory.view_producto':              'prod_ver',
    'inventory.add_producto':               'prod_crear',
    'inventory.change_producto':            'prod_editar',
    'inventory.delete_producto':            'prod_eliminar',
    # Proveedores
    'inventory.view_proveedor':             'prov_ver',
    'inventory.add_proveedor':              'prov_crear',
    'inventory.change_proveedor':           'prov_editar',
    'inventory.delete_proveedor':           'prov_eliminar',
    # Órdenes de Compra
    'inventory.view_ordencompra':           'ord_ver',
    'inventory.add_ordencompra':            'ord_crear',
    'inventory.change_ordencompra':         'ord_editar',
    'inventory.delete_ordencompra':         'ord_eliminar',
    # Ingresos
    'inventory.view_ingreso':               'ing_ver',
    'inventory.add_ingreso':                'ing_crear',
    'inventory.change_ingreso':             'ing_editar',
    'inventory.delete_ingreso':             'ing_eliminar',
    # Salidas
    'inventory.view_salida':                'sal_ver',
    'inventory.add_salida':                 'sal_crear',
    'inventory.change_salida':              'sal_editar',
    'inventory.delete_salida':              'sal_eliminar',
    # Proyectos
    'inventory.view_proyecto':              'pro_ver',
    'inventory.add_proyecto':               'pro_crear',
    'inventory.change_proyecto':            'pro_editar',
    'inventory.delete_proyecto':            'pro_eliminar',
    # Bodegas (usan permisos de proyecto)
    'inventory.view_bodega':                'pro_ver',
    'inventory.add_bodega':                 'pro_crear',
    'inventory.change_bodega':              'pro_editar',
    'inventory.delete_bodega':              'pro_eliminar',
    # Trabajadores
    'inventory.view_trabajador':            'trab_ver',
    'inventory.add_trabajador':             'trab_crear',
    'inventory.change_trabajador':          'trab_editar',
    'inventory.delete_trabajador':          'trab_eliminar',
    # Transferencias (GDI/GRI)
    'inventory.view_transferencia':         'tra_ver',
    'inventory.add_transferencia':          'tra_crear',
    'inventory.change_transferencia':       'tra_recibir',
    'inventory.delete_transferencia':       'tra_eliminar',
    # Herramientas
    'inventory.view_herramienta':           'herr_ver',
    'inventory.add_herramienta':            'herr_crear',
    'inventory.change_herramienta':         'herr_editar',
    'inventory.delete_herramienta':         'herr_eliminar',
    # Maquinaria
    'inventory.view_maquinaria':            'maq_ver',
    'inventory.add_maquinaria':             'maq_crear',
    'inventory.change_maquinaria':          'maq_editar',
    'inventory.delete_maquinaria':          'maq_eliminar',
    # GDI Activos (TransferenciaActivo)
    'inventory.view_transferenciaactivo':   'gdi_ver',
    'inventory.add_transferenciaactivo':    'gdi_crear',
    'inventory.change_transferenciaactivo': 'gdi_editar',
    'inventory.delete_transferenciaactivo': 'gdi_eliminar',
    # Mantención Herramientas
    'inventory.view_mantenimientoherramienta':   'mant_herr_ver',
    'inventory.add_mantenimientoherramienta':    'mant_herr_crear',
    'inventory.change_mantenimientoherramienta': 'mant_herr_editar',
    'inventory.delete_mantenimientoherramienta': 'mant_herr_eliminar',
    # Reparación Maquinaria
    'inventory.view_mantenimientomaquinaria':    'mant_maq_ver',
    'inventory.add_mantenimientomaquinaria':     'mant_maq_crear',
    'inventory.change_mantenimientomaquinaria':  'mant_maq_editar',
    'inventory.delete_mantenimientomaquinaria':  'mant_maq_eliminar',
    # Gastos
    'inventory.view_gasto':   'gasto_ver',
    'inventory.add_gasto':    'gasto_crear',
    'inventory.change_gasto': 'gasto_editar',
    'inventory.delete_gasto': 'gasto_eliminar',
    # Módulos Torre / Empresa (admin only, sin campo Permiso específico → denegar)
}


def user_has_custom_perm(user, perm: str) -> bool:
    """
    Verifica si el usuario tiene el permiso según el modelo Permiso personalizado.
    Retorna True si el campo correspondiente en Permiso está en True.
    Retorna False si no hay mapeo o si el usuario no tiene objeto Permiso.
    """
    campo = PERM_MAP.get(perm)
    if not campo:
        return False
    try:
        return bool(getattr(user.permisos, campo, False))
    except Exception:
        return False
