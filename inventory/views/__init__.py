from .auth import login_view, logout_view
from .auditoria import historial_list
from .gastos import GastoListView, GastoCreateView, GastoUpdateView, GastoDeleteView, FaseListView, FaseCreateView, FaseUpdateView, ResumenGastosProyectoView
from .dashboard import index, dashboard_graficos
from .productos import (
    ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    BodegaListView, BodegaCreateView, BodegaUpdateView, BodegaDeleteView,
    UnidadMedidaListView, UnidadMedidaCreateView, UnidadMedidaUpdateView, UnidadMedidaDeleteView,
)
from .compras import (
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView, ProveedorDeleteView,
    OrdenCompraView, OrdenCompraUpdateView, get_orden_compra_detalle
)
from .movimientos import (
    SalidaView, SalidaUpdateView, IngresoView, IngresoUpdateView,
    TransferenciaListView, TransferenciaCreateView, TransferenciaUpdateView, recibir_transferencia,
    trazabilidad_list, api_stock_disponible,
    api_partidas_por_proyecto, api_modulos_torre_por_proyecto,
)
from .usuarios import (
    UsuarioListView, crear_usuario, editar_usuario, editar_permisos, cambiar_password,
    primer_ingreso_password,
    TrabajadorListView, TrabajadorCreateView, TrabajadorUpdateView,
    ModuloTorreListView, ModuloTorreCreateView, ModuloTorreUpdateView,
    PartidaListView, PartidaCreateView, PartidaUpdateView,
    ProyectoListView, ProyectoCreateView, ProyectoUpdateView,
    get_proyectos_usuario, empresa_configuracion
)
from .equipos import (
    herramientas_view, herramienta_editar, herramienta_eliminar,
    mantenimiento_herramienta_view, recibir_herramienta_mantenimiento,
    maquinaria_view, maquinaria_editar, maquinaria_eliminar, actualizar_lectura_maquinaria,
    mantenimiento_maquinaria_view, recibir_maquinaria_mantenimiento,
    transferencia_activo_view, recibir_transferencia_activo
)
from .reportes import (
    reporte_compras_pdf, reporte_oc_pendientes_pdf, reporte_ingresos_pdf, reporte_ingreso_detail_pdf, reporte_salidas_pdf,
    reporte_productos_pdf, reporte_proveedores_pdf, reporte_categorias_pdf, reporte_transferencia_pdf,
    reporte_compras_list_view, reporte_stock_bodega_list_view, reporte_stock_bodega_pdf, exportar_stock_bodega_excel,
    reporte_movimiento_general_list_view, reporte_movimiento_general_pdf, exportar_movimiento_general_excel,
    exportar_productos_excel, exportar_proveedores_excel, exportar_categorias_excel,
    exportar_compras_excel, exportar_ingresos_excel, exportar_salidas_excel,
    reporte_herramientas_pdf, exportar_herramientas_excel, reporte_maquinarias_pdf, exportar_maquinarias_excel,
    reporte_movimientos_producto_list_view, reporte_movimientos_producto_pdf, exportar_movimientos_producto_excel,
    reporte_gasto_modulo_torre_list_view, reporte_gasto_modulo_torre_pdf, exportar_gasto_modulo_torre_excel,
    reporte_movimientos_usuario_list_view,
    reporte_gastos_list_view, reporte_gastos_pdf, exportar_gastos_excel,
)
