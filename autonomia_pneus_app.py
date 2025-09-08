import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata
import numpy as np

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

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

    # Ajustes de nomes
    if "Modelo" in df_pneus.columns and "Modelo (Atual)" not in df_pneus.columns:
        df_pneus = df_pneus.rename(columns={"Modelo": "Modelo (Atual)"})
    if "Modelo" in df_sulco.columns and "Modelo (Atual)" not in df_sulco.columns:
        df_sulco = df_sulco.rename(columns={"Modelo": "Modelo (Atual)"})
    if "SULCO" in df_sulco.columns and "Sulco" not in df_sulco.columns:
        df_sulco = df_sulco.rename(columns={"SULCO": "Sulco"})
    df_posicao = df_posicao.rename(columns={
        "Sigla": "Sigla da Posição",
        "SIGLA": "Sigla da Posição",
        "POSIÇÃO": "Posição",
        "Posição": "Posição"
    })
    if "Sigla" in df_pneus.columns and "Sigla da Posição" not in df_pneus.columns:
        df_pneus = df_pneus.rename(columns={"Sigla": "Sigla da Posição"})
    if "SIGLA" in df_pneus.columns and "Sigla da Posição" not in df_pneus.columns:
        df_pneus = df_pneus.rename(columns={"SIGLA": "Sigla da Posição"})

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

    base = df_sulco[["_VIDA", "_MODELO", "Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")

    # Cálculos
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(
        df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"]>0),
        df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"],
        np.nan
    )

    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", "").apply(classificar_veiculo)

    # ----------------- ABAS -----------------
    aba1, aba2 = st.tabs([
        "📌 Indicadores",
        "📏 Medidas de Sulco"
    ])

    # ----------------- INDICADORES -----------------
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

    # ----------------- MEDIDAS DE SULCO -----------------
    with aba2:
        st.subheader("📏 Medidas de Sulco (Análise Avançada)")

        # KPIs de risco
        df_show = df_pneus.copy()
        df_show["% Sulco Restante"] = (df_show["Aferição - Sulco"] / df_show["Sulco Inicial"] * 100).round(1)
        df_show["Condição"] = pd.cut(
            df_show["Aferição - Sulco"],
            bins=[-1, 2, 4, 99],
            labels=["🔴 Crítico (<2mm)", "🟡 Alerta (2-4mm)", "🟢 Ok (>4mm)"]
        )
        df_show["Km Restante (estimado)"] = np.where(
            (df_show["Desgaste (mm/km)"].notna()) & (df_show["Desgaste (mm/km)"] > 0),
            ((df_show["Aferição - Sulco"] - 2) / df_show["Desgaste (mm/km)"]).round(0),
            np.nan
        )

        criticos = (df_show["Condição"] == "🔴 Crítico (<2mm)").sum()
        alerta = (df_show["Condição"] == "🟡 Alerta (2-4mm)").sum()
        ok = (df_show["Condição"] == "🟢 Ok (>4mm)").sum()

        k1,k2,k3 = st.columns(3)
        k1.metric("🔴 Pneus Críticos", criticos)
        k2.metric("🟡 Pneus em Alerta", alerta)
        k3.metric("🟢 Pneus Ok", ok)

        # Tabela interativa
        cols_show = [c for c in [
            "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
            "Vida","Sulco Inicial","Aferição - Sulco","% Sulco Restante","Condição",
            "Sulco Consumido","Km Rodado até Aferição","Desgaste (mm/km)","Km Restante (estimado)",
            "Posição","Sigla da Posição"
        ] if c in df_show.columns]

        st.data_editor(
            df_show[cols_show],
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Sulco Restante": st.column_config.ProgressColumn(
                    "% Sulco Restante", min_value=0, max_value=100, format="%.1f %%"
                ),
                "Km Restante (estimado)": st.column_config.NumberColumn("Km Restante (estimado)", format="%.0f km")
            }
        )

        # Gráficos de apoio
        st.subheader("📊 Distribuição de Sulcos")
        colg1, colg2 = st.columns(2)

        with colg1:
            fig_hist = px.histogram(df_show, x="Aferição - Sulco", nbins=20, title="Distribuição de Sulcos")
            st.plotly_chart(fig_hist, use_container_width=True)

        with colg2:
            if "Tipo Veículo" in df_show.columns:
                fig_box = px.box(df_show, x="Tipo Veículo", y="Aferição - Sulco", title="Sulco por Tipo de Veículo")
                st.plotly_chart(fig_box, use_container_width=True)

        # Exportação
        st.subheader("📥 Exportar Dados")
        risco = df_show[df_show["Condição"].isin(["🔴 Crítico (<2mm)","🟡 Alerta (2-4mm)"])]
        st.download_button(
            "📥 Exportar Pneus em Risco (Excel)",
            risco.to_csv(index=False).encode("utf-8"),
            "pneus_em_risco.csv",
            "text/csv"
        )

else:
    st.info("Aguardando upload do arquivo Excel…")
