from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Count, Sum, Q, F
from collections import defaultdict
from ..models import (
    Producto, DetalleIngreso, StockProyecto, DetalleSalida,
    DetalleTransferencia, DetalleCompra, Maquinaria, Herramienta, Salida, OrdenCompra, Empresa
)

@login_required
def index(request):
    proyecto = request.user.proyecto
    
    precios_dict = {}
    ultimos_ingresos = DetalleIngreso.objects.values('producto').annotate(max_id=Max('idDetalle'))
    ids_ingresos = [i['max_id'] for i in ultimos_ingresos]
    precios_qs = DetalleIngreso.objects.filter(idDetalle__in=ids_ingresos).values('producto_id', 'precio')
    for p in precios_qs:
        precios_dict[p['producto_id']] = float(p['precio'])

    if proyecto and not request.user.es_admin:
        stock_qs = StockProyecto.objects.filter(proyecto=proyecto, producto__activo=True)
        total_inventario_val = sum(sp.cantidad * precios_dict.get(sp.producto_id, 0) for sp in stock_qs)
        total_productos_inv = sum(sp.cantidad for sp in stock_qs)
    else:
        stock_qs = Producto.objects.filter(activo=True)
        total_inventario_val = sum(p.stock_actual * precios_dict.get(p.cod_prod, 0) for p in stock_qs)
        total_productos_inv = sum(p.stock_actual for p in stock_qs)

    ingresos_qs = DetalleIngreso.objects.all()
    if proyecto and not request.user.es_admin:
        ingresos_qs = ingresos_qs.filter(ingreso__proyecto=proyecto)
    
    total_recepciones_val = ingresos_qs.aggregate(total=Sum('subtotal'))['total'] or 0
    total_productos_rec = ingresos_qs.aggregate(total=Sum('cantidad'))['total'] or 0

    salidas_qs = DetalleSalida.objects.select_related('salida')
    if proyecto and not request.user.es_admin:
        salidas_qs = salidas_qs.filter(salida__proyecto=proyecto)
    
    total_salidas_val = sum(d.cantidad * precios_dict.get(d.producto_id, 0) for d in salidas_qs)
    total_productos_sal = salidas_qs.aggregate(total=Sum('cantidad'))['total'] or 0

    transf_qs = DetalleTransferencia.objects.select_related('transferencia')
    if proyecto and not request.user.es_admin:
        transf_qs = transf_qs.filter(Q(transferencia__proyecto_origen=proyecto) | Q(transferencia__proyecto_destino=proyecto))
    
    total_pedidos_val = sum(d.cantidad_enviada * precios_dict.get(d.producto_id, 0) for d in transf_qs)
    total_productos_ped = transf_qs.aggregate(total=Sum('cantidad_enviada'))['total'] or 0

    compras_qs = DetalleCompra.objects.all()
    if proyecto and not request.user.es_admin:
        compras_qs = compras_qs.filter(orden_compra__proyecto=proyecto)
    
    total_facturas_val = compras_qs.aggregate(total=Sum('subtotal'))['total'] or 0
    total_productos_fac = compras_qs.aggregate(total=Sum('cantidad'))['total'] or 0

    maquinarias_con_alerta = list(Maquinaria.objects.filter(activo=True).filter(
        Q(tipo_control='HORAS', valor_actual__gte=F('ultimo_mantenimiento') + 200) |
        Q(tipo_control='KILOMETROS', valor_actual__gte=F('ultimo_mantenimiento') + 9000)
    ))
    herramientas_en_reparacion = Herramienta.objects.filter(en_reparacion=True, activo=True).count()
    total_herramientas = Herramienta.objects.filter(activo=True).count()
    total_maquinarias = Maquinaria.objects.filter(activo=True).count()

    context = {
        'empresa': Empresa.objects.first(),
        'total_inventario_val': total_inventario_val,
        'total_productos_inv': total_productos_inv,
        'total_recepciones_val': total_recepciones_val,
        'total_productos_rec': total_productos_rec,
        'total_salidas_val': total_salidas_val,
        'total_productos_sal': total_productos_sal,
        'total_pedidos_val': total_pedidos_val,
        'total_productos_ped': total_productos_ped,
        'total_facturas_val': total_facturas_val,
        'total_productos_fac': total_productos_fac,
        'proyecto_actual': proyecto.nombre if proyecto else "Global (Todos)",
        'maquinarias_con_alerta': maquinarias_con_alerta,
        'herramientas_en_reparacion': herramientas_en_reparacion,
        'total_herramientas': total_herramientas,
        'total_maquinarias': total_maquinarias,
    }
    return render(request, 'inventory/index.html', context)

@login_required
def dashboard_graficos(request):
    productos_top_stock = Producto.objects.filter(activo=True).order_by('-stock_actual')[:10]
    detalles = DetalleSalida.objects.select_related('salida', 'producto')
    
    precios_dict = {}
    ultimos_ingresos = DetalleIngreso.objects.values('producto').annotate(max_id=Max('idDetalle'))
    ids_ingresos = [i['max_id'] for i in ultimos_ingresos]
    precios_qs = DetalleIngreso.objects.filter(idDetalle__in=ids_ingresos).values('producto_id', 'precio')
    for p in precios_qs:
        precios_dict[p['producto_id']] = float(p['precio'])

    valor_por_modulo = defaultdict(float)
    for d in detalles:
        precio = precios_dict.get(d.producto_id, 0)
        modulo_nombre = str(d.salida.modulo_torre) if d.salida.modulo_torre else 'Sin Modulo'
        valor_por_modulo[modulo_nombre] += d.cantidad * precio
    
    modulos_labels = list(valor_por_modulo.keys())
    modulos_valores = list(valor_por_modulo.values())

    oc_estados = OrdenCompra.objects.filter(estado__in=['PENDIENTE', 'RECEPCION PARCIAL']).values('estado').annotate(count=Count('estado'))
    oc_labels = [dict(OrdenCompra.ESTADO_CHOICES).get(item['estado']) for item in oc_estados]
    oc_counts = [item['count'] for item in oc_estados]

    context = {
        'productos_top_stock': productos_top_stock,
        'modulos_labels': modulos_labels,
        'modulos_valores': modulos_valores,
        'oc_labels': oc_labels,
        'oc_counts': oc_counts,
        'salidas_recientes': Salida.objects.all().order_by('-fecha', '-numSalida')[:10],
    }
    return render(request, 'inventory/dashboard_charts.html', context)
