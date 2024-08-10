from sqlalchemy import create_engine, text
from app.config import Config

class ArticuloService:
    def __init__(self):
        self.connection_string = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.connection = None
        self.foreign_keys = None

    def open_connection(self):
        try:
            self.connection = self.connection_string.connect()
            return self.connection
        except Exception as e:
            print("Error abriendo la conexion: ", e)

    def close_connection(self):
        if self.connection:
            self.connection.close()

    def get_foreign_keys(self,conn):
        try:
            query = text(f"SELECT f.name AS nombre_restriccion, OBJECT_NAME(f.parent_object_id) AS tabla_principal, OBJECT_NAME(f.referenced_object_id) AS tabla_secundaria, OBJECT_DEFINITION(f.object_id) AS constraint_definition FROM sys.foreign_keys AS f INNER JOIN sys.foreign_key_columns AS fc ON f.object_id = fc.constraint_object_id WHERE OBJECT_NAME(fc.referenced_object_id) = 'tbMaestroArticulo' AND COL_NAME(fc.parent_object_id, fc.parent_column_id) = 'IDArticulo'")
            result = conn.execute(query).fetchall()
            self.foreign_keys = result
            return result
        except Exception as e:
            print("Error en la consulta: ", e)
            if conn:
                conn.close()

    def update_id_articulo(self, old_id_articulo, new_id_articulo, conn):
        try:
            # Actualizar las tablas secundarias
            if self.foreign_keys:
                for fk in self.foreign_keys:
                    constraint_name = fk[0]
                    tabla_principal = fk[1]
                    tabla_secundaria = fk[2]

                    query_update_secondary = text(
                            f"UPDATE {tabla_principal} SET IDArticulo = '{new_id_articulo}' WHERE IDArticulo = '{old_id_articulo}'")
                    conn.execute(query_update_secondary)
                # Realizar la actualización en la tabla principal
                query_update_estructura = text(
                    f"UPDATE tbEstructura SET IDComponente = '{new_id_articulo}' WHERE IDComponente = '{old_id_articulo}'")
                query_update_tbOFControlEstructura = text(
                    f"UPDATE tbOFControlEstructura SET IDComponente = '{new_id_articulo}' WHERE IDComponente = '{old_id_articulo}'")
                query_update_ordenEstructura = text(
                    f"UPDATE tbOrdenEstructura SET IDComponente = '{new_id_articulo}' WHERE IDComponente = '{old_id_articulo}'")
                query_update_main = text(
                    f"UPDATE tbMaestroArticulo SET IDArticulo = '{new_id_articulo}' WHERE IDArticulo = '{old_id_articulo}'")
                query_update_tbHistoricoCosteMaterial = text(f"UPDATE tbHistoricoCosteMaterial SET IDArticuloPadre = '{new_id_articulo}' WHERE IDArticuloPadre = '{old_id_articulo}'")
                query_update_tbHistoricoCosteOperacion = text(f"UPDATE tbHistoricoCosteOperacion SET IDArticuloPadre = '{new_id_articulo}' WHERE IDArticuloPadre = '{old_id_articulo}'")
                query_update_tbHistoricoCosteVarios = text(f"UPDATE tbHistoricoCosteVarios SET IDArticuloPadre = '{new_id_articulo}' WHERE IDArticuloPadre = '{old_id_articulo}'")
                conn.execute(query_update_estructura)
                conn.execute(query_update_tbOFControlEstructura)
                conn.execute(query_update_ordenEstructura)
                conn.execute(query_update_main)
                conn.execute(query_update_tbHistoricoCosteMaterial)
                conn.execute(query_update_tbHistoricoCosteOperacion)
                conn.execute(query_update_tbHistoricoCosteVarios)

                conn.commit()

                self.enable_all_foreign_keys()
        except Exception as e:
            print("Error al actualizar el campo IDArticulo: ", e)
            if conn:
                conn.rollback()
                self.close_conn()

    def disable_all_foreign_keys(self,conn):
        try:
            for fk in self.get_foreign_keys(conn):
                query = text(f"ALTER TABLE {fk[1]} NOCHECK CONSTRAINT {fk[0]}")
                conn.execute(query)
                conn.commit()
            self.disable_foreign_key_rest()
        except Exception as e:
            print("Error al desactivar las restricciones de clave externa: ", e)
            if conn:
                conn.rollback()

    def disable_foreign_key_rest(self, conn):
        try:
            tbEstructura = text(f"ALTER TABLE [dbo].[tbEstructura] NOCHECK CONSTRAINT [FK_tbEstructura_tbArticuloEstructura]")
            tbEstructura_IDComponente = text(                    f"ALTER TABLE [dbo].[tbEstructura] NOCHECK CONSTRAINT [FK_tbEstructura_tbMaestroArticulo]")
            tbRuta = text(
                    f"ALTER TABLE [dbo].[tbRuta] NOCHECK CONSTRAINT [FK_tbRuta_tbArticuloRuta]")
            tbHistoricoMovimiento = text(
                    f"ALTER TABLE [dbo].[tbHistoricoMovimiento] NOCHECK CONSTRAINT [FK_tbHistoricoMovimiento_tbMaestroArticuloAlmacen]")
            tbOrdenEstructura = text(
                    f"ALTER TABLE [dbo].[tbOrdenEstructura] NOCHECK CONSTRAINT [FK_tbOrdenEstructura_tbMaestroArticulo]")
            tbOFControlEstructura = text(
                    f"ALTER TABLE [dbo].[tbOFControlEstructura] NOCHECK CONSTRAINT [FK_tbOFControlEstructura_tbMaestroArticulo]")
            tbArticuloClienteLinea = text(
                    f"ALTER TABLE [dbo].[tbArticuloClienteLinea] NOCHECK CONSTRAINT [FK_tbArticuloClienteLinea_tbArticuloCliente]")
            tbArticuloProveedorLinea = text(
                    f"ALTER TABLE [dbo].[tbArticuloProveedorLinea] NOCHECK CONSTRAINT [FK_tbArticuloProveedorLinea_tbArticuloProveedor]")
            tbHistoricoCosteMaterial = text(f"ALTER TABLE [dbo].[tbHistoricoCosteMaterial] NOCHECK CONSTRAINT [FK_tbHistoricoCosteMaterial_tbArticuloCosteEstandar]")
            tbHistoricoCosteOperacion = text(f"ALTER TABLE [dbo].[tbHistoricoCosteOperacion] NOCHECK CONSTRAINT [FK_tbHistoricoCosteOperacion_tbArticuloCosteEstandar]")
            tbHistoricoCosteVarios = text(f"ALTER TABLE [dbo].[tbHistoricoCosteVarios] NOCHECK CONSTRAINT [FK_tbHistoricoCosteVarios_tbArticuloCosteEstandar]")
            tbHistoricoCosteVariosPadre = text(f"ALTER TABLE [dbo].[tbHistoricoCosteOperacion] NOCHECK CONSTRAINT [FK_tbHistoricoCosteOperacion_tbMaestroArticulo]")
            conn.execute(tbEstructura)
            conn.execute(tbEstructura_IDComponente)
            conn.execute(tbRuta)
            conn.execute(tbHistoricoMovimiento)
            conn.execute(tbOrdenEstructura)
            conn.execute(tbOFControlEstructura)
            conn.execute(tbArticuloClienteLinea)
            conn.execute(tbArticuloProveedorLinea)
            conn.execute(tbHistoricoCosteMaterial)
            conn.execute(tbHistoricoCosteOperacion)
            conn.execute(tbHistoricoCosteVarios)
            conn.execute(tbHistoricoCosteVariosPadre)
            conn.commit()
            print(f"Resto de restricciones desactivadas.")
        except Exception as e:
            print("Error al desactivar la restricción de clave externa: ", e)
            if conn:
                conn.rollback()

    def enable_all_foreign_keys(self):
        try:
            conn = self.open_connection()
            if conn:
                for fk in self.get_foreign_keys():
                    query = text(f"ALTER TABLE {fk[1]} CHECK CONSTRAINT {fk[0]}")
                    conn.execute(query)
                conn.commit()
        except Exception as e:
            print("Error al activar las restricciones de clave externa: ", e)
        finally:
            if conn:
                self.close_connection()
    
    def autocomplete(self, search):
        conn = self.open_connection()
        query = text("SELECT TOP 10 IDArticulo, DescArticulo FROM tbMaestroArticulo WHERE IDArticulo LIKE :search")
        result = conn.execute(query, {'search': f'%{search}%'}).fetchall()
        articles = [{'IDArticulo': row[0], 'DescArticulo': row[1]} for row in result]
        conn.close()
        return articles
