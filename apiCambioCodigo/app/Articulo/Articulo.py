from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from flask_cors import CORS
import json
from typing import List, Dict, Any

# app = Flask(__name__)
# CORS(app)

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
        self.tb_auto_nu_orden = None

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
                tbHistoricoCosteMaterial = text(f"ALTER TABLE [dbo].[tbHistoricoCosteMaterial] CHECK CONSTRAINT [FK_tbHistoricoCosteMaterial_tbArticuloCosteEstandar]")
                tbHistoricoCosteOperacion = text(f"ALTER TABLE [dbo].[tbHistoricoCosteOperacion] CHECK CONSTRAINT [FK_tbHistoricoCosteOperacion_tbArticuloCosteEstandar]")
                tbHistoricoCosteVarios = text(f"ALTER TABLE [dbo].[tbHistoricoCosteVarios] CHECK CONSTRAINT [FK_tbHistoricoCosteVarios_tbArticuloCosteEstandar]")
                tbHistoricoCosteVariosPadre = text(f"ALTER TABLE [dbo].[tbHistoricoCosteOperacion] CHECK CONSTRAINT [FK_tbHistoricoCosteOperacion_tbMaestroArticulo]")
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

    def autocomplete(self, search):
        conn = self.Open_Conn_Solmicro()
        query = text("SELECT TOP 10 IDArticulo, DescArticulo FROM tbMaestroArticulo WHERE IDArticulo LIKE :search")
        result = conn.execute(query, {'search': f'%{search}%'}).fetchall()
        articles = [{'IDArticulo': row[0], 'DescArticulo': row[1]} for row in result]
        conn.close()
        return articles

    def autocomplete2(self, search):
        script = text("SELECT TOP 10 [of].IDArticulo, [of].QFabricar,[of].NOrden, [of].Estado FROM tbOrdenFabricacion [of] WHERE [of].NOrden LIKE :search")
        conn = self.connection_string_solmicro.connect()
        result = conn.execute(script,{'search':f'%{search}%'}).fetchall()
        conn.close()
        return [{'IDArticulo':row[0],'QFabricar':row[1],'NOrden':row[2]} for row in result]
    
    from typing import List, Dict, Any

    def result_to_dicts(selft,column_names: List[str], query_result: List[tuple]) -> List[Dict[str, Any]]:   
        return [dict(zip(column_names, row)) for row in query_result]


    def getArticulos(self,listaIDs):
        conn = self.connection_string_solmicro.connect()
        result = []
        for row in listaIDs:
            script = text(f"SELECT ma.IDArticulo FROM tbMaestroArticulo ma WHERE ma.IDArticulo=N'{row}'")
            print(script)
            response = conn.execute(script).fetchall()
            for r in response:
                result.append(r)
        conn.close()
        return [{'IDArticulo':row[0]} for row in result]
    
    def _restaurar_sp(self):
        restaurar_sp_query = text(""" ALTER PROCEDURE [dbo].[xAutoNumericValue]
        AS
        BEGIN
            DECLARE @Valor INT

            INSERT INTO xAutoNumeric (Valor)
            VALUES (0)

            SET @Valor = @@IDENTITY

            --INSERT INTO ale_autoNumber (autonumber)
            --VALUES (@Valor)
            
            DELETE FROM xAutoNumeric
            WHERE ID = @Valor
            SELECT @Valor AS value
        END """)

        borrar_datos_query = text("DELETE FROM   ale_autoNumber")
        self.connection.execute(restaurar_sp_query)
        self.connection.execute(borrar_datos_query)
        self.connection.commit()

    def _modificar_sp(self):
        modificar_sp_query = text(""" ALTER PROCEDURE [dbo].[xAutoNumericValue]
        AS
        BEGIN
            DECLARE @Valor INT

            INSERT INTO xAutoNumeric (Valor)
            VALUES (0)

            SET @Valor = @@IDENTITY

            INSERT INTO ale_autoNumber (autonumber)
            VALUES (@Valor)
            
            DELETE FROM xAutoNumeric
            WHERE ID = @Valor
            SELECT @Valor AS value
        END """)
        self.connection.execute(modificar_sp_query)
        self.connection.commit()
    
    def _obtener_contador(self):
        query = text("SELECT mc.Texto, mc.Contador FROM tbMaestroContador mc WHERE mc.IDContador= N'OFF'")
        result = self.connection.execute(query).fetchall()
        texto, contador = result[0][0], int(result[0][1]) + 1
        n_orden = texto + str(contador)
        return contador, n_orden
    
    def _actualizar_contador(self, contador_of):
        query = text(f"UPDATE tbMaestroContador SET Contador={contador_of}, FechaModificacionAudi='20240810 14:03:13.112', UsuarioAudi=N'favram\\a.obregon' WHERE IDContador=N'OFF'")
        self.connection.execute(query)
        self.connection.commit()

    def _obtener_datos_articulo(self, rows):
        id_articulo = rows[0][1]
        q_fabrica = rows[0][4]
        q_buenas = rows[0][5]
        return id_articulo, q_fabrica, q_buenas   
    
    def _obtener_revision(self, id_articulo):
        query = text(f"SELECT ma.NivelModificacionPlan FROM tbMaestroArticulo ma WHERE ma.IDArticulo = N'{id_articulo}'")
        result = self.connection.execute(query).fetchall()
        return result[0][0]
    
    def _obtener_estructura(self, id_articulo, rows):
        secuencias = [row[2] for row in rows]
        secuencias_str = ', '.join(map(str, secuencias))
        query = text(f"SELECT e.IDComponente, e.Cantidad, e.Merma, e.Secuencia, e.IDEstrComp, e.IDUdMedidaProduccion, e.Factor, e.CantidadProduccion FROM tbEstructura e WHERE e.IDArticulo = N'{id_articulo}' AND e.IDEstructura = N'01' AND e.Secuencia IN ({secuencias_str})")
        result = self.connection.execute(query).fetchall()
        columns = ["IDComponente", "Cantidad", "Merma", "Secuencia", "IDEstrComp", "IDUdMedidaProduccion", "Factor", "CantidadProduccion"]
        return [dict(zip(columns, row)) for row in result]

    def _get_value_autonumerico(self):
        queryAutonumeric = text("EXEC dbo.xAutoNumericValue")
        self.connection.execute(queryAutonumeric)
        queryGetValueAutonumeric = text("SELECT MAX(an.autonumber) AS Valor FROM ale_autoNumber an")
        resultValueAutonumeric = self.connection.execute(queryGetValueAutonumeric).fetchall()
        return resultValueAutonumeric[0][0]

    def _insertar_cabecera_of(self, n_orden, id_articulo, q_fabrica, revision):
        self.tb_auto_nu_orden = self._get_value_autonumerico()
        query = text(f"""INSERT INTO tbOrdenFabricacion (IDOrden, NOrden, IDContador, IDArticulo, FechaCreacion, IDCentroGestion, QFabricar, Estado, FechaInicio, FechaFin, IDAlmacen, IDEstructura, IDRuta, FechaInicioProg, FechaFinProg, ParamMaterial, ParamTerminado, NivelPlano, Reproceso, FechaCreacionAudi, FechaModificacionAudi, UsuarioAudi, UsuarioCreacionAudi)
                        VALUES ({self.tb_auto_nu_orden}, N'{n_orden}', N'OFF', N'{id_articulo}', '20240810 00:00:00.000', N'1', {q_fabrica}, 2, '20240810 00:00:00.000', '20240901 00:00:00.000', N'0', N'01', N'01', '20240810 07:00:00.000', '20240901 08:51:19.000', 3, 1, N'{revision}', 0, '20240810 14:03:13.292', '20240810 14:03:13.292', N'favram\\a.obregon', N'favram\\a.obregon')""")
        self.connection.execute(query)
        self.connection.commit()

    def _insertar_orden_estructura(self, n_orden, item, q_fabrica, q_buenas):
        auto_num_id_estructura = self._get_value_autonumerico()
        query = text(f"""INSERT INTO tbOrdenEstructura (IDOrdenEstructura, IDOrden, IDComponente, NOrden, Cantidad, Merma, Secuencia, QNecesaria, QConsumida, IDAlmacen, IDEstrComp, IDUdMedidaProduccion, Factor, CantidadProduccion, RamaExplosionOF, FechaCreacionAudi, FechaModificacionAudi, UsuarioAudi, UsuarioCreacionAudi)
                        VALUES ({auto_num_id_estructura}, {self.tb_auto_nu_orden}, N'{item["IDComponente"]}', N'{n_orden}', {item["Cantidad"]}, {item["Merma"]}, {item["Secuencia"]}, {item["Cantidad"] * q_fabrica}, {q_buenas * item["Cantidad"]}, N'0', {item["IDEstrComp"]}, N'{item["IDUdMedidaProduccion"]}', {item["Factor"]}, {item["CantidadProduccion"]}, N'{self.tb_auto_nu_orden}\\{auto_num_id_estructura}', '20240810 14:03:13.294', '20240810 14:03:13.294', N'favram\\a.obregon', N'favram\\a.obregon')""")
        self.connection.execute(query)
        self.connection.commit()

    def _procesar_ruta(self, id_articulo, n_orden, rows):
        for row in rows:
            query = text(f"SELECT r.IDRutaOp, r.IDOperacion,r.DescOperacion, r.IDCentro,r.FactorHombre, r.TiempoPrep,r.UdTiempoPrep, r.TiempoEjecUnit,r.UdTiempoEjec, r.CantidadTiempo, r.UdTiempo,r.IDUdProduccion, r.FactorProduccion,r.ControlProduccion,r.TiempoCiclo,r.UdTiempoCiclo,r.LoteCiclo,r.PlazoSub,r.UdTiempoPlazo,r.SolapePor, r.Ciclo, r.Rendimiento, r.CantidadTiempo100, r.SolapeLote, r.Secuencia FROM tbRuta r WHERE r.IDArticulo = N'{id_articulo}' AND r.IDRuta = N'01' and r.Secuencia = {row[2]}")                
            result = self.connection.execute(query).fetchall()
            if result:
                columnRuta = ["IDRutaOp","IDOperacion","DescOperacion","IDCentro","FactorHombre","TiempoPrep","UdTiempoPrep","TiempoEjecUnit","UdTiempoEjec","CantidadTiempo","UdTiempo","IDUdProduccion","FactorProduccion", "ControlProduccion","TiempoCiclo","UdTiempoCiclo","LoteCiclo","PlazoSub","UdTiempoPlazo","SolapePor","Ciclo", "Rendimiento","CantidadTiempo100","SolapeLote","Secuencia"]
                tbRuta = self.result_to_dicts(columnRuta,result)
                item = tbRuta[0]
                auto_num_id_ruta = self._get_value_autonumerico()
                queryInsertTbOrdenRuta = text(f"""INSERT INTO tbOrdenRuta ([IDOrdenRuta], [IDRutaOp], [IDOrden], [NOrden], [TipoOperacion], [IDOperacion], [DescOperacion], [Critica], [IDCentro], [FactorHombre], [TiempoPrep], [UdTiempoPrep], [TiempoEjecUnit], [UdTiempoEjec], [CantidadTiempo], [UdTiempo], [IDUdProduccion], [QBuena], [QRechazada], [FactorProduccion], [ControlProduccion], [FechaInicio], [FechaFin], [QFabricar], [TiempoCiclo], [UdTiempoCiclo], [LoteCiclo], [PlazoSub], [UdTiempoPlazo], [SolapePor], [Ciclo], [QDudosa], [Rendimiento], [CantidadTiempo100], [SolapeLote], [Secuencia], [FechaCreacionAudi], [FechaModificacionAudi], [UsuarioAudi], [UsuarioCreacionAudi])
VALUES ({auto_num_id_ruta}, {item["IDRutaOp"]}, {self.tb_auto_nu_orden}, N'{n_orden}', 0, N'{item["IDOperacion"]}', N'{item["DescOperacion"]}', 0, N'{item["IDCentro"]}', {item["FactorHombre"]}, {item["TiempoPrep"]}, {item["UdTiempoPrep"]}, {item["TiempoEjecUnit"]}, {item["UdTiempoEjec"]}, {item["CantidadTiempo"]}, {item["UdTiempo"]}, N'{item["IDUdProduccion"]}', {row[5]}, 0, {item["FactorProduccion"]}, {item["ControlProduccion"]}, '20240810 07:00:00.000', '20240810 07:00:05.000', {row[4]}, {item["TiempoCiclo"]}, {item["UdTiempoCiclo"]}, {item["LoteCiclo"]}, {item["PlazoSub"]}, {item["UdTiempoPlazo"]}, {item["SolapePor"]}, 0, 0, {item["Rendimiento"]}, {item["CantidadTiempo100"]}, {item["SolapeLote"]}, {item["Secuencia"]}, '20240810 14:03:13.309', '20240810 14:03:13.309', N'favram\\a.obregon', N'favram\\a.obregon')""")
                self.connection.execute(queryInsertTbOrdenRuta)
                self.connection.commit()

    def _process_lanzamiento(self, rows):
        contador_of, n_orden = self._obtener_contador()
        id_articulo, q_fabrica, q_buenas = self._obtener_datos_articulo(rows)
        revision = self._obtener_revision(id_articulo)

        self._insertar_cabecera_of(n_orden, id_articulo, q_fabrica, revision)
        self._actualizar_contador(contador_of)

        tb_estructura = self._obtener_estructura(id_articulo, rows)
        for item in tb_estructura:
            self._insertar_orden_estructura(n_orden, item, q_fabrica, q_buenas)

        self._procesar_ruta(id_articulo, n_orden, rows)

    def generate_of(self,listaArticulo):
        try:
            self.connection = self.connection_string_solmicro.connect()
            self._modificar_sp()
            for lanzamiento, rows in listaArticulo.items():
                self._process_lanzamiento(rows)
            self._restaurar_sp()
        except Exception as e:
            print("Error al activar las restricciones de clave externa: ", e)
        finally:
            self.connection.close()            

    
        

# @app.route('/recoding_articulo', methods=['POST'])
# def update_articulo():
#     data = request.json
#     old_id_articulo = data.get('old_id_articulo')
#     new_id_articulo = data.get('new_id_articulo')
#     print(old_id_articulo)
#     print(new_id_articulo)
    
#     if not old_id_articulo or not new_id_articulo:
#         return jsonify({"error": "old_id_articulo and new_id_articulo are required"}), 400
    
#     articulo = Articulo()
    
#     try:
#         articulo.disable_all_foreign_keys()
#         articulo.update_id_articulo(old_id_articulo, new_id_articulo)
#         articulo.enable_all_foreign_keys()
#         return jsonify({"status": "success"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
