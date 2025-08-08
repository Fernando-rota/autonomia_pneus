import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Indicadores Manutenção e Pneus", layout="wide")
st.title("📊 Indicadores de Manutenção e Pneus")

@st.cache_data
def carregar_planilha(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' not in xls.sheet_names or 'pneu' not in xls.sheet_names:
        st.error("A planilha precisa conter abas 'manutencao' e 'pneu'.")
        return None, None
    df_manut = pd.read_excel(xls, sheet_name='manutencao')
    df_pneu = pd.read_excel(xls, sheet_name='pneu')
    return df_manut, df_pneu

def achar_coluna_km(df):
    colunas_km_possiveis = [
        'KM DO VEÍCULO', 'KM VEÍCULO', 'KM VEICULO', 'KM', 'KM ATUAL',
        'HODÔMETRO', 'HODOMETRO', 'KM_RODADOS'
    ]
    for col in colunas_km_possiveis:
        if col in df.columns:
            return col
    return None

def intervalo_medio(series):
    s = series.dropna().sort_values()
    if len(s) < 2:
        return np.nan
    return s.diff().mean()

def preparar_dados(df_manut, df_pneu):
    # Padroniza nomes das colunas e placas
    for df in [df_manut, df_pneu]:
        df.columns = df.columns.str.strip().str.upper()
        if 'VEÍCULO - PLACA' in df.columns:
            df.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)
        df['PLACA'] = df['PLACA'].astype(str).str.upper().str.strip()
    # KM
    col_km = achar_coluna_km(df_manut)
    if not col_km:
        st.error("Coluna de KM não encontrada na aba manutenção.")
        return None, None
    df_manut['KM_DO_VEICULO'] = pd.to_numeric(df_manut[col_km], errors='coerce')

    # Datas
    df_manut['DATA DA MANUTENÇÃO'] = pd.to_datetime(df_manut.get('DATA DA MANUTENÇÃO'), errors='coerce')
    df_pneu['DATA DA MOVIMENTAÇÃO'] = pd.to_datetime(df_pneu.get('DATA DA MOVIMENTAÇÃO'), errors='coerce')

    # Remove duplicados e linhas com dados faltantes essenciais
    df_manut.drop_duplicates(inplace=True)
    df_pneu.drop_duplicates(inplace=True)
    df_manut = df_manut.dropna(subset=['PLACA', 'DATA DA MANUTENÇÃO', 'KM_DO_VEICULO'])
    df_pneu = df_pneu.dropna(subset=['PLACA'])

    return df_manut, df_pneu

def criar_grafico_histograma(df, coluna, titulo, nbins=30):
    if coluna in df.columns:
        fig = px.histogram(df, x=coluna, nbins=nbins, title=titulo)
        fig.update_layout(margin=dict(t=40,b=20))
        return fig
    return None

def criar_grafico_barra(df, x_col, y_col, titulo, orientacao='v', top_n=None):
    if top_n:
        df = df.head(top_n)
    fig = px.bar(df, x=x_col, y=y_col, title=titulo)
    if orientacao == 'h':
        fig.update_layout(yaxis={'categoryorder':'total descending'}, margin=dict(t=40,b=20))
        fig.update_traces(orientation='h')
    else:
        fig.update_layout(margin=dict(t=40,b=20))
    return fig

uploaded_file = st.file_uploader("Faça upload da planilha Excel (.xlsx) com abas 'manutencao' e 'pneu'", type=["xlsx"])

if uploaded_file:
    df_manut, df_pneu = carregar_planilha(uploaded_file)
    if df_manut is not None and df_pneu is not None:
        df_manut, df_pneu = preparar_dados(df_manut, df_pneu)

        manut_freq = df_manut.groupby('PLACA').agg(
            total_manut=('PLACA', 'count'),
            km_medio_entre_manut=('KM_DO_VEICULO', intervalo_medio),
            dias_medio_entre_manut=('DATA DA MANUTENÇÃO', intervalo_medio)
        ).reset_index()

        manut_tipo = df_manut['DESCRIÇÃO DA MANUTENÇÃO'].value_counts().reset_index()
        manut_tipo.columns = ['Tipo de Manutenção', 'Quantidade']

        pneu_analise = df_pneu.groupby('PLACA').agg(
            total_pneus_trocados=('PLACA', 'count'),
        ).reset_index()

        if 'AUTONOMIA' in df_pneu.columns:
            autonomia_media = df_pneu['AUTONOMIA'].mean()
            pneus_baixa_autonomia = df_pneu[df_pneu['AUTONOMIA'] < autonomia_media]
        else:
            pneus_baixa_autonomia = pd.DataFrame()

        abas = st.tabs([
            "Frequência e Intervalo de Manutenção",
            "Tipos de Manutenção",
            "Movimentação de Pneus",
            "Pneus com Baixa Autonomia"
        ])

        with abas[0]:
            st.subheader("Frequência e Intervalo entre Manutenções por Veículo")
            st.dataframe(manut_freq)
            fig = criar_grafico_histograma(manut_freq, 'km_medio_entre_manut',
                                          "Distribuição do Intervalo Médio de KM entre Manutenções")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para gráfico de intervalos de KM.")

        with abas[1]:
            st.subheader("Tipos de Manutenção mais Comuns")
            st.dataframe(manut_tipo)
            fig = criar_grafico_barra(manut_tipo, 'Quantidade', 'Tipo de Manutenção',
                                     'Top 20 Tipos de Manutenção', orientacao='h', top_n=20)
            st.plotly_chart(fig, use_container_width=True)

        with abas[2]:
            st.subheader("Total de Pneus Trocados por Veículo")
            st.dataframe(pneu_analise)
            fig = criar_grafico_barra(pneu_analise, 'PLACA', 'total_pneus_trocados',
                                     'Pneus Trocados por Veículo')
            st.plotly_chart(fig, use_container_width=True)

        with abas[3]:
            st.subheader("Pneus com Autonomia Abaixo da Média")
            if not pneus_baixa_autonomia.empty:
                st.dataframe(pneus_baixa_autonomia)
                fig = criar_grafico_histograma(pneus_baixa_autonomia, 'AUTONOMIA',
                                              'Distribuição de Autonomia Baixa', nbins=20)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Coluna 'AUTONOMIA' não encontrada na planilha de pneus ou sem dados válidos.")

else:
    st.info("Faça upload da planilha para iniciar a análise.")
