import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # --- LER TODAS AS ABAS ---
    planilhas = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)

    # Procurar aba "Legenda" (sem case sensitive)
    aba_legenda = None
    for nome in planilhas.keys():
        if nome.strip().lower() == "legenda":
            aba_legenda = nome
            break

    if not aba_legenda:
        st.error("❌ Não encontrei a aba 'Legenda' na planilha. Verifique o arquivo.")
        st.stop()

    # Dados principais
    df = planilhas[list(planilhas.keys())[0]].copy()

    # Aba legenda
    df_legenda = planilhas[aba_legenda].copy()
    df_legenda = df_legenda.rename(columns=lambda x: str(x).strip())

    # ----------------- FUNÇÕES -----------------
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    def colorir_sulco(val):
        try:
            val_float = float(val)
            if val_float < 2:
                return "background-color: #FF6B6B; color: white"
            elif val_float < 4:
                return "background-color: #FFD93D; color: black"
            else:
                return "background-color: #6BCB77; color: white"
        except:
            return ""

    # ----------------- PREPARAR DADOS -----------------
    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # Adiciona pneus extras no estoque
    df_extra = pd.DataFrame({
        "Referência": [f"Extra{i}" for i in range(1, 7)],
        "Status": ["Sucata"]*6,
        "Veículo - Placa": [None]*6,
        "Modelo (Atual)": [None]*6,
        "Marca (Atual)": [None]*6,
        "Aferição - Sulco": [0]*6,
        "Hodômetro Inicial": [0]*6,
        "Observação": [None]*6,
        "Vida": ["Ressolado"]*6
    })
    df = pd.concat([df, df_extra], ignore_index=True)

    # --- MERGE COM A LEGENDA ---
    df = df.merge(
        df_legenda[["Modelo (Atual)", "Sulco"]],
        on="Modelo (Atual)",
        how="left"
    )
    df.rename(columns={"Sulco": "Sulco_Novo"}, inplace=True)

    # Calcular desgaste
    df["Sulco_Consumido"] = df["Sulco_Novo"] - df["Aferição - Sulco"]
    df["Desgaste_por_km"] = df["Sulco_Consumido"] / df["Km Rodado até Aferição"]

    # ----------------- ABAS -----------------
    aba1, aba2, aba4, aba3 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa"
    ])

    # --- Indicadores ---
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = df["Referência"].nunique()
        status_counts = df["Status"].value_counts()
        estoque = status_counts.get("Estoque", 0)
        sucata = status_counts.get("Sucata", 0)
        caminhao = status_counts.get("Caminhão", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        col5, col6, col7 = st.columns(3)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneu_critico = df[df["Aferição - Sulco"] < 2]
        perc_critico = len(pneu_critico) / len(df) * 100

        col5.metric("🟢 Média Sulco (mm)", f"{media_sulco:.2f}")
        col6.metric("🛣️ Média Km até Aferição", f"{media_km:,.0f} km")
        col7.metric("⚠️ Pneus Críticos (<2mm)", len(pneu_critico), f"{perc_critico:.1f}%")

    # --- Gráficos ---
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco")

        df_com_km = df[df["Km Rodado até Aferição"].notna() & (df["Km Rodado até Aferição"] > 0)].copy()
        if not df_com_km.empty:
            def cor_pneu(row):
                if pd.notna(row["Aferição - Sulco"]) and row["Aferição - Sulco"] < 2:
                    return "Crítico"
                else:
                    return row["Modelo (Atual)"]

            df_com_km["Cor_Gráfico"] = df_com_km.apply(cor_pneu, axis=1)

            fig = px.scatter(
                df_com_km,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Cor_Gráfico",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Vida", "Sulco_Novo", "Sulco_Consumido"],
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📊 Tabela: Relação Km Rodado x Sulco")
            df_tab = df_com_km.sort_values(by="Km Rodado até Aferição")
            colunas = ["Referência", "Veículo - Placa", "Modelo (Atual)", "Vida", "Km Rodado até Aferição", "Sulco_Novo", "Aferição - Sulco", "Sulco_Consumido"]
            st.dataframe(
                df_tab[colunas].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
                use_container_width=True
            )

    # --- Medidas de Sulco ---
    with aba4:
        st.subheader("📏 Medidas de Sulco")
        df_sulco = df[df["Aferição - Sulco"].notna()].copy()
        df_sulco = df_sulco.sort_values(by="Aferição - Sulco", ascending=True)
        colunas_sulco = ["Referência", "Veículo - Placa", "Modelo (Atual)", "Vida", "Status", "Sulco_Novo", "Aferição - Sulco", "Sulco_Consumido"]
        st.dataframe(
            df_sulco[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # --- Tabela Completa ---
    with aba3:
        st.subheader("📑 Tabela Completa")
        st.dataframe(
            df.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )
