import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Dashboard de Gestão de Pneus")

# -----------------------------
# Carregar dados
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("pneus.xlsx")  # Ajuste para o caminho do seu arquivo
    return df

df = load_data()

# -----------------------------
# Indicadores gerais
# -----------------------------
total_pneus = len(df)
media_vida = df['Vida'].mean() if 'Vida' in df.columns else np.nan
pneus_criticos = df[df['Sulco'] < 2] if 'Sulco' in df.columns else pd.DataFrame()

col1, col2, col3 = st.columns(3)
col1.metric("Total de Pneus", total_pneus)
col2.metric("Vida Útil Média (meses)", f"{media_vida:.1f}")
col3.metric("Pneus Críticos (sulco < 2mm)", len(pneus_criticos))

# -----------------------------
# Medidas de sulco
# -----------------------------
st.subheader("📏 Medidas de Sulco")
if 'Sulco' in df.columns:
    df_sulco = df.sort_values(by='Sulco', ascending=False)
    st.dataframe(df_sulco, use_container_width=True)

    # Gráfico interativo
    fig_sulco = px.bar(df_sulco, x='Placa', y='Sulco', color='Sulco',
                       title="Profundidade do Sulco por Pneu",
                       color_continuous_scale='RdYlGn', text='Sulco')
    st.plotly_chart(fig_sulco, use_container_width=True)

# -----------------------------
# Mapeamento Visual do Truck
# -----------------------------
st.subheader("🚛 Mapeamento Visual do Truck")

# Configurar grid do caminhão
posicoes_grid = {
    "AEI": (0, 0), "ADI": (0, 1),
    "CEE": (1, 0), "CEI": (1, 1), "CDE": (1, 2), "CDI": (1, 3),
    "DEE": (2, 0), "DEI": (2, 1), "DDE": (2, 2), "DDI": (2, 3)
}

x, y, color, text, labels = [], [], [], [], []

for idx, row in df.iterrows():
    sigla = row['Sigla']
    if sigla in posicoes_grid:
        grid_y, grid_x = posicoes_grid[sigla]
        x.append(grid_x)
        y.append(-grid_y)  # inverter y para mostrar dianteiro no topo

        sulco = row['Sulco']
        if sulco >= 5:
            color.append("green")
        elif sulco >= 3:
            color.append("yellow")
        else:
            color.append("red")

        info = f"Placa: {row['Placa']}<br>Vida: {row['Vida']} meses<br>Posição: {sigla}<br>Sulco: {sulco}mm"
        text.append(info)
        labels.append(sigla)

fig_truck = go.Figure()
fig_truck.add_trace(go.Scatter(
    x=x, y=y, mode='markers+text',
    marker=dict(size=50, color=color, line=dict(width=2, color='black')),
    text=labels,
    textposition="middle center",
    hoverinfo='text',
    hovertext=text
))

fig_truck.update_layout(
    title="Mapa de Pneus do Truck",
    xaxis=dict(showgrid=False, zeroline=False, tickvals=[]),
    yaxis=dict(showgrid=False, zeroline=False, tickvals=[]),
    plot_bgcolor="white",
    height=400,
    width=800
)

st.plotly_chart(fig_truck, use_container_width=True)

# -----------------------------
# Conclusões / Alertas
# -----------------------------
st.subheader("⚠️ Conclusões e Alertas")
if not pneus_criticos.empty:
    st.warning(f"Existem {len(pneus_criticos)} pneus com sulco crítico, atenção à substituição!")
else:
    st.success("Todos os pneus dentro da faixa segura de sulco.")

st.info("Análise concluída. Todos os indicadores e mapeamentos estão atualizados com base nos dados fornecidos.")
