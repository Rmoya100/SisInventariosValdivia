from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_transferencia_usuario_recibe'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                PRAGMA foreign_keys=OFF;

                ALTER TABLE inventory_detalleingreso RENAME TO old_inventory_detalleingreso;
                ALTER TABLE inventory_detallecompra RENAME TO old_inventory_detallecompra;
                ALTER TABLE inventory_ingreso RENAME TO old_inventory_ingreso;

                CREATE TABLE inventory_ingreso (
                    numIngreso integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    fecha date NOT NULL,
                    tipo_documento varchar(100) NOT NULL,
                    num_documento varchar(100) NOT NULL,
                    orden_compra_id integer NOT NULL REFERENCES inventory_ordencompra(idCompra) DEFERRABLE INITIALLY DEFERRED,
                    proyecto_id integer NULL REFERENCES inventory_proyecto(idProyecto) DEFERRABLE INITIALLY DEFERRED
                );
                CREATE TABLE inventory_detalleingreso (
                    idDetalle integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    cantidad integer NOT NULL,
                    precio decimal NOT NULL,
                    subtotal decimal NOT NULL,
                    ingreso_id integer NOT NULL REFERENCES inventory_ingreso(numIngreso) DEFERRABLE INITIALLY DEFERRED,
                    producto_id integer NOT NULL REFERENCES inventory_producto(cod_prod) DEFERRABLE INITIALLY DEFERRED
                );
                CREATE TABLE inventory_detallecompra (
                    idDetalle integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    cantidad integer NOT NULL,
                    precio decimal NOT NULL,
                    subtotal decimal NOT NULL,
                    orden_compra_id integer NOT NULL REFERENCES inventory_ordencompra(idCompra) DEFERRABLE INITIALLY DEFERRED,
                    producto_id integer NOT NULL REFERENCES inventory_producto(cod_prod) DEFERRABLE INITIALLY DEFERRED
                );

                INSERT INTO inventory_ingreso (numIngreso, fecha, tipo_documento, num_documento, orden_compra_id, proyecto_id)
                SELECT numIngreso, fecha, tipo_documento, num_documento, orden_compra_id, proyecto_id FROM old_inventory_ingreso;
                INSERT INTO inventory_detalleingreso (idDetalle, cantidad, precio, subtotal, ingreso_id, producto_id)
                SELECT idDetalle, cantidad, precio, subtotal, ingreso_id, producto_id FROM old_inventory_detalleingreso;
                INSERT INTO inventory_detallecompra (idDetalle, cantidad, precio, subtotal, orden_compra_id, producto_id)
                SELECT idDetalle, cantidad, precio, subtotal, orden_compra_id, producto_id FROM old_inventory_detallecompra;

                DROP TABLE old_inventory_detalleingreso;
                DROP TABLE old_inventory_detallecompra;
                DROP TABLE old_inventory_ingreso;

                PRAGMA foreign_keys=ON;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

    def apply(self, project_state, schema_editor, collect_sql=False):
        if schema_editor.connection.vendor == 'sqlite':
            return super().apply(project_state, schema_editor, collect_sql)
        return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        if schema_editor.connection.vendor == 'sqlite':
            return super().unapply(project_state, schema_editor, collect_sql)
        return project_state


