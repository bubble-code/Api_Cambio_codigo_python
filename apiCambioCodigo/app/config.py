import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('mssql+pyodbc://sa:Altai2021@srvsql/SolmicroERP6_Favram?driver=SQL+Server')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
