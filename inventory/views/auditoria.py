from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import HistorialMovimiento, Producto, Bodega


@login_required
def historial_list(request):
    if not (request.user.es_admin or request.user.is_superuser):
        messages.error(request, 'Solo los administradores pueden ver el historial de auditoría.')
        return redirect('index')

    TIPOS_EXCLUIDOS = ('ORDEN_CREAR', 'ORDEN_EDITAR')
    qs = HistorialMovimiento.objects.select_related('usuario', 'bodega').exclude(
        tipo_accion__in=TIPOS_EXCLUIDOS
    ).order_by('-fecha')

    bodega_id   = request.GET.get('bodega_id', '')
    desde       = request.GET.get('desde', '')
    hasta       = request.GET.get('hasta', '')
    producto_id = request.GET.get('producto_id', '')

    if bodega_id:
        qs = qs.filter(bodega_id=bodega_id)
    if desde:
        qs = qs.filter(fecha__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha__date__lte=hasta)

    filtro_producto_nombre = ''
    if producto_id:
        try:
            prod = Producto.all_objects.get(pk=producto_id)
            filtro_producto_nombre = prod.nombre
            qs = qs.filter(datos__icontains=filtro_producto_nombre)
        except Producto.DoesNotExist:
            producto_id = ''

    paginator = Paginator(qs, 50)
    page_obj  = paginator.get_page(request.GET.get('page'))

    for h in page_obj:
        datos     = h.datos if isinstance(h.datos, dict) else {}
        productos_list = datos.get('productos', [])
        h.total_cantidad = sum(
            (p.get('cantidad') or p.get('cantidad_enviada') or p.get('enviada') or 0)
            for p in productos_list
        )
        if h.bodega:
            h.bodega_display = h.bodega.nombre
        elif h.tipo_accion in ('TRANSFERENCIA_DESPACHAR', 'TRANSFERENCIA_EDITAR'):
            h.bodega_display = datos.get('origen', '—')
        elif h.tipo_accion == 'TRANSFERENCIA_RECIBIR':
            h.bodega_display = datos.get('destino', '—')
        else:
            h.bodega_display = datos.get('bodega') or datos.get('proyecto') or '—'

    bodegas   = Bodega.objects.order_by('nombre')
    productos = Producto.objects.order_by('nombre')

    return render(request, 'inventory/historial_list.html', {
        'page_obj':               page_obj,
        'tipo_choices':           HistorialMovimiento.TIPO_CHOICES,
        'bodegas':                bodegas,
        'productos':              productos,
        'filtro_bodega_id':       bodega_id,
        'filtro_desde':           desde,
        'filtro_hasta':           hasta,
        'filtro_producto_id':     producto_id,
        'filtro_producto_nombre': filtro_producto_nombre,
    })
