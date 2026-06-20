from django.core.management.base import BaseCommand
from django.db.models import Sum, F
from inventory.models import Producto, StockProyecto, DetalleIngreso, DetalleSalida, Proyecto


class Command(BaseCommand):
    help = (
        'Reconcilia stock_actual de cada Producto y cada StockProyecto '
        'recalculando desde los movimientos reales (ingresos y salidas). '
        'Usar cuando se sospeche desincronización causada por operaciones masivas o migraciones.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra las diferencias sin aplicar cambios.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('-- MODO DRY-RUN: no se aplicarán cambios --\n'))

        self._reconciliar_stock_global(dry_run)
        self._reconciliar_stock_proyecto(dry_run)

        self.stdout.write(self.style.SUCCESS('Reconciliación completada.'))

    def _reconciliar_stock_global(self, dry_run):
        self.stdout.write('Reconciliando stock_actual global...')
        productos = Producto.all_objects.all()
        cambios = 0

        ing_map = {
            r['producto']: r['total']
            for r in DetalleIngreso.objects.values('producto').annotate(total=Sum('cantidad'))
        }
        sal_map = {
            r['producto']: r['total']
            for r in DetalleSalida.objects.values('producto').annotate(total=Sum('cantidad'))
        }

        for producto in productos:
            ingresos = ing_map.get(producto.pk, 0)
            salidas = sal_map.get(producto.pk, 0)
            correcto = producto.stock_inicial + ingresos - salidas

            if producto.stock_actual != correcto:
                self.stdout.write(
                    f'  [{producto.pk}] {producto.nombre}: '
                    f'actual={producto.stock_actual} → correcto={correcto} '
                    f'(inicial={producto.stock_inicial}, ing={ingresos}, sal={salidas})'
                )
                if not dry_run:
                    Producto.all_objects.filter(pk=producto.pk).update(stock_actual=correcto)
                cambios += 1

        self.stdout.write(f'  {cambios} producto(s) corregido(s).')

    def _reconciliar_stock_proyecto(self, dry_run):
        self.stdout.write('Reconciliando StockProyecto...')
        cambios = 0

        for proyecto in Proyecto.all_objects.all():
            ing_map = {
                r['producto']: r['total']
                for r in DetalleIngreso.objects.filter(ingreso__proyecto=proyecto)
                .values('producto')
                .annotate(total=Sum('cantidad'))
            }
            sal_map = {
                r['producto']: r['total']
                for r in DetalleSalida.objects.filter(salida__proyecto=proyecto)
                .values('producto')
                .annotate(total=Sum('cantidad'))
            }

            producto_ids = set(ing_map) | set(sal_map)
            for prod_id in producto_ids:
                correcto = ing_map.get(prod_id, 0) - sal_map.get(prod_id, 0)
                sp = StockProyecto.objects.filter(producto_id=prod_id, proyecto=proyecto).first()

                if sp is None:
                    self.stdout.write(
                        f'  [nuevo] proyecto={proyecto.nombre} prod_id={prod_id} cantidad={correcto}'
                    )
                    if not dry_run:
                        StockProyecto.objects.create(
                            producto_id=prod_id, proyecto=proyecto, cantidad=correcto
                        )
                    cambios += 1
                elif sp.cantidad != correcto:
                    self.stdout.write(
                        f'  proyecto={proyecto.nombre} prod_id={prod_id}: '
                        f'actual={sp.cantidad} → correcto={correcto}'
                    )
                    if not dry_run:
                        StockProyecto.objects.filter(pk=sp.pk).update(cantidad=correcto)
                    cambios += 1

        self.stdout.write(f'  {cambios} registro(s) de StockProyecto corregido(s).')
