import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel de Autonomia dos Pneus", layout="wide")

st.title("📊 Painel de Autonomia dos Pneus")
st.markdown("⬆️ Faça upload da planilha com as abas de manutenção e movimentação")

uploaded_file = st.file_uploader("Upload", type=["xlsx"], key="planilha_pneus")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manutencao = pd.read_excel(xls, sheet_name="manutencao")
        df_pneu = pd.read_excel(xls, sheet_name="pneu")

        # Padroniza colunas
        df_manutencao.columns = df_manutencao.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip().str.upper()

        # Padroniza nome da coluna PLACA
        if 'VEÍCULO - PLACA' in df_pneu.columns:
            df_pneu.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)

        # Converte coluna de autonomia (se existir)
        if 'AUTONOMIA' in df_pneu.columns:
            df_pneu['AUTONOMIA'] = pd.to_numeric(df_pneu['AUTONOMIA'], errors='coerce')

        # Verifica se as colunas essenciais existem
        if 'PLACA' not in df_manutencao.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'manutencao'")
        elif 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'pneu'")
        else:
            # Filtros laterais
            placas = sorted(set(df_manutencao['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
            eixos = sorted(df_pneu['EIXO'].dropna().unique()) if 'EIXO' in df_pneu.columns else []
            marcas = sorted(df_pneu['MARCA'].dropna().unique()) if 'MARCA' in df_pneu.columns else []

            st.sidebar.header("Filtros")
            selected_placa = st.sidebar.multiselect("Filtrar por Placa", placas, default=placas)
            selected_eixo = st.sidebar.multiselect("Filtrar por Eixo", eixos, default=eixos)
            selected_marca = st.sidebar.multiselect("Filtrar por Marca", marcas, default=marcas)

            # Aplica filtros
            if selected_placa:
                df_manutencao = df_manutencao[df_manutencao['PLACA'].isin(selected_placa)]
                df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placa)]
            if selected_eixo and 'EIXO' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['EIXO'].isin(selected_eixo)]
            if selected_marca and 'MARCA' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['MARCA'].isin(selected_marca)]

            abas = st.tabs(["📊 Resumo Geral", "📈 Gráficos", "🔍 Detalhamento", "⚠️ Pneus com Menor Autonomia"])

            with abas[0]:
                st.subheader("📊 Estatísticas Gerais")
                if not df_pneu.empty:
                    st.dataframe(df_pneu.describe(include='all'))
                else:
                    st.warning("Nenhum dado encontrado com os filtros selecionados.")

            with abas[1]:
                st.subheader("📈 Visualizações Gráficas")
                if 'AUTONOMIA' in df_pneu.columns:
                    col1, col2 = st.columns(2)

                    with col1:
                        fig1 = px.histogram(df_pneu, x='AUTONOMIA', nbins=30, title='Distribuição da Autonomia dos Pneus')
                        st.plotly_chart(fig1, use_container_width=True)

                    with col2:
                        if 'MARCA' in df_pneu.columns:
                            fig2 = px.box(df_pneu, x='MARCA', y='AUTONOMIA', title='Autonomia por Marca')
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.info("Coluna 'MARCA' não encontrada.")

                else:
                    st.warning("Coluna 'AUTONOMIA' não encontrada.")

            with abas[2]:
                st.subheader("🔍 Detalhamento dos Registros")
                st.dataframe(df_pneu)

            with abas[3]:
                st.subheader("⚠️ Top 10 Pneus com Menor Autonomia")
                if 'AUTONOMIA' in df_pneu.columns:
                    df_piores = df_pneu.sort_values(by='AUTONOMIA').head(10)
                    st.dataframe(df_piores)
                else:
                    st.warning("Coluna 'AUTONOMIA' não encontrada.")
    else:
        st.error("❌ As abas 'manutencao' e 'pneu' devem estar presentes na planilha.")
