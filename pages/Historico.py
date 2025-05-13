import streamlit as st
import pandas as pd
import plotly.express as px
from models.ativos import tipo_titulo,Bond


#Config
st.set_page_config(
    layout="wide",
    page_title="Mai Page - Historico"
)

st.sidebar.title("Acompanhamento de Mercado")

# Escolhendo modo
cols = st.sidebar.columns(3)
retorno_yield = cols[2].toggle("Retorno",value = True)


# Escolhendo titulo
selected_titulo = st.sidebar.selectbox(
    "Selecione o Título",
    tipo_titulo.keys(),
    index = 3
)

titulo:Bond = tipo_titulo.get(selected_titulo)()
df = titulo.get_historico(retorno = retorno_yield)
df['data_referencia'] = pd.to_datetime(df['data_referencia']).dt.date
st.title(f"Evolução do {'Retorno' if retorno_yield else 'Yield'}: {titulo.tipo_titulo}")

#Vencimentos para escolher
asset_names = df['data_vencimento'].unique().tolist()

# Selecoes
selected_assets = st.sidebar.multiselect('Selecione o Vencimento',asset_names,default=asset_names)
start_date, end_date = st.sidebar.date_input(
    "Selecione o Período:", 
    (
        pd.to_datetime('2025-01-01'),
        df['data_referencia'].max()
    ),
    df['data_referencia'].min(),
    df['data_referencia'].max(),
    format = "DD.MM.YYYY"
)

# Filter data
selected_data = df[
    (df['data_referencia'] >= start_date) & 
    (df['data_referencia'] <= end_date) &
    (df['data_vencimento'].isin(selected_assets))
]

if retorno_yield:
# Recalculate normalized accumulated return for the selected period
    selected_data['Normalized_Accumulated_Return'] = selected_data.apply(
        lambda row:(1+row['retorno_acumulado'])/(1 + selected_data.loc[selected_data['data_vencimento']==row['data_vencimento'],"retorno_acumulado"].iloc[0]) - 1,axis = 1
    )
# Plotly chart
    # fig = px.line(
    #     selected_data,
    #     x='data_referencia',
    #     y=['Normalized_Accumulated_Return'],
    #     labels={'value': 'Returns'},
    #     color = 'data_vencimento'
    # )
    # fig.update_layout(yaxis_tickformat='.3%')
    selected_data_lastdate:pd.DataFrame = selected_data.loc[selected_data['data_referencia'] == selected_data['data_referencia'].max()]
    selected_data_lastdate['data_vencimento'] = selected_data_lastdate['data_vencimento'].apply(
        lambda x: f"{x[5:7]}/{x[2:4]}"
    )
    selected_data_lastdate['Color'] = selected_data_lastdate['Normalized_Accumulated_Return'].apply(
        lambda x: 'Positive' if x >= 0 else 'Negative'
    )

    fig = px.bar(
        selected_data_lastdate,
        y = 'data_vencimento',
        x = 'Normalized_Accumulated_Return',
        category_orders={'data_vencimento':selected_data_lastdate['data_vencimento'].tolist()},
        labels = {'data_vencimento':'Vencimento','Normalized_Accumulated_Return':'Retorno Acumulado'}
        ,text = 'Normalized_Accumulated_Return'
        ,color = 'Color'
        ,color_discrete_map={'Negative':'red'}
    )
    fig.update_traces(textposition='outside',
                       texttemplate = '%{text:.2%}'
                       ,textfont=dict(size=12, color='black'))
    fig.update_layout(xaxis=dict(showticklabels=False, showgrid=False, zeroline=False)
                       ,showlegend = False)
else:
# Plotly chart
    fig = px.line(selected_data, x='data_referencia', y=['taxa'], labels={'value': 'Yield'},color='data_vencimento',
                    )
fig.for_each_xaxis(lambda x: x.update(showgrid=True,showticklabels=True))
fig.update_layout(hovermode = "x",
                  legend = dict(
                      orientation = 'v',
                      y = 0.5,
                      x = -0.2
                  ))
fig.update_traces(hovertemplate = "")
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
st.plotly_chart(fig,use_container_width=True)
st.dataframe(selected_data,use_container_width=True,hide_index=True)
# st.plotly_chart(fig2,use_container_width=True)
# st.write(selected_data_lastdate)

