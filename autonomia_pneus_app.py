import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # ----------------- LEITURA DAS ABAS -----------------
    sheets = pd.read_excel(arquivo, sheet_name=None, engine="openpyxl")
    if not {"pneus", "poicao", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'poicao' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"]
    df_posicao = sheets["poicao"]
    df_sulco = sheets["sulco"]

    # Padroniza colunas
    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns = df_sulco.columns.str.strip()

    # ----------------- JUNTAR POSIÇÃO -----------------
    df_pneus = df_pneus.merge(df_posicao, left_on="Sigla da Posição", right_on="SIGLA", how="left")

    # ----------------- CONVERTER PARA NUMÉRICO -----------------
    def to_float(x):
        try:
            if pd.isna(x):
                return np.nan
            s = str(x).replace(",", ".").strip()
            return float(s)
        except:
            return np.nan

    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus["Vida do Pneu - Km. Rodado"].apply(to_float)

    # ----------------- JUNTAR SULCO NOVO -----------------
    df_pneus = df_pneus.merge(
        df_sulco,
        left_on=["Vida", "Modelo (Atual)"],
        right_on=["Vida", "Modelo (Atual)"],
        how="left"
    )

    df_pneus = df_pneus.rename(columns={
        "Sulco": "Sulco Novo",
        "Aferição - Sulco": "Sulco Atual"
    })

    # ----------------- CÁLCULOS -----------------
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Novo"] - df_pneus["Sulco Atual"]
    df_pneus["Sulco Consumido/km"] = df_pneus["Sulco Consumido"] / df_pneus["Vida do Pneu - Km. Rodado"].replace(0, pd.NA)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus["Vida do Pneu - Km. Rodado"].apply(lambda x: f"{x:.0f} km" if pd.notna(x) else "")

    # ----------------- ABAS -----------------
    aba1, aba2 = st.tabs(["📌 Indicadores", "📏 Medidas de Sulco"])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus.columns else len(df_pneus)
        estoque = 99
        sucata = 14
        caminhao = 383

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

    # ----------------- MEDIDAS DE SULCO -----------------
    with aba2:
        st.subheader("📏 Medidas de Sulco (com cálculos)")

        def colorir_sulco(val):
            try:
                if val < 2:
                    return "background-color: #FF6B6B; color:white"
                elif val < 4:
                    return "background-color: #FFD93D; color:black"
                else:
                    return "background-color: #6BCB77; color:white"
            except:
                return ""

        cols_show = [
            "Referência","Status","Vida","Modelo (Atual)","POSIÇÃO",
            "Sulco Novo","Sulco Atual","Sulco Consumido","Sulco Consumido/km",
            "Vida do Pneu - Km. Rodado"
        ]
        df_show = df_pneus[cols_show].copy()
        st.dataframe(
            df_show.style.applymap(colorir_sulco, subset=["Sulco Atual"])
                         .format({
                             "Sulco Novo":"{:.2f}",
                             "Sulco Atual":"{:.2f}",
                             "Sulco Consumido":"{:.2f}",
                             "Sulco Consumido/km":"{:.6f}"
                         }),
            use_container_width=True
        )
else:
    st.info("Aguardando upload do arquivo Excel…")
