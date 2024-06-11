from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import json

app = Flask(__name__)


class Articulo:
    def __init__(self):
        self.server_solmicro = r'srvsql'
        # self.database_solmicro = 'SolmicroERP6_Favram_Pruebas'
        self.database_solmicro = 'SolmicroERP6_Favram'
        self.username_solmicro = 'sa'
        self.password_solmicro = 'Altai2021'
        self.connection_string_solmicro = create_engine(
            f'mssql+pyodbc://{self.username_solmicro}:{self.password_solmicro}@{self.server_solmicro}/{self.database_solmicro}?driver=SQL+Server')
        self.connection = None
        self.old_id_articulo = None
        self.foreign_keys = None

    def Open_Conn_Solmicro(self):
        try:
            self.connection = self.connection_string_solmicro.connect()
            return self.connection
        except Exception as e:
            print("Error opening connection: ", e)

    def close_conn(self):
        if self.connection:
            self.connection.close()

    def get_foreign_keys(self):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                query = text(f"SELECT f.name AS nombre_restriccion, OBJECT_NAME(f.parent_object_id) AS tabla_principal, OBJECT_NAME(f.referenced_object_id) AS tabla_secundaria, OBJECT_DEFINITION(f.object_id) AS constraint_definition FROM sys.foreign_keys AS f INNER JOIN sys.foreign_key_columns AS fc ON f.object_id = fc.constraint_object_id WHERE OBJECT_NAME(fc.referenced_object_id) = 'tbMaestroArticulo' AND COL_NAME(fc.parent_object_id, fc.parent_column_id) = 'IDArticulo'")
                result = conn.execute(query).fetchall()
                self.foreign_keys = result
                conn.close()
                return result
        except Exception as e:
            print("Error en la consulta: ", e)
            if conn:
                conn.close()

    def update_id_articulo(self, old_id_articulo, new_id_articulo):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
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
                conn.execute(query_update_estructura)
                conn.execute(query_update_tbOFControlEstructura)
                conn.execute(query_update_ordenEstructura)
                conn.execute(query_update_main)

                conn.commit()
                self.close_conn()
        except Exception as e:
            print("Error al actualizar el campo IDArticulo: ", e)
            if conn:
                conn.rollback()
                self.close_conn()

    def disable_foreign_key(self, table_name, constraint_name):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                query = text(
                    f"ALTER TABLE {table_name} NOCHECK CONSTRAINT {constraint_name}")
                conn.execute(query)
                conn.commit()
                # print(f"Restricción {constraint_name} en {table_name} desactivada.")
        except Exception as e:
            print("Error al desactivar la restricción de clave externa: ", e)
            if conn:
                conn.rollback()

    def disable_foreign_key_rest(self):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                tbEstructura = text(
                    f"ALTER TABLE [dbo].[tbEstructura] NOCHECK CONSTRAINT [FK_tbEstructura_tbArticuloEstructura]")
                tbEstructura_IDComponente = text(
                    f"ALTER TABLE [dbo].[tbEstructura] NOCHECK CONSTRAINT [FK_tbEstructura_tbMaestroArticulo]")
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
                conn.execute(tbEstructura)
                conn.execute(tbEstructura_IDComponente)
                conn.execute(tbRuta)
                conn.execute(tbHistoricoMovimiento)
                conn.execute(tbOrdenEstructura)
                conn.execute(tbOFControlEstructura)
                conn.execute(tbArticuloClienteLinea)
                conn.execute(tbArticuloProveedorLinea)
                conn.commit()
                print(f"Resto de restricciones desactivadas.")
        except Exception as e:
            print("Error al desactivar la restricción de clave externa: ", e)
            if conn:
                conn.rollback()

    def enable_foreign_key(self, table_name, constraint_name):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                query = text(
                    f"ALTER TABLE {table_name} CHECK CONSTRAINT {constraint_name}")
                conn.execute(query)
                conn.commit()
                # print(f"Restricción {constraint_name} en {table_name} activada.")
        except Exception as e:
            print("Error al activar la restricción de clave externa: ", e)
            if conn:
                conn.rollback()

    def enable_foreign_key_rest(self):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                tbEstructura = text(
                    f"ALTER TABLE [dbo].[tbEstructura] CHECK CONSTRAINT [FK_tbEstructura_tbArticuloEstructura]")
                tbEstructura_IDComponente = text(
                    f"ALTER TABLE [dbo].[tbEstructura] NOCHECK CONSTRAINT [FK_tbEstructura_tbMaestroArticulo]")
                tbRuta = text(
                    f"ALTER TABLE [dbo].[tbRuta] CHECK CONSTRAINT [FK_tbRuta_tbArticuloRuta]")
                tbHistoricoMovimiento = text(
                    f"ALTER TABLE [dbo].[tbHistoricoMovimiento] CHECK CONSTRAINT [FK_tbHistoricoMovimiento_tbMaestroArticuloAlmacen]")
                tbOrdenEstructura = text(
                    f"ALTER TABLE [dbo].[tbOrdenEstructura] CHECK CONSTRAINT [FK_tbOrdenEstructura_tbMaestroArticulo]")
                tbOFControlEstructura = text(
                    f"ALTER TABLE [dbo].[tbOFControlEstructura] CHECK CONSTRAINT [FK_tbOFControlEstructura_tbMaestroArticulo]")
                tbArticuloClienteLinea = text(
                    f"ALTER TABLE [dbo].[tbArticuloClienteLinea] CHECK CONSTRAINT [FK_tbArticuloClienteLinea_tbArticuloCliente]")
                tbArticuloProveedorLinea = text(
                    f"ALTER TABLE [dbo].[tbArticuloProveedorLinea] CHECK CONSTRAINT [FK_tbArticuloProveedorLinea_tbArticuloProveedor]")
                conn.execute(tbEstructura)
                conn.execute(tbEstructura_IDComponente)
                conn.execute(tbRuta)
                conn.execute(tbHistoricoMovimiento)
                conn.execute(tbOrdenEstructura)
                conn.execute(tbOFControlEstructura)
                conn.execute(tbArticuloClienteLinea)
                conn.execute(tbArticuloProveedorLinea)
                conn.commit()
                # print(f"Resto de restricciones activadas.")
        except Exception as e:
            print("Error al activar la restricción de clave externa: ", e)
            if conn:
                conn.rollback()

    def disable_all_foreign_keys(self):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                for fk in self.get_foreign_keys():
                    constraint_name = fk[0]
                    table_name = fk[1]
                    self.disable_foreign_key(table_name, constraint_name)
                self.disable_foreign_key_rest()
        except Exception as e:
            print("Error al desactivar las restricciones de clave externa: ", e)
        finally:
            if conn:
                self.close_conn()

    def enable_all_foreign_keys(self):
        try:
            conn = self.Open_Conn_Solmicro()
            if conn:
                for fk in self.get_foreign_keys():
                    constraint_name = fk[0]
                    table_name = fk[1]
                    self.enable_foreign_key(table_name, constraint_name)
                self.enable_foreign_key_rest()
        except Exception as e:
            print("Error al activar las restricciones de clave externa: ", e)
        finally:
            if conn:
                self.close_conn()



@app.route('/recoding_articulo', methods=['POST'])
def update_articulo():
    data = request.json
    old_id_articulo = data.get('old_id_articulo')
    new_id_articulo = data.get('new_id_articulo')
    print(old_id_articulo)
    print(new_id_articulo)
    
    if not old_id_articulo or not new_id_articulo:
        return jsonify({"error": "old_id_articulo and new_id_articulo are required"}), 400
    
    articulo = Articulo()
    
    try:
        articulo.disable_all_foreign_keys()
        articulo.update_id_articulo(old_id_articulo, new_id_articulo)
        articulo.enable_all_foreign_keys()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
