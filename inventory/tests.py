from django.test import TestCase
from django.urls import reverse

from .models import (
    Bodega,
    Categoria,
    DetalleCompra,
    Ingreso,
    ModuloTorre,
    OrdenCompra,
    Producto,
    Proyecto,
    Proveedor,
    Salida,
    StockProyecto,
    Trabajador,
    Usuario,
)


class MovimientoBodegaAssignmentTests(TestCase):
    def setUp(self):
        self.proyecto = Proyecto.objects.create(nombre='Proyecto Norte')
        self.bodega = Bodega.objects.create(nombre='Bodega Norte', proyecto=self.proyecto)
        self.categoria = Categoria.objects.create(nombre='Materiales')
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre='Cemento',
            stock_inicial=0,
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Uno',
            direccion='Direccion',
            telefono='123',
            contacto='Contacto',
            cel_contacto='456',
            correo='proveedor@example.com',
        )
        self.usuario = Usuario.objects.create_user(
            username='admin',
            password='pass',
            es_admin=True,
            proyecto=self.proyecto,
        )
        self.modulo_torre = ModuloTorre.objects.create(nombre='TORRE A')
        self.solicitante = Trabajador.objects.create(
            nombre='Juan',
            apellido='Perez',
            correo='juan@example.com',
            cargo='JEFE DE TERRENO',
            sueldo=1000,
        )
        self.client.force_login(self.usuario)

    def _management_form(self):
        return {
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
        }

    def test_orden_compra_uses_user_project_bodega(self):
        data = {
            'numCompra': 'OC-001',
            'proveedor': self.proveedor.pk,
            'bodega': self.bodega.pk,
            'fecha_compra': '2026-05-26',
            'forma_de_pago': 'CONTADO',
            **self._management_form(),
            'detalles-0-producto': self.producto.pk,
            'detalles-0-cantidad': '5',
            'detalles-0-precio': '1000',
        }

        response = self.client.post(reverse('ordenes'), data)

        self.assertEqual(response.status_code, 302)
        orden = OrdenCompra.objects.get(numCompra='OC-001')
        self.assertEqual(orden.proyecto, self.proyecto)
        self.assertEqual(orden.bodega, self.bodega)

    def test_admin_without_project_selects_bodega_for_order(self):
        admin_sin_proyecto = Usuario.objects.create_user(
            username='admin_sin_proyecto',
            password='pass',
            es_admin=True,
        )
        self.client.force_login(admin_sin_proyecto)
        data = {
            'numCompra': 'OC-ADMIN',
            'proveedor': self.proveedor.pk,
            'bodega': self.bodega.pk,
            'fecha_compra': '2026-05-26',
            'forma_de_pago': 'CONTADO',
            **self._management_form(),
            'detalles-0-producto': self.producto.pk,
            'detalles-0-cantidad': '2',
            'detalles-0-precio': '1500',
        }

        response = self.client.post(reverse('ordenes'), data)

        self.assertEqual(response.status_code, 302)
        orden = OrdenCompra.objects.get(numCompra='OC-ADMIN')
        self.assertEqual(orden.proyecto, self.proyecto)
        self.assertEqual(orden.bodega, self.bodega)

    def test_ingreso_inherits_project_bodega_from_order_without_losing_assignment(self):
        orden = OrdenCompra.objects.create(
            numCompra='OC-002',
            proveedor=self.proveedor,
            proyecto=self.proyecto,
            bodega=self.bodega,
            fecha_compra='2026-05-26',
            forma_de_pago='CONTADO',
        )
        DetalleCompra.objects.create(
            orden_compra=orden,
            producto=self.producto,
            cantidad=5,
            precio=1000,
            subtotal=5000,
        )
        data = {
            'fecha': '2026-05-26',
            'orden_compra': orden.pk,
            'tipo_documento': 'FACTURA',
            'num_documento': 'F-001',
            **self._management_form(),
            'detalles-0-producto': self.producto.pk,
            'detalles-0-cantidad': '5',
            'detalles-0-precio': '1000',
        }

        response = self.client.post(reverse('ingresos'), data)

        self.assertEqual(response.status_code, 302)
        ingreso = Ingreso.objects.get(num_documento='F-001')
        self.assertEqual(ingreso.proyecto, self.proyecto)
        self.assertEqual(ingreso.bodega, self.bodega)

    def test_salida_uses_user_project_bodega(self):
        StockProyecto.objects.create(
            producto=self.producto,
            proyecto=self.proyecto,
            cantidad=10,
        )
        data = {
            'fecha': '2026-05-26',
            'modulo_torre': self.modulo_torre.pk,
            'solicitante': self.solicitante.pk,
            **self._management_form(),
            'detalles-0-producto': self.producto.pk,
            'detalles-0-cantidad': '3',
        }

        response = self.client.post(reverse('salidas'), data)

        self.assertEqual(response.status_code, 302)
        salida = Salida.objects.get(modulo_torre=self.modulo_torre)
        self.assertEqual(salida.proyecto, self.proyecto)
        self.assertEqual(salida.bodega, self.bodega)

    def test_trabajador_edit_page_and_save_use_existing_route_names(self):
        trabajador = Trabajador.objects.create(
            nombre='Pedro',
            apellido='Rojas',
            correo='pedro@example.com',
        )

        response = self.client.get(reverse('trabajador_editar', args=[trabajador.pk]))

        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('trabajador_editar', args=[trabajador.pk]), {
            'nombre': 'Pedro',
            'apellido': 'Soto',
            'correo': 'pedro.soto@example.com',
            'cargo': 'ADMINISTRADOR DE OBRA',
            'sueldo': '1200',
        })

        self.assertRedirects(response, reverse('trabajadores_list'))
        trabajador.refresh_from_db()
        self.assertEqual(trabajador.apellido, 'SOTO')
        self.assertEqual(trabajador.correo, 'PEDRO.SOTO@EXAMPLE.COM')
        self.assertEqual(trabajador.cargo, 'ADMINISTRADOR DE OBRA')

    def test_admin_can_assign_user_projects_from_permissions_page(self):
        otro_proyecto = Proyecto.objects.create(nombre='Proyecto Sur')
        usuario_objetivo = Usuario.objects.create_user(
            username='operador',
            password='pass',
        )

        response = self.client.get(reverse('editar_permisos', args=[usuario_objetivo.pk]))
        self.assertContains(response, self.proyecto.nombre)
        self.assertContains(response, otro_proyecto.nombre)

        response = self.client.post(reverse('editar_permisos', args=[usuario_objetivo.pk]), {
            'proyecto': self.proyecto.pk,
            'proyectos_asignados': [otro_proyecto.pk],
            'cat_ver': 'on',
        })

        self.assertRedirects(response, reverse('usuarios_list'))
        usuario_objetivo.refresh_from_db()
        self.assertEqual(usuario_objetivo.proyecto, self.proyecto)
        self.assertIn(otro_proyecto, list(usuario_objetivo.proyectos_asignados.all()))

    def test_admin_can_manage_modulo_torre_catalog(self):
        response = self.client.get(reverse('modulos_torre'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('modulo_torre_crear'), {
            'nombre': 'MODULO B',
            'descripcion': 'Sector B',
            'activo': 'on',
        })

        self.assertRedirects(response, reverse('modulos_torre'))
        self.assertTrue(ModuloTorre.objects.filter(nombre='MODULO B').exists())

    def test_reporte_movimientos_producto_views(self):
        self.client.force_login(self.usuario)
        url = reverse('reporte_movimientos_producto_listado')
        response = self.client.get(url, {
            'producto': self.producto.pk,
            'bodega': self.bodega.pk
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cemento')
        
        pdf_url = reverse('reporte_movimientos_producto_pdf')
        response_pdf = self.client.get(pdf_url, {
            'producto': self.producto.pk,
            'bodega': self.bodega.pk
        })
        self.assertEqual(response_pdf.status_code, 200)

        excel_url = reverse('exportar_movimientos_producto_excel')
        response_excel = self.client.get(excel_url, {
            'producto': self.producto.pk,
            'bodega': self.bodega.pk
        })
        self.assertEqual(response_excel.status_code, 200)

    def test_reporte_movimientos_producto_views_no_selection(self):
        self.client.force_login(self.usuario)
        url = reverse('reporte_movimientos_producto_listado')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consulta de Movimientos')

    def test_reporte_gasto_modulo_views(self):
        self.client.force_login(self.usuario)
        url = reverse('reporte_gasto_modulo_listado')
        
        # Test general summary list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gasto de Material por Módulo')
        
        # Test specific module filter
        response_detail = self.client.get(url, {
            'modulo': self.modulo_torre.pk
        })
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, 'Detalle de Gasto')
        
        # Test PDF view
        pdf_url = reverse('reporte_gasto_modulo_pdf')
        response_pdf = self.client.get(pdf_url, {
            'modulo': self.modulo_torre.pk
        })
        self.assertEqual(response_pdf.status_code, 200)
        
        # Test Excel view
        excel_url = reverse('exportar_gasto_modulo_excel')
        response_excel = self.client.get(excel_url, {
            'modulo': self.modulo_torre.pk
        })
        self.assertEqual(response_excel.status_code, 200)

