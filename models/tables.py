####Imports####
##Local imports##
from Api.anbima import Api
from utils import workdays,db
##Local imports##

##Lib imports##
import numpy as np
import pandas as pd
from datetime import datetime
from sqlite3 import OperationalError
from typing import Literal
##Lib imports##
####Imports####

class Anbima:
    api = Api()
    wd = workdays()
    db = db

    def __init__(self,Table,api_get_function) -> None:
        "Classe Para Lidar com a Api da Anbima, buscar dados e montar um banco com os dados coletados"
        self.Table = Table
        self.api_get_function = api_get_function
    
    def explode(self,df:pd.DataFrame,explode_col:str) -> pd.DataFrame:

        df = df.explode(explode_col,ignore_index=True)
        df = pd.concat([df.drop([explode_col], axis=1), df[explode_col].apply(pd.Series)], axis=1)

        return df

    def get_range(self,date_range:pd.DatetimeIndex) -> pd.DataFrame:

        df = pd.DataFrame()
        for data in date_range:
            data = data.strftime('%Y-%m-%d')
            try:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame.from_records(
                            self.api_get_function(data)
                        )
                    ],
                    ignore_index=True
                )
            except:
                print(f"Erro na data {data}")

        return df

    def delete_if_exist(self,df:pd.DataFrame,Table = "",data_col_name = 'data_referencia'):
        datas = df[data_col_name].drop_duplicates().to_list()
        Table = Table if not Table == "" else self.Table
        sql = f'''DELETE from {Table} Where data_referencia in ('{"','".join(datas)}')'''
        try:
            self.db.execute(sql)
        except Exception as e:
            if e.args[0] == f'no such table: {Table}':
                pass
            else:
                raise(Exception)
    
    def update_range(self,**kwargs):
        pass

    def update(self,since_date:str = None,table_check:str = ""):

        #Aqui eu pego a última data que tem na base
        if table_check == "": table_check = self.Table
        try:
            start_date = since_date if since_date is not None else db.select(f"Select data_referencia from {table_check} order by data_referencia desc LIMIT 1",df = False)[0][0]
        except OperationalError as OE:
            if 'no such table' in str(OE).lower():
                print(f"Table {table_check} do not exist, will create when exporting the first data...")
        try:
            temp_date = start_date
        except:
            temp_date,start_date = "2017-06-01","2017-06-01"
        start_date = str(self.wd.offset(start_date,1))
        end_date = str(self.wd.offset(datetime.today().strftime("%Y-%m-%d"),-1))
        if pd.to_datetime(end_date) < pd.to_datetime(start_date):
            print(f"Tabela {table_check} atualizada até a Última Data disponível: {temp_date}")
            return
        self.update_range(start_date,end_date)

class TPF(Anbima):
    """
    Subclasse Anbima para lidar com os dados da API da Anbima no endpoint 'titulos-publicos/mercado-secundario-TPF'
    """
    def __init__(self) -> None:
        super().__init__(Table = 'TPF', api_get_function = self.api.get_secundario_tpf)
    
    def update_range(self,start_date,end_date):

        st_str = start_date
        start_date = datetime.strptime(start_date,'%Y-%m-%d')
        end_str = end_date
        end_date = datetime.strptime(end_date,'%Y-%m-%d')
        date_range = self.wd.range(start_date,end_date)

        df = self.get_range(date_range)

        new_columns = []
        for col in df.columns:
            if col in new_columns: col = f"{col}_titulo" 
            new_columns.append(col)
        df.columns = new_columns
        
        self.delete_if_exist(df)
        df.to_sql(
            self.Table,db.engine,index=False,if_exists='append'
        )
        print(f'Tabela {self.Table} Atualizada de {st_str} até {end_str}')

    def query(self,tipo_titulo = "",data_inicial = "",data_final = "",table = "",columns:list="",distinct = True):
        
        filter_date = ""
        if data_inicial != "": filter_date = f"where data_referencia >= '{data_inicial}'"
        if data_final != "": filter_date = f"{filter_date} and data_referencia <= '{data_final}'"
        if tipo_titulo !="": tipo_titulo = f" and tipo_titulo like '%{tipo_titulo}%'"
        return  f"""Select {'Distinct' if distinct else ''}
                    {columns if isinstance(columns,str) else ",".join(columns)}
                    from {self.Table if table == "" else table}
                    {filter_date}
                    {tipo_titulo}
                """
    def get_historico(self,tipo_titulo = "",data_inicial = "",data_final = "",table = "",columns:list="",distinct = True):
        
        columns = "*" if columns == "" else columns
        if table == "": table = self.Table
        return self.db.select(
            self.query(tipo_titulo,data_inicial,data_final,table,columns,distinct)
        )


class IMA(Anbima):
    """
    Subclasse Anbima para lidar com os dados da API da Anbima no endpoint 'indices-mais/resultados-ima'
    """
    def __init__(self) -> None:
        super().__init__(Table ='IMA', api_get_function = self.api.get_IMA)
        self.table_retornos = "retornos_historicos"
    
    def update_range(self,start_date,end_date):

        st_str = start_date
        start_date = datetime.strptime(start_date,'%Y-%m-%d')
        end_str = end_date
        end_date = datetime.strptime(end_date,'%Y-%m-%d')
        date_range = self.wd.range(start_date,end_date)

        df = self.get_range(date_range)
        df = self.explode(df,'componentes')

        new_columns = []
        for col in df.columns:
            if col in new_columns: col = f"{col}_titulo" 
            new_columns.append(col)
        df.columns = new_columns
        
        self.delete_if_exist(df)
        df.to_sql(
            self.Table,db.engine,index=False,if_exists='append'
        )
        print(f'Tabela {self.Table} Atualizada de {st_str} até {end_str}')
    
    def query(self,tipo_titulo:Literal["LTN","NTN-F","LFT","NTN-B","NTN-C"] = "",data_vencimento = "",data_inicial = "",data_final = "",
              on_the_run=True,table = "",columns:list="",retorno = False,distinct = True,
              tipo_indice:Literal['IRF-M 1+','IRF-M','IMA-S','IMA-B 5','IMA-B 5+','IMA-B','IMA-GERAL-EX-C','IMA-GERAL','IRF-M P2','IMA-B 5 P2','IRF-M 1','IMA-C'] = "",indice = False
        ):

        tipo_column = "tipo_titulo" if not indice or retorno else "indice"
        tipo_value = tipo_titulo if not indice else tipo_indice
        if data_vencimento == "" and on_the_run:
            data_vencimento = f">= '{self.wd.today.strftime('%Y-%m-%d')}'"
        else:
            data_vencimento = f"like '%{data_vencimento}%'"
        filter_date = ""
        if data_inicial != "": filter_date = f"and data_referencia >= '{data_inicial}'"
        if data_final != "": filter_date = f"{filter_date} and data_referencia <= '{data_final}'"
        if not indice:
            data_vencimento = f"and data_vencimento {data_vencimento}"
        else:
            data_vencimento = ""
        return  f"""Select {'Distinct' if distinct else ''}
                    {columns if isinstance(columns,str) else ",".join(columns)}
                    from {self.Table if table == "" else table}
                    where {tipo_column} like '%{tipo_value}%'
                    {data_vencimento}
                    {filter_date}
                """
    
    def get_historico(self,tipo_titulo:Literal["LTN","NTN-F","LFT","NTN-B","NTN-C"] = "",data_vencimento = "",data_inicial = "",data_final = "",
                      on_the_run=True,table = "",columns:list="",retorno = False,distinct = True,
                      tipo_indice:Literal['IRF-M 1+','IRF-M','IMA-S','IMA-B 5','IMA-B 5+','IMA-B','IMA-GERAL-EX-C','IMA-GERAL','IRF-M P2','IMA-B 5 P2','IRF-M 1','IMA-C'] = "",indice = False
                ):
        
        if not retorno:
            columns = ["data_referencia","tipo_titulo","data_vencimento","taxa_indicativa taxa","pu","pu_juros"] if columns == "" else columns
        else:
            columns = "*" if columns == "" else columns
            table = self.table_retornos
        return self.db.select(
            self.query(tipo_titulo,data_vencimento,data_inicial,data_final,on_the_run,table,columns,retorno,distinct,tipo_indice,indice)
        )

    def monta_retorno_acumulado(self,tipo_titulo:Literal["LTN","NTN-F","LFT","NTN-B","NTN-C"] = "",data_vencimento = "",data_inicial = "",data_final = "",if_exists = "append") -> None:
        df = self.get_historico(tipo_titulo,data_vencimento,data_inicial,data_final)
        df.sort_values(
            ['tipo_titulo','data_vencimento','data_referencia'],ignore_index=True,inplace=True
        )
        df['retorno'] = df['pu'].div(df['pu'].shift()) + df['pu_juros'].div(df['pu'].shift()) -1
        df['row_number'] = df.groupby(['tipo_titulo','data_vencimento']).cumcount()+1
        df = df[df['row_number']!=1]
        df['retorno_acumulado'] = df['retorno'] + 1
        df['retorno_acumulado'] = df.groupby(['tipo_titulo','data_vencimento'])['retorno_acumulado'].cumprod()-1
        df = df.drop('row_number',axis=1)

        self.delete_if_exist(
            df,self.table_retornos
        )

        df.to_sql(
            self.table_retornos,self.db.engine,index = False,if_exists=if_exists
        )
    
    def monta_retorno_acumulado_indice(self,data_vencimento = "",data_inicial = "",data_final = "",
                                      tipo_indice:Literal['IRF-M 1+','IRF-M','IMA-S','IMA-B 5','IMA-B 5+','IMA-B','IMA-GERAL-EX-C','IMA-GERAL','IRF-M P2','IMA-B 5 P2','IRF-M 1','IMA-C'] = "",
                                      if_exists = "append"
            ) -> None:
        df = self.get_historico(
            indice = True,tipo_indice = tipo_indice,data_vencimento = data_vencimento,data_inicial = data_inicial,data_final = data_final,
            columns = ["indice","data_referencia","numero_indice"]
        )
        df.sort_values(
            ['indice','data_referencia'],ignore_index=True,inplace=True
        )
        df['retorno'] = df['numero_indice'].div(df['numero_indice'].shift()) -1
        df['row_number'] = df.groupby(['indice']).cumcount()+1
        df = df[df['row_number']!=1]
        df['retorno_acumulado'] = df['retorno'] + 1
        df['retorno_acumulado'] = df.groupby(['indice'])['retorno_acumulado'].cumprod()-1
        df = df.drop('row_number',axis=1)
        df.rename(
            columns = {'indice':'tipo_titulo','numero_indice':'pu'},inplace=True
        )

        df.to_sql(
            self.table_retornos,self.db.engine,index = False,if_exists=if_exists
        )
    
    

class Curva_Juros(Anbima):

    def __init__(self) -> None:
        super().__init__(Table = "ettj", api_get_function = self.api.get_curva_juros)
    
    def convert_vertice(self,vertice):
        return f"{int(vertice/21)}M" if vertice<252 else f"{vertice/252}Y".replace(".0","")
    
    def update_range(self,start_date,end_date):

        st_str = start_date
        start_date = datetime.strptime(start_date,'%Y-%m-%d')
        end_str = end_date
        end_date = datetime.strptime(end_date,'%Y-%m-%d')
        date_range = self.wd.range(start_date,end_date)

        df = self.get_range(date_range)
        for table in ['parametros','ettj','erros']:
            df_table = self.explode(df[['data_referencia',table]],table)
            self.delete_if_exist(df_table,table)
            df_table.to_sql(
                table,self.db.engine,index = False,if_exists = 'append'
            )
            print(f'Tabela {table} Atualizada de {st_str} até {end_str}')
    
    def query(self,data_inicial = "",data_final = "",table = "",columns:list="",distinct = True):
        
        filter_date = ""
        if data_inicial != "": filter_date = f"and data_referencia >= '{data_inicial}'"
        if data_final != "": filter_date = f"{filter_date} and data_referencia <= '{data_final}'"
        return  f"""Select {'Distinct' if distinct else ''}
                    {columns if isinstance(columns,str) else ",".join(columns)}
                    from {self.Table if table == "" else table}
                    {filter_date}
                """
    def get_historico(self,data_inicial = "",data_final = "",table = "",columns:list="",distinct = True):
        
        columns = "*" if columns == "" else columns
        if table == "": table = self.Table
        return self.db.select(
            self.query(data_inicial,data_final,table,columns,distinct)
        )
        
class Organizer:
    def __init__(self,routines:list[Anbima]=[IMA,Curva_Juros]) -> None:
        self.routines = routines
    def run(self):
        for routine in self.routines:
            instance:Anbima = routine()
            instance.update()


if __name__ == '__main__':

    ima = IMA()
    df_retornos = ima.get_historico(tipo_titulo = 'LFT',data_inicial='2019-01-01',on_the_run=False)
    print(df_retornos)

