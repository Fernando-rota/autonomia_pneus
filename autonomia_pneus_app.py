import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel Completo de Manutenção e Pneus", layout="wide")

st.title("🚛 Painel Completo de Manutenção e Movimentação de Pneus")
st.markdown("⬆️ Faça upload da planilha com abas 'manutencao' e 'pneu' para análise completa")

uploaded_file = st.file_uploader("Carregue sua planilha Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manut = pd.read_excel(xls, sheet_name='manutencao')
        df_pneu = pd.read_excel(xls, sheet_name='pneu')

        # --- Normalização colunas ---
        df_manut.columns = df_manut.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip().str.upper()

        # --- Conversão datas ---
        if 'DATA DA MANUTENÇÃO' in df_manut.columns:
            df_manut['DATA DA MANUTENÇÃO'] = pd.to_datetime(df_manut['DATA DA MANUTENÇÃO'], errors='coerce')
        if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
            df_pneu['DATA DA MOVIMENTAÇÃO'] = pd.to_datetime(df_pneu['DATA DA MOVIMENTAÇÃO'], errors='coerce')

        # --- Converter VALOR para numérico ---
        if 'VALOR' in df_pneu.columns:
            df_pneu['VALOR'] = pd.to_numeric(df_pneu['VALOR'], errors='coerce')

        # --- Ajustar coluna PLACA ---
        for df in [df_manut, df_pneu]:
            if 'VEÍCULO - PLACA' in df.columns:
                df.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)

        # --- Check colunas essenciais ---
        if 'PLACA' not in df_manut.columns or 'PLACA' not in df_pneu.columns:
            st.error("❌ Coluna PLACA é obrigatória nas abas 'manutencao' e 'pneu'")
            st.stop()

        # --- Filtros no sidebar ---
        placas = sorted(set(df_manut['PLACA'].dropna().unique()) | set(df_pneu['PLACA'].dropna().unique()))
        selected_placas = st.sidebar.multiselect("Filtrar por Placas", placas, default=placas)

        # Datas mínimas e máximas
        data_min_manut = df_manut['DATA DA MANUTENÇÃO'].min() if 'DATA DA MANUTENÇÃO' in df_manut.columns else None
        data_max_manut = df_manut['DATA DA MANUTENÇÃO'].max() if 'DATA DA MANUTENÇÃO' in df_manut.columns else None
        data_min_pneu = df_pneu['DATA DA MOVIMENTAÇÃO'].min() if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns else None
        data_max_pneu = df_pneu['DATA DA MOVIMENTAÇÃO'].max() if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns else None
        data_min = min(filter(None, [data_min_manut, data_min_pneu]))
        data_max = max(filter(None, [data_max_manut, data_max_pneu]))
        selected_datas = st.sidebar.date_input("Intervalo de datas", [data_min, data_max])

        # Tipo manutenção e movimentação
        manut_types = df_manut['DESCRIÇÃO DA MANUTENÇÃO'].dropna().unique() if 'DESCRIÇÃO DA MANUTENÇÃO' in df_manut.columns else []
        selected_manut_types = st.sidebar.multiselect("Tipos de Manutenção", manut_types, default=manut_types)

        pneu_mov_types = df_pneu['TIPO DA MOVIMENTAÇÃO'].dropna().unique() if 'TIPO DA MOVIMENTAÇÃO' in df_pneu.columns else []
        selected_pneu_mov_types = st.sidebar.multiselect("Tipos de Movimentação Pneus", pneu_mov_types, default=pneu_mov_types)

        marcas = df_pneu['MARCA'].dropna().unique() if 'MARCA' in df_pneu.columns else []
        selected_marcas = st.sidebar.multiselect("Marcas de Pneus", marcas, default=marcas)

        # Aplicar filtros
        if selected_placas:
            df_manut = df_manut[df_manut['PLACA'].isin(selected_placas)]
            df_pneu = df_pneu[df_pneu['PLACA'].isin(selected_placas)]

        if len(selected_datas) == 2:
            start_date, end_date = pd.to_datetime(selected_datas[0]), pd.to_datetime(selected_datas[1])
            if 'DATA DA MANUTENÇÃO' in df_manut.columns:
                df_manut = df_manut[
                    (df_manut['DATA DA MANUTENÇÃO'] >= start_date) & (df_manut['DATA DA MANUTENÇÃO'] <= end_date)]
            if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
                df_pneu = df_pneu[
                    (df_pneu['DATA DA MOVIMENTAÇÃO'] >= start_date) & (df_pneu['DATA DA MOVIMENTAÇÃO'] <= end_date)]

        if selected_manut_types:
            df_manut = df_manut[df_manut['DESCRIÇÃO DA MANUTENÇÃO'].isin(selected_manut_types)]
        if selected_pneu_mov_types:
            df_pneu = df_pneu[df_pneu['TIPO DA MOVIMENTAÇÃO'].isin(selected_pneu_mov_types)]
        if selected_marcas:
            df_pneu = df_pneu[df_pneu['MARCA'].isin(selected_marcas)]

        st.header("📈 Indicadores Gerais")

        # KPIs Manutenção
        total_manut = len(df_manut)
        st.metric("Total de Manutenções", total_manut)

        # Média de KM entre manutenções
        if 'KM DO VEÍCULO' in df_manut.columns and total_manut > 1:
            km_medios = df_manut.groupby('PLACA')['KM DO VEÍCULO'].apply(lambda x: x.sort_values().diff().mean())
            st.metric("KM Médio entre Manutenções (média geral)", f"{km_medios.mean():,.0f} km")

        # KPIs Pneus
        total_pneu = len(df_pneu)
        st.metric("Total de Movimentações de Pneus", total_pneu)

        if 'VALOR' in df_pneu.columns:
            valor_total = df_pneu['VALOR'].sum()
            st.metric("Valor Total Gasto em Pneus (R$)", f"{valor_total:,.2f}")

        # Autonomia: alertas para pneus com autonomia baixa
        if 'AUTONOMIA' in df_pneu.columns:
            df_pneu['AUTONOMIA'] = pd.to_numeric(df_pneu['AUTONOMIA'], errors='coerce')
            alert_pneus = df_pneu[df_pneu['AUTONOMIA'] < 5000]  # exemplo limiar 5000 km
            st.subheader("⚠️ Pneus com Autonomia Baixa (< 5000 km)")
            st.dataframe(alert_pneus[['REFERÊNCIA DO PNEU', 'PLACA', 'AUTONOMIA', 'DATA DA MOVIMENTAÇÃO']])

        # --- Gráficos interativos ---

        abas = st.tabs(["Resumo", "Manutenções", "Movimentação Pneus", "Análise Temporal", "Detalhamento"])

        with abas[0]:
            st.subheader("Resumo por Veículo")

            # Manutenções por veículo
            manut_placa = df_manut.groupby('PLACA').size().reset_index(name='Qtd Manutenções')
            # Pneus por veículo
            pneu_placa = df_pneu.groupby('PLACA').size().reset_index(name='Qtd Movimentações Pneus')

            resumo = pd.merge(manut_placa, pneu_placa, on='PLACA', how='outer').fillna(0)
            st.dataframe(resumo)

            # Gráfico barras com manutenções e pneus por veículo
            fig = px.bar(resumo.melt(id_vars='PLACA', value_vars=['Qtd Manutenções', 'Qtd Movimentações Pneus']),
                         x='PLACA', y='value', color='variable',
                         title='Quantidade de Manutenções e Movimentações de Pneus por Veículo')
            st.plotly_chart(fig, use_container_width=True)

        with abas[1]:
            st.subheader("Manutenções - Detalhes e Tipos")

            # Frequência manutenções por tipo
            manut_tipo = df_manut['DESCRIÇÃO DA MANUTENÇÃO'].value_counts().reset_index()
            manut_tipo.columns = ['Tipo de Manutenção', 'Quantidade']
            st.dataframe(manut_tipo)

            # Gráfico pizza
            fig_pizza = px.pie(manut_tipo, names='Tipo de Manutenção', values='Quantidade', title='Distribuição dos Tipos de Manutenção')
            st.plotly_chart(fig_pizza, use_container_width=True)

        with abas[2]:
            st.subheader("Movimentação de Pneus - Tipos e Valores")

            pneu_tipo = df_pneu['TIPO DA MOVIMENTAÇÃO'].value_counts().reset_index()
            pneu_tipo.columns = ['Tipo de Movimentação', 'Quantidade']
            st.dataframe(pneu_tipo)

            fig_bar = px.bar(pneu_tipo, x='Tipo de Movimentação', y='Quantidade', title='Movimentação de Pneus por Tipo')
            st.plotly_chart(fig_bar, use_container_width=True)

            if 'VALOR' in df_pneu.columns:
                valor_placa = df_pneu.groupby('PLACA')['VALOR'].sum().reset_index()
                fig_valor = px.bar(valor_placa, x='PLACA', y='VALOR', title='Valor Total Gasto em Pneus por Veículo')
                st.plotly_chart(fig_valor, use_container_width=True)

        with abas[3]:
            st.subheader("Análise Temporal")

            # Manutenções ao longo do tempo
            if 'DATA DA MANUTENÇÃO' in df_manut.columns:
                fig_tempo_manut = px.histogram(df_manut, x='DATA DA MANUTENÇÃO', color='PLACA',
                                              title='Manutenções ao longo do tempo', nbins=30)
                st.plotly_chart(fig_tempo_manut, use_container_width=True)

            # Movimentação pneus ao longo do tempo
            if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
                fig_tempo_pneu = px.histogram(df_pneu, x='DATA DA MOVIMENTAÇÃO', color='TIPO DA MOVIMENTAÇÃO',
                                             title='Movimentação de Pneus ao longo do tempo', nbins=30)
                st.plotly_chart(fig_tempo_pneu, use_container_width=True)

        with abas[4]:
            st.subheader("Detalhamento Completo dos Dados")

            st.markdown("**Dados de Manutenção**")
            st.dataframe(df_manut)

            st.markdown("**Dados de Movimentação de Pneus**")
            st.dataframe(df_pneu)

    else:
        st.error("A planilha deve conter abas chamadas exatamente 'manutencao' e 'pneu'.")
else:
    st.info("Por favor, faça upload da planilha para iniciar a análise.")
