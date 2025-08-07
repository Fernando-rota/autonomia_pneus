import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel de Autonomia dos Pneus", layout="wide")

st.title("📊 Painel de Autonomia dos Pneus")
st.markdown("⬆️ Faça upload da planilha com as abas de manutenção e movimentação")

# Adiciona key para evitar conflitos se houver múltiplos uploaders (mesmo que não tenha aqui)
uploaded_file = st.file_uploader("Upload", type=["xlsx"], key="planilha_pneus")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manutencao = pd.read_excel(xls, sheet_name="manutencao")
        df_pneu = pd.read_excel(xls, sheet_name="pneu")

        # Padroniza colunas: remove espaços e coloca maiúsculas nas colunas do manutencao
        df_manutencao.columns = df_manutencao.columns.str.strip().str.upper()
        # Remove espaços nas colunas do pneu
        df_pneu.columns = df_pneu.columns.str.strip()

        # Padroniza nome da coluna placa na aba pneu
        if 'Veículo - Placa' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa': 'PLACA'}, inplace=True)
        elif 'Veículo - Placa ' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa ': 'PLACA'}, inplace=True)

        # Confirma colunas obrigatórias
        if 'PLACA' not in df_manutencao.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'manutencao'")
        elif 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'pneu'")
        else:
            # Gera opções de filtro
            placas = sorted(set(df_manutencao['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
            eixos = sorted(df_pneu['Eixo'].dropna().unique()) if 'Eixo' in df_pneu.columns else []
            marcas = sorted(df_pneu['Marca'].dropna().unique()) if 'Marca' in df_pneu.columns else []

            st.sidebar.header("Filtros")

            selected_placa = st.sidebar.multiselect("Filtrar por Placa", placas, default=placas)
            selected_eixo = st.sidebar.multiselect("Filtrar por Eixo", eixos, default=eixos)
            selected_marca = st.sidebar.multiselect("Filtrar por Marca", marcas, default=marcas)

            # Aplica filtros
            if selected_placa:
                df_manutencao = df_manutencao[df_manutencao['PLACA'].isin(selected_placa)]
                df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placa)]
            if selected_eixo and 'Eixo' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Eixo'].isin(selected_eixo)]
            if selected_marca and 'Marca' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Marca'].isin(selected_marca)]

            # Layout das abas
            abas = st.tabs(["📊 Resumo Geral", "🔍 Detalhamento", "⚠️ Pneus com Menor Autonomia"])

            with abas[0]:
                st.subheader("📈 Estatísticas de Autonomia")
                if not df_pneu.empty:
                    st.dataframe(df_pneu.describe(include='all'))
                else:
                    st.warning("Nenhum dado encontrado com os filtros selecionados.")

            with abas[1]:
                st.subheader("🔍 Detalhamento dos Registros")
                st.dataframe(df_pneu)

            with abas[2]:
                st.subheader("⚠️ Pneus com Menor Autonomia")
                if 'Autonomia' in df_pneu.columns:
                    df_piores = df_pneu.sort_values(by='Autonomia').head(10)
                    st.dataframe(df_piores)
                else:
                    st.warning("Coluna 'Autonomia' não encontrada.")
    else:
        st.error("❌ As abas 'manutencao' e 'pneu' devem estar presentes na planilha.")
