from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.index, name='index'),
    path('graficos/', views.dashboard_graficos, name='graficos'),
    path('reportes/trazabilidad/', views.trazabilidad_list, name='trazabilidad_list'),
    path('categorias/', views.CategoriaListView.as_view(), name='categorias'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
    path('unidades-medida/', views.UnidadMedidaListView.as_view(), name='unidades_medida'),
    path('unidades-medida/crear/', views.UnidadMedidaCreateView.as_view(), name='unidad_medida_crear'),
    path('unidades-medida/<int:pk>/editar/', views.UnidadMedidaUpdateView.as_view(), name='unidad_medida_editar'),
    path('unidades-medida/<int:pk>/eliminar/', views.UnidadMedidaDeleteView.as_view(), name='unidad_medida_eliminar'),
    path('productos/', views.ProductoListView.as_view(), name='productos'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedores'),
    path('proveedores/crear/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),

    # Proyectos
    path('proyectos/', views.ProyectoListView.as_view(), name='proyectos'),
    path('proyectos/crear/', views.ProyectoCreateView.as_view(), name='proyecto_crear'),
    path('proyectos/<int:pk>/editar/', views.ProyectoUpdateView.as_view(), name='proyecto_editar'),

    # Bodegas
    path('bodegas/', views.BodegaListView.as_view(), name='bodegas'),
    path('bodegas/crear/', views.BodegaCreateView.as_view(), name='bodega_crear'),
    path('bodegas/<int:pk>/editar/', views.BodegaUpdateView.as_view(), name='bodega_editar'),
    path('bodegas/<int:pk>/eliminar/', views.BodegaDeleteView.as_view(), name='bodega_eliminar'),

    # Trabajadores
    path('trabajadores/', views.TrabajadorListView.as_view(), name='trabajadores_list'),
    path('trabajadores/crear/', views.TrabajadorCreateView.as_view(), name='trabajador_crear'),
    path('trabajadores/<int:pk>/editar/', views.TrabajadorUpdateView.as_view(), name='trabajador_editar'),

    # Modulo Torre
    path('modulos-torre/', views.ModuloTorreListView.as_view(), name='modulos_torre'),
    path('modulos-torre/crear/', views.ModuloTorreCreateView.as_view(), name='modulo_torre_crear'),
    path('modulos-torre/<int:pk>/editar/', views.ModuloTorreUpdateView.as_view(), name='modulo_torre_editar'),

    # Partidas
    path('partidas/', views.PartidaListView.as_view(), name='partidas'),
    path('partidas/crear/', views.PartidaCreateView.as_view(), name='partida_crear'),
    path('partidas/<int:pk>/editar/', views.PartidaUpdateView.as_view(), name='partida_editar'),

    # Transferencias
    path('transferencias/', views.TransferenciaListView.as_view(), name='transferencias'),
    path('transferencias/crear/', views.TransferenciaCreateView.as_view(), name='transferencia_crear'),
    path('transferencias/<int:pk>/recibir/', views.recibir_transferencia, name='transferencia_recibir'),
    path('transferencias/<int:pk>/editar/', views.TransferenciaUpdateView.as_view(), name='transferencia_editar'),
    path('transferencias/<int:pk>/pdf/', views.reporte_transferencia_pdf, name='reporte_transferencia_pdf'),

    # Órdenes de Compra
    path('ordenes/', views.OrdenCompraView.as_view(), name='ordenes'),
    path('ordenes/<int:pk>/editar/', views.OrdenCompraUpdateView.as_view(), name='orden_compra_editar'),
    path('salidas/', views.SalidaView.as_view(), name='salidas'),
    path('salidas/<int:pk>/editar/', views.SalidaUpdateView.as_view(), name='salida_editar'),
    path('ingresos/', views.IngresoView.as_view(), name='ingresos'),
    path('ingresos/<int:pk>/editar/', views.IngresoUpdateView.as_view(), name='ingreso_editar'),
    path('ordenes/<int:orden_id>/detalle/', views.get_orden_compra_detalle, name='orden_compra_detalle'),
    
    # Reportes PDF
    path('reportes/compras/listado/', views.reporte_compras_list_view, name='reporte_compras_listado'),
    path('reportes/compras/', views.reporte_compras_pdf, name='reporte_compras_pdf'),
    path('reportes/compras/pendientes/', views.reporte_oc_pendientes_pdf, name='reporte_oc_pendientes_pdf'),
    path('reportes/stock-bodega/', views.reporte_stock_bodega_list_view, name='reporte_stock_bodega_listado'),
    path('reportes/stock-bodega/pdf/', views.reporte_stock_bodega_pdf, name='reporte_stock_bodega_pdf'),
    path('reportes/stock-bodega/excel/', views.exportar_stock_bodega_excel, name='exportar_stock_bodega_excel'),
    # Reportes de Movimientos de Producto
    path('reportes/movimientos-producto/listado/', views.reporte_movimientos_producto_list_view, name='reporte_movimientos_producto_listado'),
    path('reportes/movimientos-producto/pdf/', views.reporte_movimientos_producto_pdf, name='reporte_movimientos_producto_pdf'),
    path('reportes/movimientos-producto/excel/', views.exportar_movimientos_producto_excel, name='exportar_movimientos_producto_excel'),
    path('reportes/movimiento-general/', views.reporte_movimiento_general_list_view, name='reporte_movimiento_general_listado'),
    path('reportes/movimiento-general/pdf/', views.reporte_movimiento_general_pdf, name='reporte_movimiento_general_pdf'),
    path('reportes/movimiento-general/excel/', views.exportar_movimiento_general_excel, name='exportar_movimiento_general_excel'),
    path('reportes/gasto-modulo-torre/', views.reporte_gasto_modulo_torre_list_view, name='reporte_gasto_modulo_listado'),
    path('reportes/gasto-modulo-torre/pdf/', views.reporte_gasto_modulo_torre_pdf, name='reporte_gasto_modulo_pdf'),
    path('reportes/gasto-modulo-torre/excel/', views.exportar_gasto_modulo_torre_excel, name='exportar_gasto_modulo_excel'),
    path('reportes/ingresos/', views.reporte_ingresos_pdf, name='reporte_ingresos_pdf'),
    path('reportes/ingresos/<int:pk>/', views.reporte_ingreso_detail_pdf, name='reporte_ingreso_detail_pdf'),
    path('reportes/salidas/', views.reporte_salidas_pdf, name='reporte_salidas_pdf'),
    path('reportes/productos/', views.reporte_productos_pdf, name='reporte_productos_pdf'),
    path('reportes/proveedores/', views.reporte_proveedores_pdf, name='reporte_proveedores_pdf'),
    path('reportes/categorias/', views.reporte_categorias_pdf, name='reporte_categorias_pdf'),

    # Reportes Excel
    path('reportes/excel/compras/', views.exportar_compras_excel, name='exportar_compras_excel'),
    path('reportes/excel/ingresos/', views.exportar_ingresos_excel, name='exportar_ingresos_excel'),
    path('reportes/excel/salidas/', views.exportar_salidas_excel, name='exportar_salidas_excel'),
    path('reportes/excel/productos/', views.exportar_productos_excel, name='exportar_productos_excel'),
    path('reportes/excel/proveedores/', views.exportar_proveedores_excel, name='exportar_proveedores_excel'),
    path('reportes/excel/categorias/', views.exportar_categorias_excel, name='exportar_categorias_excel'),

    # Usuarios y Permisos
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_list'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/permisos/', views.editar_permisos, name='editar_permisos'),
    path('usuarios/<int:usuario_id>/password/', views.cambiar_password, name='cambiar_password'),
    path('empresa/', views.empresa_configuracion, name='empresa_configuracion'),

    # Herramientas
    path('herramientas/', views.herramientas_view, name='herramientas'),
    path('herramientas/<int:pk>/editar/', views.herramienta_editar, name='herramienta_editar'),
    path('herramientas/<int:pk>/eliminar/', views.herramienta_eliminar, name='herramienta_eliminar'),
    path('herramientas/mantenimiento/', views.mantenimiento_herramienta_view, name='mantenimiento_herramientas'),
    path('herramientas/mantenimiento/<int:pk>/recibir/', views.recibir_herramienta_mantenimiento, name='recibir_herramienta_mantenimiento'),

    # Maquinarias
    path('maquinarias/', views.maquinaria_view, name='maquinarias'),
    path('maquinarias/<int:pk>/editar/', views.maquinaria_editar, name='maquinaria_editar'),
    path('maquinarias/<int:pk>/eliminar/', views.maquinaria_eliminar, name='maquinaria_eliminar'),
    path('maquinarias/<int:pk>/lectura/', views.actualizar_lectura_maquinaria, name='maquinaria_lectura'),
    path('maquinarias/mantenimiento/', views.mantenimiento_maquinaria_view, name='mantenimiento_maquinarias'),
    path('maquinarias/mantenimiento/<int:pk>/recibir/', views.recibir_maquinaria_mantenimiento, name='recibir_maquinaria_mantenimiento'),

    # GDI de Activos (Herramientas/Maquinaria entre bodegas)
    path('activos/transferencias/', views.transferencia_activo_view, name='transferencias_activos'),
    path('activos/transferencias/<int:pk>/recibir/', views.recibir_transferencia_activo, name='transferencia_activo_recibir'),

    # Reportes Equipos
    path('reportes/herramientas/pdf/', views.reporte_herramientas_pdf, name='reporte_herramientas_pdf'),
    path('reportes/herramientas/excel/', views.exportar_herramientas_excel, name='exportar_herramientas_excel'),
    path('reportes/maquinarias/pdf/', views.reporte_maquinarias_pdf, name='reporte_maquinarias_pdf'),
    path('reportes/maquinarias/excel/', views.exportar_maquinarias_excel, name='exportar_maquinarias_excel'),

    # Gastos
    path('gastos/', views.GastoListView.as_view(), name='gastos'),
    path('gastos/crear/', views.GastoCreateView.as_view(), name='gasto_crear'),
    path('gastos/<int:pk>/editar/', views.GastoUpdateView.as_view(), name='gasto_editar'),
    path('gastos/<int:pk>/eliminar/', views.GastoDeleteView.as_view(), name='gasto_eliminar'),
    path('gastos/resumen-proyecto/', views.ResumenGastosProyectoView.as_view(), name='resumen_gastos_proyecto'),

    # Fases
    path('fases/', views.FaseListView.as_view(), name='fases'),
    path('fases/crear/', views.FaseCreateView.as_view(), name='fase_crear'),
    path('fases/<int:pk>/editar/', views.FaseUpdateView.as_view(), name='fase_editar'),

    # Reportes de Gastos
    path('reportes/gastos/', views.reporte_gastos_list_view, name='reporte_gastos_listado'),
    path('reportes/gastos/pdf/', views.reporte_gastos_pdf, name='reporte_gastos_pdf'),
    path('reportes/gastos/excel/', views.exportar_gastos_excel, name='exportar_gastos_excel'),

    # Cambio de contraseña primer ingreso
    path('mi-cuenta/cambiar-clave/', views.primer_ingreso_password, name='primer_ingreso_password'),

    # Auditoría
    path('auditoria/', views.historial_list, name='historial_auditoria'),
    path('reportes/movimientos-usuario/', views.reporte_movimientos_usuario_list_view, name='reporte_movimientos_usuario'),

    # API multi-proyecto
    path('api/proyectos-usuario/', views.get_proyectos_usuario, name='api_proyectos_usuario'),
    path('api/stock-disponible/', views.api_stock_disponible, name='api_stock_disponible'),
    path('api/partidas-por-proyecto/', views.api_partidas_por_proyecto, name='api_partidas_por_proyecto'),
    path('api/modulos-torre-por-proyecto/', views.api_modulos_torre_por_proyecto, name='api_modulos_torre_por_proyecto'),
]
