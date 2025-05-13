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
from models.tables import Curva_Juros
import pandas as pd

#Config
st.set_page_config(
    layout="wide",
    page_title="Mai Page - ETTJ"
)
st.sidebar.markdown(
    "<h1 style='text-align: center;'>Curva de Juros Fechamento</h1><br>",
    unsafe_allow_html=True
)
curva_bool = st.sidebar.toggle("Curva",value = True)

curva = Curva_Juros()
df = curva.get_historico()
df["vertice_du_years"] = df["vertice_du"].apply(curva.convert_vertice)
df['data_referencia'] = pd.to_datetime(df['data_referencia']).dt.date

df = df.melt(
    id_vars = ['data_referencia','vertice_du','vertice_du_years'],
    var_name = "Ativo",
    value_name = "taxa"
)

#Select Mercado
asset_names = df["Ativo"].unique().tolist()
selected_asset = st.sidebar.selectbox(
    'Selecione o Mercado',
    asset_names,
    index = 0
)
y_axis = ["taxa"]
labels = {
    "vertice_du_years": "Vertice",
    "data_referencia": "Data",
    "value":"Taxa"
}
if not curva_bool:
    
    #Select Periodo
    start_date, end_date = st.sidebar.date_input(
        "Selecione o Período:", 
        (
            pd.to_datetime('2023-01-01'),
            df['data_referencia'].max()
        ),
        df['data_referencia'].min(),
        df['data_referencia'].max(),
        format = "DD.MM.YYYY"
    )
    selected_data = df[
        (df["Ativo"] == selected_asset)
        & (df['data_referencia'] >= start_date)
        & (df['data_referencia'] <= end_date)
    ]
    index_keep = selected_data.groupby('vertice_du_years')['taxa'].sum()
    index_keep = index_keep[index_keep !=0].index
    selected_data = selected_data[
        (selected_data["vertice_du_years"].isin(index_keep))
    ]
    x_axis = "data_referencia"
    color = "vertice_du_years"
    mode = "lines"
    dict_legend = dict(orientation='v',y =0.5,x = -0.2)
else:
    dates_list:list = df["data_referencia"].unique().tolist()
    dates_list.sort(reverse=True)
    selected_dates = st.multiselect(
        "Adicione Datas:", 
        dates_list,
        default = df['data_referencia'].max()
    )
    selected_data:pd.DataFrame = df[
        (df["Ativo"] == selected_asset)
        & (df["data_referencia"].isin(selected_dates))
        & (~df["taxa"].isnull())
    ]
    selected_data.sort_values(
        by = ["vertice_du"],
        inplace = True   
    )

    x_axis = "vertice_du_years"
    color = "data_referencia"
    mode = "markers+lines"
    dict_legend = dict(orientation='h',y =1.1,x = 0)

fig = px.line(
    selected_data,
    x = x_axis,
    y = y_axis,
    color = color,
    labels = labels,
    height = 650
)
fig.for_each_xaxis(lambda x: x.update(showgrid=True,showticklabels=True))
fig.update_layout(
    hovermode = "x"
    ,legend=dict_legend
    ,autosize=True
    ,margin=dict(l=0, r=0, t=0, b=0)
)
fig.update_traces(hovertemplate = "",mode = mode)
fig.update_xaxes(
    rangeselector = dict(
        buttons = list([
            dict(step = "all",label = "All"),
            dict(count = 1,label = "1M",step = "month",stepmode = "backward"),
            dict(count = 3,label = "3M",step = "month",stepmode = "backward"),
            dict(count = 6,label = "6M",step = "month",stepmode = "backward"),
            dict(count = 1,label = "YTD",step = "year",stepmode = "todate"),
            dict(count = 1,label = "1Y",step = "year",stepmode = "backward"),
        ])
    )
)

if selected_asset == "taxa_implicita":
    fig.add_shape(
        type='line',
        x0=0, x1=1,  # x0 and x1 are relative to the x-axis range (0 to 1 means full width of the plot)
        y0=3, y1=3,
        line=dict(
            color='gray',
            width=2,
            dash='dash',  # Set the line style to dashed
        ),
        xref='paper',  # xref set to 'paper' ensures the line spans the entire plot width
        yref='y'  # yref set to 'y' to position the line based on y-axis values
    )
    fig.add_annotation(
        x=0.5,  # x position relative to xref
        y=3,  # y position relative to yref
        text="<b>Meta</b>",  # Text to be displayed
        showarrow=False,  # Hide the arrow
        xanchor='center',  # Anchor the text to the left
        yanchor='bottom',  # Center the text vertically on the line
        xref='paper',  # xref set to 'paper' to position it relative to the plot width
        yref='y',  # yref set to 'y' to position it relative to y-axis values
        font=dict(
            size=14,  # Set the font size (adjust as needed)
            color="Gray",  # Set the font color
            family="Arial",  # Set the font family
            # bold=True  # Make the text bold
        )
    )
st.plotly_chart(fig,use_container_width=True)
st.dataframe(selected_data,use_container_width=True,hide_index=True)