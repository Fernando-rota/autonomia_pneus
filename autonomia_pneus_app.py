import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel de Autonomia dos Pneus", layout="wide")

st.title("📊 Painel de Autonomia dos Pneus")
st.markdown("⬆️ Faça upload da planilha com as abas de manutenção e movimentação")

uploaded_file = st.file_uploader("Upload", type=["xlsx"])

if uploaded_file:
    # Leitura das abas
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manutencao = pd.read_excel(xls, sheet_name="manutencao")
        df_pneu = pd.read_excel(xls, sheet_name="pneu")

        # Padronizar nome de colunas
        df_manutencao.columns = df_manutencao.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip()

        # Renomear a coluna de placa na aba pneu
        if 'Veículo - Placa' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa': 'PLACA'}, inplace=True)
        elif 'Veículo - Placa ' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa ': 'PLACA'}, inplace=True)

        # Verificação de coluna obrigatória
        if 'PLACA' not in df_manutencao.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'manutencao'")
        elif 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'pneu'")
        else:
            # Filtros interativos
            placas = sorted(set(df_manutencao['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
            eixos = sorted(df_pneu['Eixo'].dropna().unique()) if 'Eixo' in df_pneu.columns else []
            marcas = sorted(df_pneu['Marca'].dropna().unique()) if 'Marca' in df_pneu.columns else []

            col1, col2, col3 = st.sidebar.columns(3)
            selected_placa = st.sidebar.multiselect("Filtrar por Placa", placas)
            selected_eixo = st.sidebar.multiselect("Filtrar por Eixo", eixos)
            selected_marca = st.sidebar.multiselect("Filtrar por Marca", marcas)

            # Aplicar filtros
            if selected_placa:
                df_manutencao = df_manutencao[df_manutencao['PLACA'].isin(selected_placa)]
                df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placa)]
            if selected_eixo and 'Eixo' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Eixo'].isin(selected_eixo)]
            if selected_marca and 'Marca' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Marca'].isin(selected_marca)]

            # Separação por abas
            aba = st.tabs(["📊 Resumo Geral", "🔍 Detalhamento", "⚠️ Pneus com Menor Autonomia"])

            with aba[0]:
                st.subheader("📈 Estatísticas de Autonomia")
                if not df_pneu.empty:
                    st.dataframe(df_pneu.describe(include='all'))
                else:
                    st.warning("Nenhum dado encontrado com os filtros selecionados.")

            with aba[1]:
                st.subheader("🔍 Detalhamento dos Registros")
                st.dataframe(df_pneu)

            with aba[2]:
                st.subheader("⚠️ Pneus com Menor Autonomia")
                if 'Autonomia' in df_pneu.columns:
                    df_piores = df_pneu.sort_values(by='Autonomia').head(10)
                    st.dataframe(df_piores)
                else:
                    st.warning("Coluna 'Autonomia' não encontrada.")
    else:
        st.error("❌ As abas 'manutencao' e 'pneu' devem estar presentes na planilha.")
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel de Autonomia dos Pneus", layout="wide")

st.title("📊 Painel de Autonomia dos Pneus")
st.markdown("⬆️ Faça upload da planilha com as abas de manutenção e movimentação")

uploaded_file = st.file_uploader("Upload", type=["xlsx"])

if uploaded_file:
    # Leitura das abas
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manutencao = pd.read_excel(xls, sheet_name="manutencao")
        df_pneu = pd.read_excel(xls, sheet_name="pneu")

        # Padronizar nome de colunas
        df_manutencao.columns = df_manutencao.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip()

        # Renomear a coluna de placa na aba pneu
        if 'Veículo - Placa' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa': 'PLACA'}, inplace=True)
        elif 'Veículo - Placa ' in df_pneu.columns:
            df_pneu.rename(columns={'Veículo - Placa ': 'PLACA'}, inplace=True)

        # Verificação de coluna obrigatória
        if 'PLACA' not in df_manutencao.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'manutencao'")
        elif 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna obrigatória ausente: PLACA na aba 'pneu'")
        else:
            # Filtros interativos
            placas = sorted(set(df_manutencao['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
            eixos = sorted(df_pneu['Eixo'].dropna().unique()) if 'Eixo' in df_pneu.columns else []
            marcas = sorted(df_pneu['Marca'].dropna().unique()) if 'Marca' in df_pneu.columns else []

            col1, col2, col3 = st.sidebar.columns(3)
            selected_placa = st.sidebar.multiselect("Filtrar por Placa", placas)
            selected_eixo = st.sidebar.multiselect("Filtrar por Eixo", eixos)
            selected_marca = st.sidebar.multiselect("Filtrar por Marca", marcas)

            # Aplicar filtros
            if selected_placa:
                df_manutencao = df_manutencao[df_manutencao['PLACA'].isin(selected_placa)]
                df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placa)]
            if selected_eixo and 'Eixo' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Eixo'].isin(selected_eixo)]
            if selected_marca and 'Marca' in df_pneu.columns:
                df_pneu = df_pneu[df_pneu['Marca'].isin(selected_marca)]

            # Separação por abas
            aba = st.tabs(["📊 Resumo Geral", "🔍 Detalhamento", "⚠️ Pneus com Menor Autonomia"])

            with aba[0]:
                st.subheader("📈 Estatísticas de Autonomia")
                if not df_pneu.empty:
                    st.dataframe(df_pneu.describe(include='all'))
                else:
                    st.warning("Nenhum dado encontrado com os filtros selecionados.")

            with aba[1]:
                st.subheader("🔍 Detalhamento dos Registros")
                st.dataframe(df_pneu)

            with aba[2]:
                st.subheader("⚠️ Pneus com Menor Autonomia")
                if 'Autonomia' in df_pneu.columns:
                    df_piores = df_pneu.sort_values(by='Autonomia').head(10)
                    st.dataframe(df_piores)
                else:
                    st.warning("Coluna 'Autonomia' não encontrada.")
    else:
        st.error("❌ As abas 'manutencao' e 'pneu' devem estar presentes na planilha.")
