import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

st.set_page_config(page_title="Painel de Manutenção com ML", layout="wide")
st.title("🚛 Painel Completo com Machine Learning para Manutenção e Pneus")

def achar_coluna_km(df):
    colunas_km_possiveis = [
        'KM DO VEÍCULO', 'KM VEÍCULO', 'KM VEICULO', 'KM', 'KM ATUAL',
        'HODÔMETRO', 'HODOMETRO', 'KM_RODADOS'
    ]
    for col in colunas_km_possiveis:
        if col in df.columns:
            return col
    return None

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

        # Identifica coluna KM na manutenção
        col_km = achar_coluna_km(df_manut)
        if col_km is None:
            st.error("❌ Não foi encontrada uma coluna válida de KM na aba 'manutencao'.")
            st.write("Colunas encontradas:", df_manut.columns.tolist())
            st.stop()
        else:
            df_manut['KM_DO_VEICULO'] = pd.to_numeric(df_manut[col_km], errors='coerce')

        # Preprocessar VALOR no pneu
        if 'VALOR' in df_pneu.columns:
            df_pneu['VALOR'] = pd.to_numeric(df_pneu['VALOR'], errors='coerce')
        else:
            df_pneu['VALOR'] = 0

        # Conversão de datas
        if 'DATA DA MANUTENÇÃO' in df_manut.columns:
            df_manut['DATA DA MANUTENÇÃO'] = pd.to_datetime(df_manut['DATA DA MANUTENÇÃO'], errors='coerce')
        if 'DATA DA MOVIMENTAÇÃO' in df_pneu.columns:
            df_pneu['DATA DA MOVIMENTAÇÃO'] = pd.to_datetime(df_pneu['DATA DA MOVIMENTAÇÃO'], errors='coerce')

        # Agrupar dados por veículo para ML
        manut_agg = df_manut.groupby('PLACA').agg(
            total_manut=('PLACA', 'count'),
            km_medio_diff=('KM_DO_VEICULO', lambda x: x.sort_values().diff().mean())
        ).reset_index()

        pneu_agg = df_pneu.groupby('PLACA').agg(
            total_pneu_mov=('PLACA', 'count'),
            valor_total_pneu=('VALOR', 'sum')
        ).reset_index()

        df_features = pd.merge(manut_agg, pneu_agg, on='PLACA', how='outer').fillna(0)

        # Features para clusterização
        features = df_features[['total_manut', 'km_medio_diff', 'total_pneu_mov', 'valor_total_pneu']]
        features = features.replace([np.inf, -np.inf], np.nan).fillna(0)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        n_clusters = st.sidebar.slider("Número de clusters (grupos)", 2, 10, 3)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df_features['cluster'] = kmeans.fit_predict(X_scaled)

        # PCA para visualização
        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)
        df_features['pca1'] = components[:, 0]
        df_features['pca2'] = components[:, 1]

        st.subheader("Clusters de Veículos baseado no Histórico de Manutenção e Pneus")
        st.dataframe(df_features)

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
