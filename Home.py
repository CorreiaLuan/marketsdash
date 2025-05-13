import streamlit as st
import plotly.graph_objects as go
from utils import get_rbusbis_series
import numpy as np

# Configurations
st.set_page_config(
    layout="wide",
    page_title="Mai Page - Home"
)

st.title("USD Broad Real Effective Exchange Rate Index (REER)")
st.markdown("Data source: [FRED](https://fred.stlouisfed.org), Index 2020=100, Not Seasonally Adjusted")

# Load data
df = get_rbusbis_series(start_date="1994-01-01")

# Calculate mean and standard deviations
mean_val = df["rbusbis"].mean()
std_val = df["rbusbis"].std()

# Midpoint date for centered annotation placement
mid_index = len(df) // 2
mid_date = df.index[mid_index]

# Create Plotly chart
fig = go.Figure()

# Add main line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["rbusbis"],
    mode="lines",
    line=dict(),
    name="RBUSBIS",
    showlegend=False
))

# Mean and standard deviation bands
bands = {
    "Average": (mean_val, "lightblue" , "dash"),
    "+1σ": (mean_val + std_val, "rgba(0,150,0,1)", "dash"),
    "-1σ": (mean_val - std_val, "rgba(0,150,0,1)", "dash"),
    "+2σ": (mean_val + 2 * std_val, "rgba(255,102,0,1)", "dash"),
    "-2σ": (mean_val - 2 * std_val, "rgba(255,102,0,1)", "dash")
}

for label, (y, color, dash_style) in bands.items():
    fig.add_trace(go.Scatter(
        x=df.index,
        y=[y] * len(df),
        mode="lines",
        line=dict(color=color, dash=dash_style),
        name=label,
        showlegend=False
    ))

# Add annotations for all lines
annotations = [
    dict(
        x=mid_date,
        y=df["rbusbis"].iloc[-1],
        xanchor="left",
        yanchor="middle",
        text="",
        showarrow=False,
        font=dict(color="blue")
    )
]

# Annotate mean and std lines
for label, (y, color, _) in bands.items():
    annotations.append(dict(
        x=mid_date,
        y=y,
        xanchor="center",
        yanchor="bottom",
        text=f"<b>{label}</b>",
        showarrow=False,
        font=dict(color=color,size = 16)
    ))

fig.update_layout(
    title="USD REER with Standard Deviation Bands",
    xaxis_title="Date",
    yaxis_title="Index (Nominal)",
    annotations=annotations,
    height=600
)

st.plotly_chart(fig, use_container_width=True)