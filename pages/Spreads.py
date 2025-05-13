import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )
)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from models.ativos import Trava_IMA,tipo_titulo
from utils import workdays
import pandas as pd
from typing import Literal

wd = workdays()
#Config
st.set_page_config(
    layout="wide",
    page_title="Mai Page - Spreads"
)
st.sidebar.markdown("<h1 style='text-align: center;'>Spreads de Títulos Públicos</h1>", unsafe_allow_html=True)

# Escolhendo titulo
selected_titulo = st.sidebar.selectbox(
    "Selecione o Título",
    tipo_titulo.keys(),
    index = 3
)

#Escolhendo O Range de Datas
start_date,end_date = st.sidebar.date_input(
    "Selecione o Período:",
    (
        pd.to_datetime(wd.offset(wd.strtoday,-90)),
        pd.to_datetime(wd.strtoday)
    ),
    pd.to_datetime("2017-01-01"),
    pd.to_datetime(wd.strtoday),
    format = "DD.MM.YYYY"
)

trava = Trava_IMA(selected_titulo)
df = trava.get_spreads_dashboard(data_inicial=start_date,data_final=end_date)
df['data_referencia'] = pd.to_datetime(df['data_referencia']).dt.date

#Escolhendo a Trava Curta
travas_choices = df["Codigo_curta"].unique().tolist()
selected_travas = st.sidebar.selectbox(
    "Selecione a Ponta Curta do Spread",
    travas_choices,
    index = 0
)

#Escolhendo a Trava Longa
travas_choices_longa = df["Codigo_longa"].unique().tolist()
selected_travas_longa = st.sidebar.multiselect(
    "Selecione a Ponta Longa do Spread",
    travas_choices_longa,
    default=travas_choices_longa
)

#Filtrando
df_trava = df[
    (df["Codigo_curta"] == selected_travas) 
    & (df["Codigo_longa"].isin(selected_travas_longa))
]

fig = px.line(
    df_trava,x="data_referencia",
    y=["Spread","Spread_mean","Std1","Std_1"],
    facet_col="Codigo_Trava",
    facet_col_wrap=4,
    facet_col_spacing=0.02,
    facet_row_spacing=0.1,
    height=800
)

for line in fig['data']:
    if line['legendgroup'] != 'Spread':
        if line['legendgroup'] != 'Spread_mean':
            line['line']['dash'] = 'dash'
            line['line']['color'] = 'gray'
        else:
            line['line']['dash'] = 'dashdot'
            line['line']['color'] = '#000001'

fig.for_each_annotation(
    lambda a:a.update(text = a.text.split("=")[-1].replace("NTN-B ","B").replace(" "," x "),font = {'size':20})
)

fig.for_each_xaxis(lambda x: x.update(showgrid=True,showticklabels=True))
fig.update_layout(hovermode = "x")
fig.update_traces(
    hovertemplate = "",
    showlegend = False
)
st.plotly_chart(
    fig,
    use_container_width=True,
)