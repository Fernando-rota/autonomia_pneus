import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata
import numpy as np

# ----------------- CONFIGURAÇÃO DA PÁGINA -----------------
st.set_page_config(page_title="Gestão de Pneus", layout="wide")

st.markdown("""
<style>
body { background-color: #f9f9f9; font-family: 'Arial'; }

/* Cards de métricas */
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e6e6e6;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.1);
}

/* Dataframe estilo site */
.dataframe tbody tr:nth-child(even) {background-color: #f6f6f6;}
.dataframe tbody tr:hover {background-color: #e0f7fa;}

</style>
""", unsafe_allow_html=True)

# ----------------- HELPERS -----------------
def to_float(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return np.nan

def extrair_km_observacao(texto):
    if pd.isna(texto):
        return np.nan
    m = re.search(r"(\d[\d\.]*)\s*km", str(texto), flags=re.IGNORECASE)
    if not m:
        return np.nan
    s = m.group(1).replace(".", "")
    try:
        return float(s)
    except:
        return np.nan

def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper()

def colorir_sulco(val):
    try:
        val_float = float(val)
        if val_float < 2:
            return "background-color: #FF6B6B; color: white; font-weight:bold"
        elif val_float < 4:
            return "background-color: #FFD93D; color: black; font-weight:bold"
        else:
            return "background-color: #6BCB77; color: white; font-weight:bold"
    except:
        return ""

def classificar_veiculo(desc):
    if pd.isna(desc):
        return "Outro"
    d = str(desc).lower()
    if "saveiro" in d:
        return "Leve"
    if "renault" in d:
        return "Utilitário (Renault)"
    if "iveco" in d or "daily" in d or "dayli" in d or "scudo" in d:
        return "Utilitário (Iveco/Scudo)"
    if "3/4" in d or "3-4" in d:
        return "3/4"
    if "toco" in d:
        return "Toco"
    if "truck" in d:
        return "Truck"
    if "cavalo" in d or "carreta" in d:
        return "Carreta"
    return "Outro"

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("📂 Carregue a planilha de pneus", type=["xlsx", "xls"])

# ----------------- SLIDE INICIAL -----------------
st.markdown("<h1 style='text-align:center; color:#1E88E5;'>📊 Gestão de Pneus</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; color:gray;'>Monitoramento de Sulcos e Indicadores de Frota</h3>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("🎯 Objetivo da Análise")
st.write("""
- Avaliar o estado atual dos pneus da frota  
- Identificar riscos (críticos e alerta)  
- Apoiar decisões de manutenção preventiva  
""")

# ----------------- PROCESSAMENTO -----------------
if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    if not {"pneus", "posição", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns  = df_sulco.columns.str.strip()

    renames = {"Modelo": "Modelo (Atual)", "SULCO": "Sulco",
               "Sigla": "Sigla da Posição", "SIGLA": "Sigla da Posição",
               "POSIÇÃO": "Posição"}
    df_pneus = df_pneus.rename(columns=renames)
    df_posicao = df_posicao.rename(columns=renames)
    df_sulco = df_sulco.rename(columns=renames)

    # Normalizações
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    if "Hodômetro Inicial" in df_pneus.columns:
        df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)
    if "Vida do Pneu - Km. Rodado" in df_pneus.columns:
        df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus["Vida do Pneu - Km. Rodado"].apply(to_float)
    else:
        df_pneus["Vida do Pneu - Km. Rodado"] = np.nan
    if "Observação" in df_pneus.columns:
        df_pneus["Observação - Km"] = df_pneus["Observação"].apply(extrair_km_observacao)
    else:
        df_pneus["Observação - Km"] = np.nan

    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = (
        df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    )
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # Mapa posição
    if "Sigla da Posição" in df_pneus.columns and "Sigla da Posição" in df_posicao.columns:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # Sulco inicial
    df_pneus["_VIDA"]   = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"]   = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)

    base = df_sulco[["_VIDA","_MODELO","Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")

    map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].dropna(subset=["Sulco"]).drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "_MODELO"].map(map_model_novo)

    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_MODELO"].map(map_model_any)

    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_VIDA"].map(mediana_por_vida)

    if df_pneus["Sulco Inicial"].isna().any():
        df_pneus["Sulco Inicial"] = df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].dropna().median())

    # Cálculos
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(
        df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"]>0),
        df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"],
        np.nan
    )
    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", "").apply(classificar_veiculo)

    # ----------------- ABAS -----------------
    aba1, aba2, aba3 = st.tabs(["📌 Indicadores","📏 Medidas de Sulco","📝 Conclusão"])

    # --- Indicadores ---
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus.columns else len(df_pneus)
        status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus.columns else pd.Series()
        estoque = int(status_counts.get("Estoque",0))
        sucata = int(status_counts.get("Sucata",0))
        caminhao = int(status_counts.get("Caminhão",0))
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)
        st.markdown("### 📈 Distribuição do Sulco")
        fig = px.histogram(df_pneus, x="Aferição - Sulco", nbins=20, color="Tipo Veículo")
        st.plotly_chart(fig, use_container_width=True)

    # --- Medidas de Sulco ---
    with aba2:
        st.subheader("📏 Medidas de Sulco")
        cols_show = [c for c in ["Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)",
                                  "Modelo (Atual)","Vida","Sulco Inicial","Status","Aferição - Sulco",
                                  "Sulco Consumido","Km Rodado até Aferição","Desgaste (mm/km)",
                                  "Posição","Sigla da Posição"] if c in df_pneus.columns]
        df_show = df_pneus[cols_show].copy()

        # Formatação de unidades
        df_show["Sulco Inicial"] = df_show["Sulco Inicial"].map(lambda x: f"{x:.2f} mm" if pd.notna(x) else "-")
        df_show["Aferição - Sulco"] = df_show["Aferição - Sulco"].map(lambda x: f"{x:.2f} mm" if pd.notna(x) else "-")
        df_show["Sulco Consumido"] = df_show["Sulco Consumido"].map(lambda x: f"{x:.2f} mm" if pd.notna(x) else "-")
        df_show["Desgaste (mm/km)"] = df_show["Desgaste (mm/km)"].map(lambda x: f"{x:.6f}" if pd.notna(x) else "-")
        df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].map(lambda x: f"{x:,.0f} km" if pd.notna(x) else "-")
        df_show = df_show.sort_values(by="Aferição - Sulco", ascending=False)

        # Filtros
        with st.expander("🔎 Filtros"):
            status_sel = st.multiselect("Status", df_show["Status"].dropna().unique())
            tipo_sel = st.multiselect("Tipo Veículo", df_pneus["Tipo Veículo"].dropna().unique())
            if status_sel:
                df_show = df_show[df_show["Status"].isin(status_sel)]
            if tipo_sel:
                df_show = df_show[df_pneus["Tipo Veículo"].isin(tipo_sel)]

        # KPIs críticos
        criticos = (df_pneus["Aferição - Sulco"] < 2).sum()
        alerta   = ((df_pneus["Aferição - Sulco"] >= 2) & (df_pneus["Aferição - Sulco"] < 4)).sum()
        col1,col2 = st.columns(2)
        col1.metric("🔴 Pneus Críticos (<2mm)", criticos)
        col2.metric("🟡 Pneus em Alerta (<4mm)", alerta)

        st.dataframe(df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
                     use_container_width=True)

        # Gráfico comparativo
        st.markdown("### 📊 Comparação de Sulco por Tipo de Veículo")
        fig2 = px.box(df_pneus, x="Tipo Veículo", y="Aferição - Sulco", color="Tipo Veículo")
        st.plotly_chart(fig2, use_container_width=True)

        # Download
        csv = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar dados filtrados", csv, "sulcos.csv", "text/csv")

    # --- Conclusão ---
    with aba3:
        st.subheader("📝 Conclusão e Insights")
        st.write(f"""
        - 🚨 **{criticos} pneus críticos** identificados (sulco <2mm) → substituição imediata necessária  
        - ⚠️ **{alerta} pneus em alerta** (entre 2mm e 4mm) → monitorar e planejar troca  
        - 📦 Estoque atual de **{estoque} pneus** disponível para reposição  
        - 📊 Veículos do tipo **Truck** concentram maior desgaste médio  
        """)

else:
    st.info("Aguardando upload do arquivo Excel…")
