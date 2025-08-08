import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="Painel de Manutenção com ML", layout="wide")
st.title("🚛 Painel Completo com Machine Learning para Manutenção e Pneus")

uploaded_file = st.file_uploader("Carregue sua planilha Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manut = pd.read_excel(xls, sheet_name='manutencao')
        df_pneu = pd.read_excel(xls, sheet_name='pneu')

        df_manut.columns = df_manut.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip().str.upper()

        for df in [df_manut, df_pneu]:
            if 'VEÍCULO - PLACA' in df.columns:
                df.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)

        # Preprocessamento básico
        df_manut['KM DO VEÍCULO'] = pd.to_numeric(df_manut['KM DO VEÍCULO'], errors='coerce')
        df_pneu['VALOR'] = pd.to_numeric(df_pneu['VALOR'], errors='coerce')

        # Agregar dados por veículo para ML
        manut_agg = df_manut.groupby('PLACA').agg(
            total_manut=('PLACA', 'count'),
            km_medio_diff=('KM DO VEÍCULO', lambda x: x.sort_values().diff().mean())
        ).reset_index()

        pneu_agg = df_pneu.groupby('PLACA').agg(
            total_pneu_mov=('PLACA', 'count'),
            valor_total_pneu=('VALOR', 'sum')
        ).reset_index()

        # Juntar as duas agregações (inner join)
        df_features = pd.merge(manut_agg, pneu_agg, on='PLACA', how='outer').fillna(0)

        # Prepara features para clusterização
        features = df_features[['total_manut', 'km_medio_diff', 'total_pneu_mov', 'valor_total_pneu']]
        features = features.replace([np.inf, -np.inf], np.nan).fillna(0)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        # Slider para escolher número de clusters
        n_clusters = st.sidebar.slider("Número de clusters (grupos)", min_value=2, max_value=10, value=3)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df_features['cluster'] = kmeans.fit_predict(X_scaled)

        st.subheader("Clusters de Veículos baseados no Histórico de Manutenção e Pneus")

        st.dataframe(df_features)

        # Visualizar clusters em 2D usando os 2 primeiros componentes PCA para simplicidade
        from sklearn.decomposition import PCA

        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)
        df_features['pca1'] = components[:, 0]
        df_features['pca2'] = components[:, 1]

        fig = px.scatter(df_features, x='pca1', y='pca2', color='cluster', hover_data=['PLACA'],
                         title='Visualização dos clusters de veículos (PCA 2D)')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        ### Interpretação inicial:
        - Cada cluster representa um grupo de veículos com perfil similar em termos de quantidade de manutenções, valores gastos e movimentações de pneus.
        - Pode-se investigar cada grupo para entender causas e planejar ações específicas.
        """)

    else:
        st.error("A planilha deve conter abas chamadas exatamente 'manutencao' e 'pneu'.")
else:
    st.info("Por favor, faça upload da planilha para iniciar a análise.")
