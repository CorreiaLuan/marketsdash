####Imports####
##Local imports##
from models.tables import IMA
import utils
from typing import Literal
##Local imports##

##Lib imports##
import pandas as pd
import datetime
##Lib imports##

class Bond:
    def __init__(self,tipo_titulo,taxa = "",pu = "",vencimento:datetime.date = "") -> None:
        self.tipo_titulo = tipo_titulo
        self.model = IMA()
        self.taxa = taxa
        self.pu = pu
        self.vencimento = vencimento if isinstance(vencimento,datetime.date) else pd.to_datetime(vencimento).date
        self.hist:pd.DataFrame = None
    
    def get_historico(self,data_vencimento = "",data_inicial = "",data_final = "",on_the_run=True,table = "",columns: list = "",retorno: bool = False,distinct: bool = True):
        df = self.model.get_historico(
            self.tipo_titulo,data_vencimento,data_inicial,data_final,on_the_run,table,columns,retorno,distinct
        )
        df.sort_values(['data_vencimento','data_referencia'],inplace=True)
        self.hist = df
        return df

class NTNB(Bond):
    def __init__(self) -> None:
        self.tipo_titulo = "NTN-B"
        super().__init__(self.tipo_titulo)

class LFT(Bond):
    def __init__(self) -> None:
        self.tipo_titulo = "LFT"
        super().__init__(self.tipo_titulo)

class LTN(Bond):
    def __init__(self) -> None:
        self.tipo_titulo = "LTN"
        super().__init__(self.tipo_titulo)

class NTNF(Bond):
    def __init__(self) -> None:
        self.tipo_titulo = "NTN-F"
        super().__init__(self.tipo_titulo)

class NTNC(Bond):
    def __init__(self) -> None:
        self.tipo_titulo = "NTN-C"
        super().__init__(self.tipo_titulo)

tipo_titulo = {
    "LTN":LTN,
    "NTN-F":NTNF,
    "LFT":LFT,
    "NTN-B":NTNB,
    "NTN-C":NTNC
}

codigos_vencimentos = {
    1:"F",
    2:"G",
    3:"H",
    4:"J",
    5:"K",
    6:"M",
    7:"N",
    8:"Q",
    9:"U",
    10:"V",
    11:"X",
    12:"Z"
}

# class Futuro:
#     api = xlAddin()
#     db = utils.db

#     def __init__(self,product_code) -> None:
#         self.product_code = product_code
#         self.table_cadastro = "Futuros"
    
#     def contracts_table(self,n=30) -> pd.DataFrame:
#         data = {f"{self.product_code}@{i}":"Ativo;dvc" for i in range(n+1)}
#         df:pd.DataFrame = self.api.bc(
#             data = data,
#             dataframe=True,
#             date_columns="dvc"
#         )
#         df.rename({"dvc":"data_vencimento"},inplace=True)
#         return df.dropna(subset = ["Ativo"])

#     def update_contracts_table(self):
#         contracts = self.contracts_table()
#         contracts.to_sql(
#             self.table_cadastro,self.db.engine,index = False,if_exists='replace'
#         )

# class Dap(Futuro):
#     def __init__(self) -> None:
#         super().__init__("DAP")

class Trava_IMA:
    ima = IMA()
    db = utils.db
    wd = utils.workdays()
    def __init__(self,tipo_titulo:Literal["LTN","NTN-F","LFT","NTN-B","NTN-C"]) -> None:
        self.table = "Trava"
        self.tipo_titulo = tipo_titulo
    
    def Codigo(self,row):
        if row["tipo_titulo"] == 'NTN-B':
            return f"{row['tipo_titulo']} {row['data_vencimento'][2:4]}"
        codigo_mes = codigos_vencimentos[int(row['data_vencimento'][5:7])]
        return f"{row['tipo_titulo']} {codigo_mes}{row['data_vencimento'][2:4]}"

    def monta_historico_trava(self,data_inicial = "",data_final = ""):
        df = self.ima.get_historico(columns=['data_referencia',"tipo_titulo",'data_vencimento','taxa_indicativa','duration_titulo'],data_inicial=data_inicial,data_final=data_final)
        df.insert(
            2,
            "Codigo",
            df.apply(lambda row:self.Codigo(row),axis = 1)
        )
        df_merged = pd.merge(
            df,df,how="left",on=["data_referencia","tipo_titulo"],suffixes=["_curta","_longa"]
        )
        df_merged = df_merged.loc[df_merged['data_vencimento_curta'] < df_merged['data_vencimento_longa']]
        df_merged.insert(
            len(df_merged.columns),
            "Codigo_Trava",
            df_merged.apply(lambda row:f'{row["Codigo_curta"]} {row["Codigo_longa"]}',axis = 1)
        )
        df_merged.insert(
            len(df_merged.columns),
            "Spread",
            df_merged.apply(lambda row:row["taxa_indicativa_longa"] - row["taxa_indicativa_curta"],axis = 1)
        )
        df_merged.insert(
            len(df_merged.columns),
            "Ratio",
            df_merged.apply(lambda row:row["duration_titulo_longa"]/row["duration_titulo_curta"],axis = 1)
        )
        df_merged.to_sql(
            self.table,self.db.engine,if_exists="append"
        )

    
    def update(self,since_date:str=None):
        start_date = since_date if since_date is not None else self.db.select(f"Select data_referencia from {self.table} order by data_referencia desc LIMIT 1",df = False)[0][0]
        temp_date = start_date
        start_date = str(self.wd.offset(start_date,1))
        end_date = str(self.wd.offset(datetime.datetime.today().strftime("%Y-%m-%d"),-1))
        if pd.to_datetime(end_date) < pd.to_datetime(start_date):
            print(f"Tabela {self.table} atualizada até a Última Data disponível: {temp_date}")
            return
        self.monta_historico_trava(data_inicial=start_date,data_final=end_date)
    
    def query(self,data_vencimento = "",data_inicial = "",data_final = "",on_the_run=True,table = "",columns:list="",distinct = True):
        if data_vencimento == "" and on_the_run:
            data_vencimento = f">= '{self.wd.today.strftime('%Y-%m-%d')}'"
        else:
            data_vencimento = f"like '%{data_vencimento}%'"
        filter_date = ""
        if data_inicial != "": filter_date = f"and data_referencia >= '{data_inicial}'"
        if data_final != "": filter_date = f"{filter_date} and data_referencia <= '{data_final}'"
        return  f"""Select {'Distinct' if distinct else ''}
                    {columns if isinstance(columns,str) else ",".join(columns)}
                    from {self.Table if table == "" else table}
                    where tipo_titulo like '%{self.tipo_titulo}%'
                    and data_vencimento_curta {data_vencimento}
                    {filter_date}
                """

    def get_historico(self,data_vencimento = "",data_inicial = "",data_final = "",on_the_run=True,columns:list="",distinct = True):
        
        columns = "*" if columns == "" else columns
        return self.db.select(
            self.query(data_vencimento,data_inicial,data_final,on_the_run,self.table,columns,distinct)
        )
    
    def get_spreads_dashboard(self,ndays:int=90,data_inicial = "",data_final = "") -> pd.DataFrame:

        if data_inicial == "" and data_final == "":
            df = self.get_historico(data_inicial=self.wd.offset(self.wd.strtoday,-ndays))
        else:
            df = self.get_historico(
                data_inicial = data_inicial,
                data_final = data_final
            )
        df_mean = df.groupby(['Codigo_Trava',"Codigo_curta","Codigo_longa"])["Spread"].mean()
        df_std = df.groupby(['Codigo_Trava',"Codigo_curta","Codigo_longa"])["Spread"].std()
        df = pd.merge(df,df_mean,left_on="Codigo_Trava",right_on="Codigo_Trava",suffixes=["","_mean"])
        df = pd.merge(df,df_std,left_on="Codigo_Trava",right_on="Codigo_Trava",suffixes=["","_std"])
        df.insert(
            len(df.columns),
            "Std1",
            df["Spread_mean"]+df["Spread_std"]
        )
        df.insert(
            len(df.columns),
            "Std_1",
            df["Spread_mean"]-df["Spread_std"]
        )
        df = df[['data_referencia','Codigo_Trava','Spread',"Codigo_curta","Codigo_longa","Spread_mean","Std1","Std_1"]]
        df.sort_values(['Codigo_Trava','data_referencia'],inplace=True)
        
        return df
    
if __name__ == "__main__":
    

    trava = Trava_IMA("NTN-B")
    df = trava.get_historico()
    df = df.loc[(df['Codigo_curta']=='NTN-B 24') & (df['Codigo_longa']=='NTN-B 50')]
    df = df[['data_referencia','Codigo_Trava','Spread']]
    
    import plotly.express as px

    fig = px.line(df,x="data_referencia",y=["Spread"])
    fig.write_html("chart.html")
    # trava.monta_historico_trava()
    