from flask import Flask, request, jsonify
import pyodbc, struct
from sqlalchemy import create_engine, text
from flask_cors import CORS
import json
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

# app = Flask(__name__)
# CORS(app)

class Articulo:
    def __init__(self):
        self.server_solmicro = r'srvsql'
        self.server_industry = r'SERVIDOR'
        # self.database_solmicro = 'SolmicroERP6_Favram_Pruebas'
        self.database_solmicro = 'SolmicroERP6_Favram'
        self.database_industry = 'IPFavram'
        self.usernameDB = 'sa'
        self.password_solmicro = 'Altai2021'
        self.password_industry = '71zl6p9h'
        self.connection_string_solmicro = create_engine(f'mssql+pyodbc://{self.usernameDB}:{self.password_solmicro}@{self.server_solmicro}/{self.database_solmicro}?driver=SQL+Server')
        self.connection_string_Industry = (f"DRIVER={{SQL Server}};"f"SERVER={self.server_industry};"f"DATABASE={self.database_industry};"f"UID={self.usernameDB};"f"PWD={self.password_industry};") 
        self.connection = None
        self.connection_industry = None
        self.old_id_articulo = None
        self.foreign_keys = None
        self.tb_auto_nu_orden = None
        self.query_tfarbfase_industry = f'select Lanzamiento,Articulo,Fase,Descripcion,CantidadFabricar,CantidadFabricada,FechaInicioFabricacion,FechaPrevistaFinal,MaquinaAsignada,Centro,NULL as Resultado from TFabrfase where CantidadFabricar<> CantidadFabricada ORDER BY Lanzamiento ASC'

    def Open_Conn_Solmicro(self):
        try:
            self.connection = self.connection_string_solmicro.connect()
            return self.connection
        except Exception as e:
            print("Error opening connection: ", e)
    
    def get_conn_insdutry(self):
        conn = pyodbc.connect(self.connection_string_Industry)
        return conn   
    
    def get_TFarbfase_industry(self):
        Listrows_group = {} 
        with self.get_conn_insdutry() as conn:
            cursor = conn.cursor()
            cursor.execute(self.query_tfarbfase_industry)
            for row in cursor.fetchall():
                lanzamiento = row.Lanzamiento
                idArticulo = row.Articulo
                if lanzamiento not in Listrows_group:
                    Listrows_group[lanzamiento] = {}
                if idArticulo not in Listrows_group[lanzamiento]:
                    Listrows_group[lanzamiento][idArticulo] = []
                Listrows_group[lanzamiento][idArticulo].append(row)
        return Listrows_group



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
            script = text(f"SELECT ma.IDArticulo FROM tbMaestroArticulo ma WHERE ma.IDArticulo=N'{str(row)}'")
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
                        VALUES ({auto_num_id_estructura}, {self.tb_auto_nu_orden}, N'{item["IDComponente"]}', N'{n_orden}', {item["Cantidad"]}, {float(item["Merma"])}, {int(item["Secuencia"])}, {float(item["Cantidad"]) * float(q_fabrica)}, {float(q_buenas) * float(item["Cantidad"])}, N'0', {item["IDEstrComp"]}, N'{item["IDUdMedidaProduccion"]}', {item["Factor"]}, {item["CantidadProduccion"]}, N'{self.tb_auto_nu_orden}\\{auto_num_id_estructura}', '20240810 14:03:13.294', '20240810 14:03:13.294', N'favram\\a.obregon', N'favram\\a.obregon')""")
        self.connection.execute(query)
        self.connection.commit()

    def _check_ruta(self,id_articulo,row):
        query = text(f"SELECT count(*) as count FROM tbRuta r WHERE r.IDArticulo = N'{id_articulo}' AND r.IDRuta = N'01' and r.Secuencia = {int(row[2])}")                
        result = self.connection.execute(query).fetchall()
        return result[0] is not None

    def _procesar_ruta(self, id_articulo, n_orden, rows):
        for row in rows:
            query = text(f"SELECT r.IDRutaOp, r.IDOperacion,r.DescOperacion, r.IDCentro,r.FactorHombre, r.TiempoPrep,r.UdTiempoPrep, r.TiempoEjecUnit,r.UdTiempoEjec, r.CantidadTiempo, r.UdTiempo,r.IDUdProduccion, r.FactorProduccion,r.ControlProduccion,r.TiempoCiclo,r.UdTiempoCiclo,r.LoteCiclo,r.PlazoSub,r.UdTiempoPlazo,r.SolapePor, r.Ciclo, r.Rendimiento, r.CantidadTiempo100, r.SolapeLote, r.Secuencia, r.TipoOperacion FROM tbRuta r WHERE r.IDArticulo = N'{id_articulo}' AND r.IDRuta = N'01' and r.Secuencia = {row[2]}")                
            result = self.connection.execute(query).fetchall()
            if result:
                columnRuta = ["IDRutaOp","IDOperacion","DescOperacion","IDCentro","FactorHombre","TiempoPrep","UdTiempoPrep","TiempoEjecUnit","UdTiempoEjec","CantidadTiempo","UdTiempo","IDUdProduccion","FactorProduccion", "ControlProduccion","TiempoCiclo","UdTiempoCiclo","LoteCiclo","PlazoSub","UdTiempoPlazo","SolapePor","Ciclo", "Rendimiento","CantidadTiempo100","SolapeLote","Secuencia","TipoOperacion"]
                tbRuta = self.result_to_dicts(columnRuta,result)
                item = tbRuta[0]
                auto_num_id_ruta = self._get_value_autonumerico()
                queryInsertTbOrdenRuta = text(f"""INSERT INTO tbOrdenRuta ([IDOrdenRuta], [IDRutaOp], [IDOrden], [NOrden], [TipoOperacion], [IDOperacion], [DescOperacion], [Critica], [IDCentro], [FactorHombre], [TiempoPrep], [UdTiempoPrep], [TiempoEjecUnit], [UdTiempoEjec], [CantidadTiempo], [UdTiempo], [IDUdProduccion], [QBuena], [QRechazada], [FactorProduccion], [ControlProduccion], [FechaInicio], [FechaFin], [QFabricar], [TiempoCiclo], [UdTiempoCiclo], [LoteCiclo], [PlazoSub], [UdTiempoPlazo], [SolapePor], [Ciclo], [QDudosa], [Rendimiento], [CantidadTiempo100], [SolapeLote], [Secuencia], [FechaCreacionAudi], [FechaModificacionAudi], [UsuarioAudi], [UsuarioCreacionAudi])
VALUES ({auto_num_id_ruta}, {item["IDRutaOp"]}, {self.tb_auto_nu_orden}, N'{n_orden}', {item["TipoOperacion"]}, N'{item["IDOperacion"]}', N'{item["DescOperacion"]}', 0, N'{item["IDCentro"]}', {item["FactorHombre"]}, {item["TiempoPrep"]}, {item["UdTiempoPrep"]}, {item["TiempoEjecUnit"]}, {item["UdTiempoEjec"]}, {item["CantidadTiempo"]}, {item["UdTiempo"]}, N'{item["IDUdProduccion"]}', {row[5]}, 0, {item["FactorProduccion"]}, {item["ControlProduccion"]}, '20240810 07:00:00.000', '20240810 07:00:05.000', {row[4]}, {item["TiempoCiclo"]}, {item["UdTiempoCiclo"]}, {item["LoteCiclo"]}, {item["PlazoSub"]}, {item["UdTiempoPlazo"]}, {item["SolapePor"]}, 0, 0, {item["Rendimiento"]}, {item["CantidadTiempo100"]}, {item["SolapeLote"]}, {item["Secuencia"]}, '20240810 14:03:13.309', '20240810 14:03:13.309', N'favram\\a.obregon', N'favram\\a.obregon')""")
                self.connection.execute(queryInsertTbOrdenRuta)
                self.connection.commit()

    def _process_lanzamiento(self, rows):
        id_articulo, q_fabrica, q_buenas = self._obtener_datos_articulo(rows)
        if not self._articulo_existe(id_articulo):
            # return {"status": "error", "message": "S/O"}
            return  "S/A"
        # for row in rows:
        #     result = self._check_ruta(id_articulo,row)
        #     if not result:
        #         return "S/F"

        contador_of, n_orden = self._obtener_contador()
        revision = self._obtener_revision(id_articulo)

        self._insertar_cabecera_of(n_orden, id_articulo, q_fabrica, revision)
        self._actualizar_contador(contador_of)

        tb_estructura = self._obtener_estructura(id_articulo, rows)
        for item in tb_estructura:
            self._insertar_orden_estructura(n_orden, item, q_fabrica, q_buenas)

        self._procesar_ruta(id_articulo, n_orden, rows)

        return n_orden

    def _articulo_existe(self, id_articulo):
        query_check_articulo = text(f"SELECT COUNT(*) as count FROM tbMaestroArticulo WHERE IDArticulo = N'{id_articulo}'")
        result = self.connection.execute(query_check_articulo).fetchone()
        return result[0] > 0

    def generate_of(self,):
        try:
            self.connection = self.connection_string_solmicro.connect()
            listaArticulo = self.get_TFarbfase_industry()
            self._modificar_sp()
            for lanzamiento, rows in listaArticulo.items():
                print(lanzamiento)
                print(rows)
                resultado = self._process_lanzamiento(rows)
                # if not resultado.get('status')== 'error':
                #     return resultado.get("message")
                # # Si ocurre un error, puedes hacer rollback aquí si es necesario
                #     self.connection.rollback()
                #     return {
                #     "status": "error",
                #     "message": f"Error processing batch {lanzamiento}: {resultado.get('message')}"
                #     }
            self._restaurar_sp()
            return {"status": "success", "message": f"{"resultado"}"}
        except Exception as e:
            print(f"Error en generate_of: {e}")
            self.connection.rollback()
            return {"status": "error", "message": "Internal Server Error"}
        finally:
            self.connection.commit()
            self.connection.close()            

    
    def getOrdenes(self,startDate=None, endDate=None):
        try:
            print(startDate, endDate)
            self.connection = self.connection_string_solmicro.connect()
            condiciones = []
            if startDate:
                # startDate = datetime.strftime(startDate, '%Y-%m-%d')
                condiciones.append(f"[Fecha Req Cliente] >= CONVERT(DATETIME,'{startDate}',102)")
            if endDate:
                # endDate = datetime.strftime(endDate, '%Y-%m-%d')
                condiciones.append(f"[Fecha Req Cliente] <= CONVERT(DATETIME,'{endDate}',102)")
            if startDate and endDate:
                query = f"SELECT IDArticulo, NOrden, NPedido, QPendiente, Fabricar, DescArticulo, TiempoEjecUnit, Tiempo, StockFisico, DescCentro, DescOperacion, Secuencia, Cliente, QPedida, [Fecha Req Cliente], IDSeccion, TIPO15085 FROM vCTLCISituacionFabricaCentro WHERE [Fecha Req Cliente] BETWEEN CONVERT(DATETIME,'{startDate}',102) AND CONVERT(DATETIME,'{endDate}',102)"
            else:
                query = "SELECT IDArticulo, NOrden, NPedido, QPendiente, Fabricar, DescArticulo, TiempoEjecUnit, Tiempo, StockFisico, DescCentro, DescOperacion, Secuencia, Cliente, QPedida, [Fecha Req Cliente], IDSeccion, TIPO15085 FROM vCTLCISituacionFabricaCentro"
                if condiciones:
                    query += " WHERE " + " AND ".join(condiciones)        
            resultado = self.connection.execute(text(query)).fetchall()
            
            # Agrupar los resultados por NOrden
            ordenes_agrupadas = []
            for row in resultado:
                row_dict = {
                    "IDArticulo": row[0],
                    "NOrden": row[1],
                    "NPedido": row[2],
                    "QPendiente": row[3],
                    "Fabricar": row[4],
                    "DescArticulo": row[5],
                    "TiempoEjecUnit": row[6],
                    "Tiempo": row[7],
                    "StockFisico": row[8],
                    "DescCentro": row[9],
                    "DescOperacion": row[10],
                    "Secuencia": row[11],
                    "Cliente": row[12],
                    "QPedida": row[13],
                    "Fecha Req Cliente": row[14],
                    "IDSeccion": row[15],
                    "TIPO15085": row[16]
                }
                ordenes_agrupadas.append(row_dict)
            # print(ordenes_agrupadas)
            return ordenes_agrupadas
        
        except Exception as e:
            print(f"Error en getOrdenes: {e}")
            return {"status": "error", "message": "Internal Server Error"}
        
        finally:
            # Cerrar la conexión
            if self.connection:
                self.connection.close() 
    
    def getSeccion(self):
        try:
            self.connection = self.connection_string_solmicro.connect()
            query = text("SELECT ms.IDSeccion, CASE WHEN ms.IDSeccion = 125 OR ms.IDSeccion = 126 THEN 'CALIDAD' WHEN ms.IDSeccion = 400 OR ms.IDSeccion = 450 OR ms.IDSeccion = 455 OR ms.IDSeccion = 500 THEN 'ALMACEN' else ms.DescSeccion END AS DescSeccion  FROM tbMaestroSeccion ms")
            resultado = self.connection.execute(query).fetchall()
            resultado_list = []
            for row in resultado:
                row_dict = {
                    "IDSeccion": row[0],
                    "DescSeccion": row[1]
                }
                resultado_list.append(row_dict)
            return resultado_list
        except Exception as e:
            print(f"Error en getOrdenes: {e}")
            return {"status": "error", "message": "Internal Server Error"}        
        finally:
            # Cerrar la conexión
            if self.connection:
                self.connection.close() 

    def procesarCapacidadTeorica(self,startDate,endDate):
        try:
            ordenes = self.getOrdenes(startDate,endDate)
            if ordenes:
                secciones = self.getSeccion()
                seccion_dict = { seccion["IDSeccion"]:seccion["DescSeccion"] for seccion in secciones}
                resumen_secciones = defaultdict(lambda: {
                "seleccion": "",
                "centro": "",
                "capacidad_teorica_diaria": 0,
                "seccion": "",
                "carga_trabajo": 0,
                "porcentaje_carga_trabajo": 0,
                "dias": 0,
                "cant_trabajo": 0
                })
                capacidad_teorica_diaria_por_centro = {
                "120": 32,  
                "125": 32, 
                "126": 32, 
                "130": 60, 
                "135": 20,  
                "136":0,
                "138":0,
                "139": 20, 
                "140": 100, 
                "145": 20,  
                "150": 20, 
                "155": 40, 
                "160": 40, 
                "161": 20,  
                "162": 20, 
                "170": 20,  
                "172": 18,  
                "175": 20,  
                "176": 20,  
                "180": 140,
                "230": 20,
                "250" : 20, 
                "270": 50,
                "280": 50, 
                "285": 50, 
                "290": 50,   
                "300": 30,   
                "350": 30,   
                "455": 50,  
                "400": 9999 ,
                "450": 9999 ,
                "500": 9999 ,
                "999": 9999
                }
                for orden in ordenes:
                    seccion_id = orden["IDSeccion"]
                    seccion_desc = seccion_dict.get(seccion_id, "Desconocido")
                    grupo_id = seccion_id
                    if seccion_id in ('125', '126'):
                        grupo_id = '125'
                    if seccion_id in ('400', '450', '500'):
                        grupo_id = '400'
                        # grupo_id = (400,450,500)
                    print(grupo_id)
                    resumen_secciones[grupo_id]["centro"] = "-".join(map(str,grupo_id)) if isinstance(grupo_id, tuple) else seccion_id
                    resumen_secciones[grupo_id]["seccion"] = seccion_desc
                    resumen_secciones[grupo_id]["capacidad_teorica_diaria"] = capacidad_teorica_diaria_por_centro.get(grupo_id, 0)
                    resumen_secciones[grupo_id]["seleccion"] = seccion_desc[:3].upper() if seccion_desc else "N/A"
                    resumen_secciones[grupo_id]["carga_trabajo"] += orden["Tiempo"]
                    resumen_secciones[grupo_id]["cant_trabajo"] += 1
                total_carga_trabajo = sum(seccion["carga_trabajo"] for seccion in resumen_secciones.values())
                for seccion_data in resumen_secciones.values():
                    seccion_data["porcentaje_carga_trabajo"] = (seccion_data["carga_trabajo"] / total_carga_trabajo) * 100 if total_carga_trabajo > 0 else 0
                    seccion_data["dias"] = seccion_data["carga_trabajo"] / seccion_data["capacidad_teorica_diaria"] if seccion_data["capacidad_teorica_diaria"] > 0 else 0
                resumen_secciones_list = list(resumen_secciones.values())
                resumen_secciones_list.sort(key=lambda x: x['seccion'],reverse=True)
                return resumen_secciones_list
            else:
                return []
                # return resumen_secciones_list
        
        except Exception as e:
            print(f"Error al procesar datos: {e}")
            return {"status": "error", "message": "Internal Server Error"}
        

    def getOFFromCentro(self,centro):
        try:
            self.connection = self.connection_string_solmicro.connect()
            query  = text(f"SELECT [of].NOrden, [of].IDArticulo,ma.DescArticulo,[or].IDOperacion,[or].QFabricar,[or].QBuena,[or].CantidadTiempo, [or].IDProveedor, [of].FechaCreacion, mc.IDSeccion FROM tbOrdenRuta [or] INNER JOIN tbOrdenFabricacion [of] ON [or].IDOrden = [of].IDOrden INNER JOIN tbMaestroCentro mc ON [or].IDCentro = mc.IDCentro INNER JOIN tbMaestroArticulo ma ON [of].IDArticulo = ma.IDArticulo WHERE [or].Estado < 4 AND mc.IDSeccion = '{centro}'")
            resultado =  self.connection.execute(query).fetchall()
            resultado_list = []
            for row in resultado:
                row_dict = {
                    "NOrden" : row[0],
                    "IDArticulo": row[1],
                    "DescArticulo": row[2],
                    "IDOperacion": row[3],
                    "QFabricar": row[4],
                    "QBuena": row[5],
                    "CantidadTiempo": row[6],
                    "IDProveedor": row[7],
                    "FechaCreacion": row[8],
                    "IDSeccion": row[9],
                    }
                resultado_list.append(row_dict)
            return resultado_list
        
        except Exception as e:
            print(f"Error en getOrdenes: {e}")
            return {"status": "error", "message": "Internal Server Error"}  

                
