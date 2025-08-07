import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Dashboard de Autonomia dos Pneus")

st.title("📊 Dashboard de Autonomia dos Pneus")

uploaded_file = st.file_uploader("📂 Envie a planilha de controle de pneus (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Detecta os nomes das abas de forma flexível
    xls = pd.ExcelFile(uploaded_file)
    sheet_manutencao = next((s for s in xls.sheet_names if 'manutencao' in s.lower()), None)
    sheet_movimentacao = next((s for s in xls.sheet_names if 'pneu' in s.lower()), None)

    if not sheet_manutencao or not sheet_movimentacao:
        st.error("❌ Não foi possível encontrar as abas 'manutencao' e 'pneu'. Verifique os nomes.")
        st.stop()

    df_manutencao = pd.read_excel(xls, sheet_name=sheet_manutencao)
    df_pneu = pd.read_excel(xls, sheet_name=sheet_movimentacao)

    # Preprocessamento: garante que as colunas importantes existam
    required_columns = ['PLACA', 'MARCA', 'EIXO', 'AUTONOMIA (km)']
    for col in required_columns:
        if col not in df_pneu.columns:
            st.error(f"❌ Coluna obrigatória ausente: {col}")
            st.stop()

    # Filtros interativos
    placas = sorted(df_pneu['PLACA'].dropna().unique())
    marcas = sorted(df_pneu['MARCA'].dropna().unique())
    eixos = sorted(df_pneu['EIXO'].dropna().unique())

    with st.sidebar:
        st.header("🔎 Filtros")
        selected_placas = st.multiselect("Placa", placas, default=placas)
        selected_marcas = st.multiselect("Marca", marcas, default=marcas)
        selected_eixos = st.multiselect("Eixo", eixos, default=eixos)

    # Aplica filtros
    df_filtered = df_pneu[
        df_pneu['PLACA'].isin(selected_placas) &
        df_pneu['MARCA'].isin(selected_marcas) &
        df_pneu['EIXO'].isin(selected_eixos)
    ]

    if df_filtered.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    # Tabela com destaque nos pneus com menor autonomia
    menor_autonomia = df_filtered['AUTONOMIA (km)'].quantile(0.1)

    df_filtered['DESTAQUE'] = df_filtered['AUTONOMIA (km)'].apply(
        lambda x: '🔴 Baixa Autonomia' if x <= menor_autonomia else ''
    )

    aba1, aba2, aba3 = st.tabs(["📋 Visão Geral", "🔧 Manutenção", "🛞 Pneus com Menor Autonomia"])

    with aba1:
        st.subheader("📈 Dados Filtrados")
        st.dataframe(df_filtered.sort_values(by='AUTONOMIA (km)', ascending=False), use_container_width=True)

        media_geral = df_filtered['AUTONOMIA (km)'].mean()
        st.metric("📌 Autonomia Média dos Pneus Filtrados", f"{media_geral:,.0f} km")

    with aba2:
        st.subheader("🔧 Dados de Manutenção")
        st.dataframe(df_manutencao, use_container_width=True)

    with aba3:
        st.subheader("🛞 Pneus com Baixa Autonomia (10% menores)")
        st.dataframe(
            df_filtered[df_filtered['AUTONOMIA (km)'] <= menor_autonomia].sort_values(by='AUTONOMIA (km)'),
            use_container_width=True
        )
        st.info(f"{(df_filtered['AUTONOMIA (km)'] <= menor_autonomia).sum()} pneus estão no grupo com menor autonomia (até {menor_autonomia:,.0f} km).")

else:
    st.warning("👆 Envie uma planilha .xlsx para começar.")
