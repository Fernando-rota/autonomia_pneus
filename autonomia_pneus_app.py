import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Mapeamento Truck Realístico", layout="wide")
st.title("🚛 Mapeamento Realístico do Truck por Veículo")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("📂 Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    sheets = pd.read_excel(arquivo, sheet_name=None)
    if not {"pneus", "posição", "sulco"}.issubset(sheets.keys()):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"]
    df_posicao = sheets["posição"]

    # Padronizar colunas de posição
    if "Sigla" in df_pneus.columns:
        df_pneus = df_pneus.rename(columns={"Sigla": "Sigla da Posição"})
    if "Sigla" in df_posicao.columns:
        df_posicao = df_posicao.rename(columns={"Sigla": "Sigla da Posição"})

    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # ----------------- FILTRO POR PLACA -----------------
    placas = df_pneus["Veículo - Placa"].dropna().unique()
    placa_sel = st.selectbox("Selecione a placa do veículo", np.append("Todas", placas))
    if placa_sel != "Todas":
        df_map = df_pneus[df_pneus["Veículo - Placa"]==placa_sel]
    else:
        df_map = df_pneus.copy()

    # ----------------- MAPA TÉCNICO -----------------
    st.subheader("🛞 Layout Realístico do Truck")

    # Coordenadas aproximadas para desenho técnico
    layout_real = {
        "AEI": (1,3), "ADI": (3,3),
        "CEE": (0.5,2), "CEI": (1.5,2), "CDE": (2.5,2), "CDI": (3.5,2),
        "DEE": (0.5,1), "DEI": (1.5,1), "DDE": (2.5,1), "DDI": (3.5,1)
    }

    x, y, color, labels, hovertext = [], [], [], [], []
    for idx, row in df_map.iterrows():
        sigla = row["Sigla da Posição"]
        if sigla in layout_real:
            px_, py_ = layout_real[sigla]
            x.append(px_)
            y.append(py_)
            sulco = row.get("Aferição - Sulco", 0)
            if sulco >= 5:
                color.append("green")
            elif sulco >= 3:
                color.append("yellow")
            else:
                color.append("red")
            labels.append(sigla)
            hovertext.append(f"Placa: {row.get('Veículo - Placa','')}<br>Sulco: {sulco}mm<br>Modelo: {row.get('Modelo (Atual)','')}")

    fig = go.Figure()

    # Desenhar cabine
    fig.add_trace(go.Scatter(x=[1,3,3,1,1], y=[3.5,3.5,4,4,3.5],
                             fill='toself', fillcolor='lightgray', line=dict(color='black'),
                             mode='lines', name='Cabine'))

    # Desenhar eixos
    fig.add_trace(go.Scatter(x=[0,4], y=[3,3], mode='lines', line=dict(color='black', width=4), name='Eixo Dianteiro'))
    fig.add_trace(go.Scatter(x=[0,4], y=[2,2], mode='lines', line=dict(color='black', width=4), name='Eixo Tração'))
    fig.add_trace(go.Scatter(x=[0,4], y=[1,1], mode='lines', line=dict(color='black', width=4), name='Eixo Truck'))

    # Pneus
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        marker=dict(size=50, color=color, line=dict(width=2, color='black')),
        text=labels, textposition="middle center",
        hoverinfo='text', hovertext=hovertext
    ))

    fig.update_layout(
        title="Truck Realístico com Pneus Coloridos",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="white",
        height=500,
        width=900
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----------------- TABELA DE MEDIDAS -----------------
    st.subheader("📏 Medidas de Sulco do Veículo")
    cols_show = ["Sigla da Posição","Posição","Veículo - Placa","Modelo (Atual)","Aferição - Sulco"]
    cols_show = [c for c in cols_show if c in df_map.columns]
    st.dataframe(df_map[cols_show].sort_values(by="Aferição - Sulco", ascending=False), use_container_width=True)

else:
    st.info("Aguardando upload do arquivo Excel…")
