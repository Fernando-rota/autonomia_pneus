import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

st.set_page_config(page_title="Autonomia dos Pneus", layout="wide")

st.title("📊 Painel de Autonomia dos Pneus")

uploaded_file = st.file_uploader("📥 Faça upload da planilha com as abas de manutenção e movimentação", type=["xlsx"])

# Função para interpretar sigla de posição do pneu
def interpretar_posicao(sigla):
    if pd.isna(sigla) or len(sigla) != 3:
        return ("Desconhecido", "Desconhecido", "Desconhecido")
    eixo = sigla[0]
    lado = "Direito" if sigla[1] == "D" else "Esquerdo"
    posicao = "Interno" if sigla[2] == "I" else "Externo"
    return (eixo, lado, posicao)

if uploaded_file:
    # Leitura das duas abas
    aba_manut = pd.read_excel(uploaded_file, sheet_name=0)
    aba_pneu = pd.read_excel(uploaded_file, sheet_name=1)

    # Filtro: apenas posições válidas com prefixo D (ex: DDI, DDE)
    aba_pneu = aba_pneu[aba_pneu['Sigla da Posição do Pneu'].str.startswith("D", na=False)]

    # Conversões
    aba_pneu['Data da Movimentação'] = pd.to_datetime(aba_pneu['Data da Movimentação'], errors='coerce')
    aba_pneu['Pneu - Hodômetro'] = pd.to_numeric(aba_pneu['Pneu - Hodômetro'], errors='coerce')

    # Decodificar posição
    posicoes = aba_pneu['Sigla da Posição do Pneu'].apply(interpretar_posicao)
    aba_pneu[['Eixo', 'Lado', 'Posição']] = pd.DataFrame(posicoes.tolist(), index=aba_pneu.index)

    # Agrupar por pneu
    df_autonomia = aba_pneu.groupby('Pneu - Série').agg({
        'Pneu - Hodômetro': ['min', 'max'],
        'Data da Movimentação': ['min', 'max'],
        'Veículo - Placa': 'first',
        'Pneu - Marca (Atual)': 'first',
        'Eixo': 'first',
        'Lado': 'first',
        'Posição': 'first'
    }).reset_index()

    df_autonomia.columns = [
        'Pneu - Série', 'KM Inicial', 'KM Final', 'Data Inicial', 'Data Final',
        'Placa', 'Marca', 'Eixo', 'Lado', 'Posição'
    ]
    df_autonomia['Autonomia (KM)'] = df_autonomia['KM Final'] - df_autonomia['KM Inicial']
    df_autonomia = df_autonomia.dropna(subset=['Autonomia (KM)'])
    df_autonomia = df_autonomia[df_autonomia['Autonomia (KM)'] > 0]

    # Filtros
    with st.sidebar:
        st.header("🎛️ Filtros")
        placas = st.multiselect("Filtrar por Placa", options=sorted(df_autonomia['Placa'].unique()), default=None)
        eixos = st.multiselect("Filtrar por Eixo", options=sorted(df_autonomia['Eixo'].unique()), default=None)
        marcas = st.multiselect("Filtrar por Marca", options=sorted(df_autonomia['Marca'].unique()), default=None)

    # Aplicar filtros
    df_filtrado = df_autonomia.copy()
    if placas:
        df_filtrado = df_filtrado[df_filtrado['Placa'].isin(placas)]
    if eixos:
        df_filtrado = df_filtrado[df_filtrado['Eixo'].isin(eixos)]
    if marcas:
        df_filtrado = df_filtrado[df_filtrado['Marca'].isin(marcas)]

    # Tabs (Abas)
    aba1, aba2, aba3 = st.tabs(["📊 Resumo Geral", "📋 Detalhamento", "⚠️ Pneus com Menor Autonomia"])

    with aba1:
        st.subheader("📊 Estatísticas de Autonomia")
        if not df_filtrado.empty:
            autonomias = df_filtrado['Autonomia (KM)']
            media = autonomias.mean()
            desvio = autonomias.std(ddof=1)
            n = len(autonomias)
            confidence = 0.85
            t_value = stats.t.ppf((1 + confidence) / 2, df=n - 1)
            margem_erro = t_value * desvio / np.sqrt(n)
            intervalo_inf = media - margem_erro
            intervalo_sup = media + margem_erro

            col1, col2, col3 = st.columns(3)
            col1.metric("🛞 Média de Autonomia", f"{media:,.0f} KM")
            col2.metric("🔐 Confiança 85%", f"{intervalo_inf:,.0f} KM - {intervalo_sup:,.0f} KM")
            col3.metric("📦 Total de Pneus", f"{n}")

            st.bar_chart(df_filtrado.set_index('Pneu - Série')['Autonomia (KM)'])
        else:
            st.warning("Nenhum dado encontrado com os filtros selecionados.")

    with aba2:
        st.subheader("📋 Detalhamento por Pneu")
        st.dataframe(df_filtrado.sort_values(by="Autonomia (KM)", ascending=False), use_container_width=True)

    with aba3:
        st.subheader("⚠️ Pneus com Menor Autonomia")
        qtd = st.slider("Quantidade de pneus a destacar", 3, 20, 5)
        df_menor = df_filtrado.sort_values(by="Autonomia (KM)").head(qtd)
        st.dataframe(df_menor, use_container_width=True)
        st.bar_chart(df_menor.set_index('Pneu - Série')['Autonomia (KM)'])
