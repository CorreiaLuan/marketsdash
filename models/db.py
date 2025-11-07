from sqlalchemy import create_engine
import pandas as pd
import pyodbc,sqlite3
# import config
from contextlib import contextmanager
import time

# Optional psycopg2 imports for connectivity-aware retries on Postgres
try:
    import psycopg2
    from psycopg2 import OperationalError as PGOperationalError, InterfaceError as PGInterfaceError
except Exception:  # pragma: no cover – environment without psycopg2
    psycopg2 = None
    class PGOperationalError(Exception):
        pass
    class PGInterfaceError(Exception):
        pass

class Db:
    def __init__(self, server=None, database=None, uid=None, pwd=None, access_path=None, sqlite_dbpath=None, driver=None,sslmode=None):
        self.engine = None
        self.sqlite = False
        self.postgres = False

        if access_path is None and sqlite_dbpath is None and driver is None:
            # PostgreSQL connection
            if sslmode is None:
                sslmode = ""
            else:
                sslmode = f"?sslmode={sslmode}"
            connection_string = f"postgresql://{uid}:{pwd}@{server}/{database}{sslmode}"
            odbc_prefix = ""
            self.postgres = True
        elif sqlite_dbpath is not None:
            # SQLite connection
            connection_string = sqlite_dbpath
            odbc_prefix = "sqlite:///"
            self.sqlite = True
        else:
            # Access or other ODBC connection
            connection_string = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={access_path}"
            odbc_prefix = "access+pyodbc:///?odbc_connect="

        self.engine = create_engine(f"{odbc_prefix}{connection_string}")
        self.connection_string = connection_string

    @contextmanager
    def connect(self):
        if self.postgres:
            connection = self.engine.raw_connection()
        elif self.sqlite:
            connection = sqlite3.connect(self.connection_string)
        else:
            connection = pyodbc.connect(self.connection_string)
        yield connection
        connection.close()

    def execute(self, query: str, result=False, operation="operation", df=True, retries:int=3, backoff_sec:float=0.8):
        """Execute a SQL statement with optional retries for transient connectivity errors.

        Parameters
        - query: SQL to execute
        - result: return result rows
        - operation: label ('select', 'insert', ...)
        - df: when returning results, format as pandas DataFrame if True
        - retries: number of attempts for transient errors (Postgres only)
        - backoff_sec: base seconds for exponential backoff
        """
        if self.postgres and not query.endswith(";"):
            query = f"{query};"

        attempt = 0
        while True:
            try:
                with self.connect() as connection:
                    cursor = connection.cursor()
                    cursor.execute(query)
                    if operation != "select":
                        connection.commit()
                    if result:
                        try:
                            if not df:
                                return cursor.fetchall()
                            rows = cursor.fetchall()
                            column_names = [desc[0] for desc in cursor.description]
                            return pd.DataFrame(rows, columns=column_names)
                        except Exception as e:
                            print(f"Error fetching results: {e}")
                            return None
                    return None
            except (PGOperationalError, PGInterfaceError) as e:
                # Only retry for Postgres connectivity-type errors
                attempt += 1
                if attempt >= retries:
                    # Re-raise after exhausting retries so Streamlit can show the error
                    raise
                sleep_time = backoff_sec * (2 ** (attempt - 1))
                time.sleep(sleep_time)
                continue
            except Exception:
                # Non-transient or unknown errors – bubble up
                raise

    def operation(self, query, operation, df=True):
        if operation == "select":
            return self.execute(query, result=True, operation=operation, df=df)
        else:
            self.execute(query, operation=operation)
            print(f"{operation} operation successful.")

    def select(self, query, df=True):
        return self.operation(query, "select", df)

    def insert(self, query):
        self.operation(query, "insert")

    def update(self, query):
        self.operation(query, "update")

class dbmai(Db):
    def __init__(self, server=None, database=None, uid=None, pwd=None, access_path=None):
        server = 'MAGDB04SQLVMDEV.mongeral.seguros,4030'
        database = 'MAI'
        uid = 'usr_appMai'
        pwd = '9962v3DrlKo0h6qR157ssetDGA'
        driver = '{SQL Server}'
        super().__init__(server, database, uid, pwd, access_path,driver)

class dbPgCloud(Db):
    def __init__(self):
        uid = "neondb_owner"
        pwd = "npg_cjL1pEwqTvu4"
        database = "Anbima"
        server = "ep-sparkling-shadow-acyrwch4-pooler.sa-east-1.aws.neon.tech"
        super().__init__(uid=uid, pwd=pwd, database=database, server=server, sslmode="require")
        
    def get_feriados(self):

        return self.select(
            "Select * from feriados"
        )

    def update_feriados(self):

        link = "https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls"
        Table = "Feriados"
        df = pd.read_excel(link)
        df.dropna(inplace=True)
        df['Data'] = df['Data'].apply(lambda dt:dt.date())

        df.to_sql(
            Table,db.engine,if_exists='replace',index=False
        )
    
    def delete_if_exist(self,df:pd.DataFrame,Table:str,keyCols:list):
        
        sql = f"""
            DELETE From {Table} where {",".join(keyCols)}
        """

# class dbMaiAtivos(Db):
#     def __init__(self, server=None, database=None, uid=None, pwd=None, access_path=None, sqlite_dbpath=None, driver='{SQL Server}'):
#         sqlite_dbpath = config.db_path
#         super().__init__(server, database, uid, pwd, access_path, sqlite_dbpath, driver)
    
#     def get_feriados(self):

#         return self.select(
#             "Select * from Feriados"
#         )

#     def update_feriados(self):

#         link = "https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls"
#         Table = "Feriados"
#         df = pd.read_excel(link)
#         df.dropna(inplace=True)
#         df['Data'] = df['Data'].apply(lambda dt:dt.date())

#         df.to_sql(
#             Table,db.engine,if_exists='replace',index=False
#         )
    
#     def delete_if_exist(self,df:pd.DataFrame,Table:str,keyCols:list):
        
#         sql = f"""
#             DELETE From {Table} where {",".join(keyCols)}
#         """
        


# Example usage:
if __name__ == "__main__":
    
    db = dbPgCloud()
    # db_mai = dbMaiAtivos()

    feriados = db.get_feriados()
    print(feriados)
    
    
    
    
    
    
