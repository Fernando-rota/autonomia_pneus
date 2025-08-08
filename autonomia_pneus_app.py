import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel de Manutenção e Movimentação de Pneus", layout="wide")

st.title("📊 Painel de Manutenção e Movimentação de Pneus")
st.markdown("⬆️ Faça upload da planilha com as abas 'manutencao' e 'pneu'")

uploaded_file = st.file_uploader("Upload da Planilha Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manut = pd.read_excel(xls, sheet_name='manutencao')
        df_pneu = pd.read_excel(xls, sheet_name='pneu')

        # Normaliza colunas
        df_manut.columns = df_manut.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip().str.upper()

        # Conversão de datas
        if 'DATA DA MANUTENÇÃO' in df_manut.columns:
            df_manut['DATA DA MANUTENÇÃO'] = pd.to_datetime(df_manut['DATA DA MANUTENÇÃO'], errors='coerce')
        if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
            df_pneu['DATA DA MOVIMENTAÇÃO'] = pd.to_datetime(df_pneu['DATA DA MOVIMENTAÇÃO'], errors='coerce')

        # Converter VALOR para numérico (pneu)
        if 'VALOR' in df_pneu.columns:
            df_pneu['VALOR'] = pd.to_numeric(df_pneu['VALOR'], errors='coerce')

        # Padroniza coluna PLACA
        for df in [df_manut, df_pneu]:
            if 'VEÍCULO - PLACA' in df.columns:
                df.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)

        # Checar colunas obrigatórias
        if 'PLACA' not in df_manut.columns or 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna PLACA é obrigatória nas duas abas.")
        else:
            # Filtros
            placas = sorted(set(df_manut['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
            selected_placas = st.sidebar.multiselect("Selecione as Placas", placas, default=placas)

            # Filtro datas com valores mínimos e máximos combinados
            data_min_manut = df_manut['DATA DA MANUTENÇÃO'].min() if 'DATA DA MANUTENÇÃO' in df_manut.columns else None
            data_max_manut = df_manut['DATA DA MANUTENÇÃO'].max() if 'DATA DA MANUTENÇÃO' in df_manut.columns else None
            data_min_pneu = df_pneu['DATA DA MOVIMENTAÇÃO'].min() if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns else None
            data_max_pneu = df_pneu['DATA DA MOVIMENTAÇÃO'].max() if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns else None

            data_min = min(filter(None, [data_min_manut, data_min_pneu]))
            data_max = max(filter(None, [data_max_manut, data_max_pneu]))

            selected_data = st.sidebar.date_input("Selecione intervalo de datas", [data_min, data_max])

            # Aplica filtros
            if selected_placas:
                df_manut = df_manut[df_manut['PLACA'].isin(selected_placas)]
                df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placas)]

            if len(selected_data) == 2:
                start_date, end_date = pd.to_datetime(selected_data[0]), pd.to_datetime(selected_data[1])
                if 'DATA DA MANUTENÇÃO' in df_manut.columns:
                    df_manut = df_manut[(df_manut['DATA DA MANUTENÇÃO'] >= start_date) & (df_manut['DATA DA MANUTENÇÃO'] <= end_date)]
                if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
                    df_pneu = df_pneu[(df_pneu['DATA DA MOVIMENTAÇÃO'] >= start_date) & (df_pneu['DATA DA MOVIMENTAÇÃO'] <= end_date)]

            st.header("📊 Indicadores Gerais")

            if df_manut.empty:
                st.warning("Nenhum dado de manutenção após filtro.")
            else:
                total_manut = len(df_manut)
                st.metric("Total de Manutenções", total_manut)

                if 'DESCRIÇÃO DA MANUTENÇÃO' in df_manut.columns:
                    manut_tipo = df_manut['DESCRIÇÃO DA MANUTENÇÃO'].value_counts()
                    st.subheader("Tipos de Manutenção")
                    st.dataframe(manut_tipo)

                if 'KM DO VEÍCULO' in df_manut.columns:
                    km_medio = df_manut.groupby('PLACA')['KM DO VEÍCULO'].apply(lambda x: x.sort_values().diff().mean()).dropna()
                    st.subheader("KM Médio entre Manutenções por Veículo")
                    st.dataframe(km_medio.astype(int))

            if df_pneu.empty:
                st.warning("Nenhum dado de movimentação de pneus após filtro.")
            else:
                total_pneu = len(df_pneu)
                st.metric("Total de Movimentações de Pneus", total_pneu)

                if 'TIPO DA MOVIMENTAÇÃO' in df_pneu.columns:
                    pneu_tipo = df_pneu['TIPO DA MOVIMENTAÇÃO'].value_counts()
                    st.subheader("Tipos de Movimentação de Pneus")
                    st.dataframe(pneu_tipo)

                if 'VALOR' in df_pneu.columns:
                    total_valor = df_pneu['VALOR'].sum()
                    st.metric("Valor Total Gasto com Pneus (R$)", f"{total_valor:,.2f}")

            # Gráficos simples para confirmar visualização
            st.header("📈 Gráficos")

            if not df_manut.empty and 'DATA DA MANUTENÇÃO' in df_manut.columns:
                fig1 = px.histogram(df_manut, x='DATA DA MANUTENÇÃO', color='PLACA', nbins=30,
                                    title="Frequência de Manutenções por Veículo")
                st.plotly_chart(fig1, use_container_width=True)

            if not df_pneu.empty and 'TIPO DA MOVIMENTAÇÃO' in df_pneu.columns:
                fig2 = px.histogram(df_pneu, x='TIPO DA MOVIMENTAÇÃO', color='PLACA',
                                    title="Movimentação de Pneus por Tipo e Veículo")
                st.plotly_chart(fig2, use_container_width=True)
