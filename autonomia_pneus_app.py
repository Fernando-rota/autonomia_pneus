import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
import unicodedata
from io import BytesIO

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

# ----------------- FUNÇÕES AUXILIARES -----------------
def to_float(x):
    if pd.isna(x): return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)): return float(x)
    s = str(x).strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try: return float(s)
    except: return np.nan

def extrair_km_observacao(texto):
    if pd.isna(texto): return np.nan
    m = re.search(r"(\d[\d\.]*)\s*km", str(texto), flags=re.IGNORECASE)
    if not m: return np.nan
    return float(m.group(1).replace(".", ""))

def normalize_text(s):
    if pd.isna(s): return ""
    s = str(s).strip().lower()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper()

def colorir_sulco(val):
    try:
        val_float = float(val)
        if val_float < 3: return "background-color:#E74C3C; color:white"
        elif val_float < 4: return "background-color:#F1C40F; color:black"
        else: return "background-color:#2ECC71; color:white"
    except: return ""

def icon_sulco(val):
    try:
        v = float(val)
        if v < 3: return "❌"
        elif v < 4: return "⚠️"
        else: return "✅"
    except: return ""

def classificar_veiculo(desc):
    if pd.isna(desc): return "Outro"
    d = str(desc).lower()
    if "saveiro" in d: return "Leve"
    if "renault" in d: return "Utilitário (Renault)"
    if "iveco" in d or "daily" in d or "scudo" in d: return "Utilitário (Iveco/Scudo)"
    if "3/4" in d or "3-4" in d: return "3/4"
    if "toco" in d: return "Toco"
    if "truck" in d: return "Truck"
    if "cavalo" in d or "carreta" in d: return "Carreta"
    return "Outro"

# ----------------- PROCESSAMENTO -----------------
if arquivo:
    sheets = pd.read_excel(arquivo, sheet_name=None)
    if not {"pneus","posição","sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    # Normalização de colunas
    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns  = df_sulco.columns.str.strip()
    df_pneus.rename(columns={"Modelo":"Modelo (Atual)","Sigla":"Sigla da Posição","SIGLA":"Sigla da Posição"}, inplace=True)
    df_sulco.rename(columns={"Modelo":"Modelo (Atual)","SULCO":"Sulco"}, inplace=True)
    df_posicao.rename(columns={"Sigla":"Sigla da Posição","POSIÇÃO":"Posição","SIGLA":"Sigla da Posição"}, inplace=True)

    # Conversão de valores
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    df_pneus["Hodômetro Inicial"] = df_pneus.get("Hodômetro Inicial", np.nan).apply(to_float)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus.get("Vida do Pneu - Km. Rodado", np.nan).apply(to_float)
    df_pneus["Observação - Km"] = df_pneus.get("Observação","").apply(extrair_km_observacao)

    # Km Rodado até aferição
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"]<=0)
    df_pneus.loc[mask,"Km Rodado até Aferição"] = df_pneus.loc[mask,"Observação - Km"] - df_pneus.loc[mask,"Hodômetro Inicial"]
    df_pneus.loc[df_pneus["Km Rodado até Aferição"]<=0,"Km Rodado até Aferição"] = np.nan

    # Merge posição
    if "Sigla da Posição" in df_pneus.columns and "Sigla da Posição" in df_posicao.columns:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # Sulco inicial
    df_pneus["_VIDA"] = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"] = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)
    base = df_sulco[["_VIDA","_MODELO","Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")
    map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].dropna(subset=["Sulco"]).drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "_MODELO"].map(map_model_novo)
    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_MODELO"].map(map_model_any)
    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_VIDA"].map(mediana_por_vida)
    df_pneus["Sulco Inicial"] = df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].dropna().median())

    # Cálculos adicionais
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"]>0),
                                             df_pneus["Sulco Consumido"]/df_pneus["Km Rodado até Aferição"], np.nan)
    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição","").apply(classificar_veiculo)
    df_pneus["Status Sulco"] = df_pneus["Aferição - Sulco"].apply(icon_sulco)

    # ----------------- FILTROS LATERAIS -----------------
    st.sidebar.header("Filtros")
    modelos = ["Todos"] + df_pneus["Modelo (Atual)"].dropna().unique().tolist()
    modelo_sel = st.sidebar.selectbox("Modelo", modelos)
    if modelo_sel != "Todos":
        df_pneus = df_pneus[df_pneus["Modelo (Atual)"]==modelo_sel]

    veiculos = ["Todos"] + df_pneus["Veículo - Placa"].dropna().unique().tolist()
    veiculo_sel = st.sidebar.selectbox("Veículo", veiculos)
    if veiculo_sel != "Todos":
        df_pneus = df_pneus[df_pneus["Veículo - Placa"]==veiculo_sel]

    # ----------------- ABAS -----------------
    aba1, aba2 = st.tabs(["📌 Indicadores","📏 Medidas de Sulco"])

    # ----------------- ABA INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = len(df_pneus)
        status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus.columns else pd.Series()
        estoque = int(status_counts.get("Estoque",0))
        sucata = int(status_counts.get("Sucata",0))
        caminhao = int(status_counts.get("Caminhão",0))
        criticos = len(df_pneus[df_pneus["Aferição - Sulco"]<3])
        sulco_medio = round(df_pneus["Aferição - Sulco"].mean(),2)
        km_medio = round(df_pneus["Km Rodado até Aferição"].mean(),0)

        col1,col2,col3,col4,col5,col6 = st.columns(6)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)
        col5.metric("❌ Pneus Críticos (<3mm)", criticos, f"{round(criticos/total_pneus*100,1)}%")
        col6.metric("📏 Sulco Médio (mm)", sulco_medio)

        # Gráfico barras por tipo de veículo
        tipo_count = df_pneus.groupby("Tipo Veículo")["Aferição - Sulco"].mean().reset_index()
        fig = px.bar(tipo_count, x="Tipo Veículo", y="Aferição - Sulco", color="Aferição - Sulco",
                     color_continuous_scale=["red","yellow","green"], title="Sulco Médio por Tipo de Veículo")
        st.plotly_chart(fig, use_container_width=True)

    # ----------------- ABA MEDIDAS DE SULCO -----------------
    with aba2:
        st.subheader("📏 Medidas de Sulco (Detalhadas)")

        # Alertas rápidos
        pneus_criticos = df_pneus[df_pneus["Aferição - Sulco"] < 3]
        if not pneus_criticos.empty:
            st.warning(f"⚠️ {len(pneus_criticos)} pneus críticos com sulco abaixo de 3mm!")

        # Filtros internos
        tipos = ["Todos"] + df_pneus["Tipo Veículo"].dropna().unique().tolist()
        tipo_sel = st.selectbox("Filtrar por Tipo de Veículo", tipos)
        df_show = df_pneus.copy()
        if tipo_sel != "Todos":
            df_show = df_show[df_show["Tipo Veículo"] == tipo_sel]

        # Colunas a mostrar
        cols_show = [
            "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
            "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Desgaste (mm/km)",
            "Posição","Sigla da Posição","Status Sulco"
        ]
        cols_show = [c for c in cols_show if c in df_show.columns]
        df_show = df_show[cols_show]

        # Formatação Km Rodado
        if "Km Rodado até Aferição" in df_show.columns:
            df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].apply(
                lambda x: f"{x:,.0f} km" if pd.notna(x) else "-"
            )

        st.dataframe(
            df_show.style.applymap(
                colorir_sulco, subset=["Sulco Inicial","Aferição - Sulco","Sulco Consumido","Desgaste (mm/km)"]
            ),
            use_container_width=True,
            height=600
        )

        # Exportação para Excel
        def to_excel(df):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Medidas de Sulco')
            writer.save()
            processed_data = output.getvalue()
            return processed_data

        df_xlsx = to_excel(df_show)
        st.download_button(
            label='📥 Baixar tabela filtrada',
            data=df_xlsx,
            file_name='medidas_de_sulco.xlsx'
        )
else:
    st.info("Aguardando upload do arquivo Excel…")
