"""
Anbima Developers API for Python
~~~~~~~~~~~~~~~~~~~~~

Uses Requests to get Data from Anbima API.

:created by Luan Correia (2023)
"""
import os
import requests
from typing import Literal
# from dotenv import load_dotenv

Ambientes = dict(
    Produção = "https://api.anbima.com.br",
    Sandbox = "https://api-sandbox.anbima.com.br"
)

# load_dotenv()

class Api:
    def __init__(
            self,
            ambiente:Literal["Produção","Sandbox"] = "Produção",
            produto = "feed/precos-indices",
            versao:Literal["v1","v2"] = "v1",
            client_id = None,
            client_secret = None
    ) -> None:
        self.client_id = client_id if client_id is not None else os.getenv("CLIENT_ID")
        self.client_secret = client_secret if client_secret is not None else os.getenv("CLIENT_SECRET")
        self.access_token = None
        self.baseurl = Ambientes[ambiente]
        self.ambiente = ambiente
        self.auth_endpoint = "oauth/access-token"
        self.produto = produto
        self.versao = versao
        self.versao_temp = None

    def build_url(self,endpoint) -> str:
        return f"{self.baseurl}/{endpoint}"

    def check_token(func):
        def wrapper(*args,**kwargs):
            self = args[0]
            if self.access_token is None: self.get_access_token()
            return func(*args,**kwargs)
        return wrapper
    
    def change_versao(self,versao:Literal["v1","v2"]):
        self.versao_temp = self.versao
        self.versao = versao
        return
    
    def volta_versao(self):
        self.versao = self.versao_temp

    @check_token
    def get(self,endpoint,**kwargs) -> requests.Response:
        try:
            json =  requests.get(
                self.build_url(f"{self.produto}/{self.versao}/{endpoint}"),
                params = kwargs,
                headers = {
                    "Content-Type":"application/json",
                    "client_id":self.client_id,
                    "access_token":self.access_token
                }
            )
            return json
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
    def get_access_token(self) -> None:
        self.access_token = requests.post(
            self.build_url(self.auth_endpoint),
            data = {
                'grant_type':'client_credentials'
            },
            auth = (self.client_id,self.client_secret)   
        ).json()["access_token"]
    
    def get_curva_juros(self,date) -> requests.Response:
        response = self.get(
            "titulos-publicos/curvas-juros",
            data = date,
            
        )
        return response.json()
    
    def get_secundario_tpf(self,date) -> requests.Response:
        response = self.get(
            "titulos-publicos/mercado-secundario-TPF",
            data = date
        )
        return response.json()
    
    def get_IMA(self,date) -> requests.Response:
        response = self.get(
            "indices-mais/resultados-ima",
            data = date
        )
        return response.json()
    
    def get_difusao_taxas(self,date="") -> requests.Response:
        response = self.get(
            "titulos-publicos/difusao-taxas",
            data = date
        )
        return response.json()

    def get_vna(self,date) -> requests.Response:
        response = self.get(
            "titulos-publicos/vna",
            data = date
        )
        return response.json()
    
    def get_negocios(self,date,
                    # indice:Literal['IRF-M 1+','IRF-M','IMA-S','IMA-B 5','IMA-B 5+','IMA-B','IMA-GERAL-EX-C','IMA-GERAL','IRF-M P2','IMA-B 5 P2','IRF-M 1','IMA-C'] = ""
        ):
        self.change_versao("v2")
        response = self.get(
            "ima-etf/negocios-extra",
            data = date
            # etf = indice
        )
        self.volta_versao()
        return response.json()

    def get_IDA(self,date) -> requests.Response:
        response = self.get(
            "indices-mais/resultados-ida",
            data = date
        )
        return response.json()    