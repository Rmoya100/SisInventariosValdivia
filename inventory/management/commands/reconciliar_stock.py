from django.core.management.base import BaseCommand
from django.db.models import Sum, F
from inventory.models import Producto, StockProyecto, DetalleIngreso, DetalleSalida, DetalleTransferencia, Proyecto


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
                    f'actual={producto.stock_actual} -> correcto={correcto} '
                    f'(inicial={producto.stock_inicial}, ing={ingresos}, sal={salidas})'
                )
                if not dry_run:
                    Producto.all_objects.filter(pk=producto.pk).update(stock_actual=correcto)
                cambios += 1

        self.stdout.write(f'  {cambios} producto(s) corregido(s).')

    def _reconciliar_stock_proyecto(self, dry_run):
        self.stdout.write('Reconciliando StockProyecto...')
        cambios = 0

        for producto in Producto.all_objects.all():
            ing_map = {
                r['ingreso__proyecto']: r['total']
                for r in DetalleIngreso.objects.filter(producto=producto)
                .values('ingreso__proyecto').annotate(total=Sum('cantidad'))
            }
            sal_map = {
                r['salida__proyecto']: r['total']
                for r in DetalleSalida.objects.filter(producto=producto)
                .values('salida__proyecto').annotate(total=Sum('cantidad'))
            }
            env_map = {
                r['transferencia__proyecto_origen']: r['total']
                for r in DetalleTransferencia.objects.filter(producto=producto)
                .values('transferencia__proyecto_origen').annotate(total=Sum('cantidad_enviada'))
            }
            rec_map = {
                r['transferencia__proyecto_destino']: r['total']
                for r in DetalleTransferencia.objects.filter(producto=producto)
                .values('transferencia__proyecto_destino').annotate(total=Sum('cantidad_recibida'))
            }

            existing_sps = {sp.proyecto_id: sp for sp in StockProyecto.objects.filter(producto=producto)}
            proyecto_ids = set(ing_map) | set(sal_map) | set(env_map) | set(rec_map) | set(existing_sps)
            proyecto_ids.discard(None)

            if not proyecto_ids:
                continue

            movimientos = {
                pid: (ing_map.get(pid, 0) - sal_map.get(pid, 0)
                      - env_map.get(pid, 0) + rec_map.get(pid, 0))
                for pid in proyecto_ids
            }

            # Atribuir stock_inicial al proyecto primario (el de mayor cantidad actual, o el único)
            if producto.stock_inicial > 0:
                if len(proyecto_ids) == 1:
                    primary_pid = next(iter(proyecto_ids))
                elif existing_sps:
                    primary_pid = max(existing_sps, key=lambda pid: existing_sps[pid].cantidad)
                else:
                    primary_pid = next(iter(proyecto_ids))
                movimientos[primary_pid] = movimientos[primary_pid] + producto.stock_inicial

            for pid in proyecto_ids:
                correcto = movimientos[pid]
                sp = existing_sps.get(pid)
                if sp is None:
                    self.stdout.write(
                        f'  [nuevo] prod={producto.nombre} proj_id={pid} cantidad={correcto}'
                    )
                    if not dry_run:
                        StockProyecto.objects.create(producto=producto, proyecto_id=pid, cantidad=correcto)
                    cambios += 1
                elif sp.cantidad != correcto:
                    self.stdout.write(
                        f'  prod={producto.nombre} proj_id={pid}: '
                        f'actual={sp.cantidad} -> correcto={correcto}'
                    )
                    if not dry_run:
                        StockProyecto.objects.filter(pk=sp.pk).update(cantidad=correcto)
                    cambios += 1

        self.stdout.write(f'  {cambios} registro(s) de StockProyecto corregido(s).')
