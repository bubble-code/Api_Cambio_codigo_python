from sqlalchemy import create_engine, text
from app.config import Config

class OrdenFabricacion:
    def __init__(self):
        self.connection_string = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.server_solmicro = r'srvsql'
        # self.database_solmicro = 'SolmicroERP6_Favram_Pruebas'
        self.database_solmicro = 'SolmicroERP6_Favram'
        self.username_solmicro = 'sa'
        self.password_solmicro = 'Altai2021'
        self.connection_string_solmicro = create_engine(
            f'mssql+pyodbc://{self.username_solmicro}:{self.password_solmicro}@{self.server_solmicro}/{self.database_solmicro}?driver=SQL+Server')

    def execute_script(self, script_id, params):
        scripts = {
            1: "UPDATE tbMaestroContador SET [Contador]=:contador, [FechaModificacionAudi]=:fecha, [UsuarioAudi]=:usuario WHERE ([IDContador]=:id_contador AND [Contador]=:old_contador)",
            2: "SELECT * FROM tbRuta WHERE ([IDArticulo]=:id_articulo AND [IDRuta]=:id_ruta) ORDER BY Secuencia",
            3: "SELECT * FROM tbRutaProveedor WHERE (([IDCentro]=:id_centro AND [IDRutaOp]=:id_ruta_op) AND [Principal]=1)",
            # Añadir más scripts aquí
        }

        if script_id not in scripts:
            raise ValueError("Script ID no válido")

        query = text(scripts[script_id])

        conn = self.connection_string.connect()
        result = conn.execute(query, params)
        conn.close()

        if result.returns_rows:
            return result.fetchall()
        else:
            return {"status": "success"}
        
    def autocomplete(self, search):
        script = text("SELECT TOP 10 [of].IDArticulo, [of].QFabricar,[of].NOrden, [of].Estado FROM tbOrdenFabricacion [of] WHERE [of].NOrden LIKE :search")
        conn = self.connection_string_solmicro.connect()
        result = conn.execute(script,{'search':f'%{search}%'}).fetchall()
        conn.close()
        return [{'IDArticulo':row[0],'QFabricar':row[1],'NOrden':row[2]} for row in result]