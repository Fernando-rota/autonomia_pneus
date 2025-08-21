import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(page_title="Análise de Vida Útil de Pneus", layout="wide")

st.title("Análise de Vida Útil de Pneus")

# Upload do arquivo
arquivo = st.file_uploader("Escolha o arquivo Excel", type=["xlsx", "xls"])
if arquivo is not None:
    # Lê todas as abas
    df = pd.read_excel(arquivo, sheet_name=None)

    # Lista para armazenar dados combinados
    df_completo = []

    # Processa cada aba
    for nome_aba, dados in df.items():
        st.subheader(f"Aba: {nome_aba}")

        # Criar coluna Tipo Pneu a partir da coluna 'Vida'
        dados["Tipo Pneu"] = dados["Vida"].fillna("Novo")

        # Função para extrair km da Observação
        def extrair_km_observacao(texto):
            if pd.isna(texto):
                return None
            match = re.search(r"(\d+)\s*km", str(texto))
            if match:
                return int(match.group(1))
            return None

        dados["Observação - Km"] = dados["Observação"].apply(extrair_km_observacao)

        # Calcular Km Rodado até Aferição
        dados["Km Rodado até Aferição"] = dados["Observação - Km"] - dados["Hodômetro Inicial"]
        dados["Km Rodado até Aferição"] = dados["Km Rodado até Aferição"].fillna(0)

        # KPIs básicos
        total_pneus = len(dados)
        total_km_rodado = dados["Km Rodado até Aferição"].sum()
        st.metric("Total de Pneus", total_pneus)
        st.metric("Total Km Rodado", f"{total_km_rodado:,} km")

        # Gráfico de Km Rodado por Tipo de Pneu
        fig = px.box(
            dados, 
            x="Tipo Pneu", 
            y="Km Rodado até Aferição", 
            points="all", 
            title="Distribuição de Km Rodado por Tipo de Pneu"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabela detalhada
        st.dataframe(dados[[
            "Veículo - Descrição", 
            "Veículo - Placa", 
            "Tipo Pneu", 
            "Hodômetro Inicial", 
            "Observação - Km", 
            "Km Rodado até Aferição"
        ]])

        # Armazena para análise combinada
        df_completo.append(dados)

    # -----------------------
    # Aba de levantamento histórico de trocas
    # -----------------------
    st.header("Levantamento Histórico de Troca de Pneus")

    if df_completo:
        df_total = pd.concat(df_completo, ignore_index=True)

        # Agrupa por Tipo de Pneu
        resumo = df_total.groupby("Tipo Pneu")["Km Rodado até Aferição"].agg(
            Total_Pneus="count",
            Km_Médio="mean",
            Km_Mínimo="min",
            Km_Máximo="max"
        ).reset_index()

        # Formatação para exibir KM com separador de milhar
        resumo["Km_Médio"] = resumo["Km_Médio"].apply(lambda x: f"{x:,.0f} km")
        resumo["Km_Mínimo"] = resumo["Km_Mínimo"].apply(lambda x: f"{x:,.0f} km")
        resumo["Km_Máximo"] = resumo["Km_Máximo"].apply(lambda x: f"{x:,.0f} km")

        st.subheader("Resumo por Tipo de Pneu")
        st.dataframe(resumo)

        # Gráfico comparativo de Km médio por Tipo de Pneu
        fig2 = px.bar(
            df_total.groupby("Tipo Pneu")["Km Rodado até Aferição"].mean().reset_index(),
            x="Tipo Pneu",
            y="Km Rodado até Aferição",
            text="Km Rodado até Aferição",
            title="Km Médio Rodado por Tipo de Pneu"
        )
        fig2.update_traces(texttemplate='%{y:.0f} km', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)
