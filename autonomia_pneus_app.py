import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

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

    def classificar_veiculo(desc):
        if pd.isna(desc):
            return "Desconhecido"
        desc = desc.lower()
        if "saveiro" in desc:
            return "Leve"
        elif any(x in desc for x in ["renault", "iveco", "scudo"]):
            return "Utilitário"
        elif any(x in desc for x in ["3/4", "toco", "truck"]):
            return "Caminhão"
        elif any(x in desc for x in ["carreta", "cavalo"]):
            return "Carreta"
        return "Outros"

    # ----------------- PREPARAR DADOS -----------------
    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # Ajuste de estoque (6 pneus extras)
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
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # Sulco novo médio por modelo (apenas pneus sem uso e não extras)
    df_novos = df[(df["Km Rodado até Aferição"].isna()) | (df["Km Rodado até Aferição"] <= 0)]
    sulco_novo_por_modelo = df_novos.groupby("Modelo (Atual)")["Aferição - Sulco"].mean()

    df["Sulco Novo"] = df["Modelo (Atual)"].map(sulco_novo_por_modelo)
    df["Sulco Consumido"] = df["Sulco Novo"] - df["Aferição - Sulco"]
    df["Desgaste por Km"] = df["Sulco Consumido"] / df["Km Rodado até Aferição"]
    df["Categoria Veículo"] = df["Veículo - Descrição"].apply(classificar_veiculo)

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba4, aba3, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "ℹ️ Legenda"
    ])

    # ----------------- ABA DE INDICADORES -----------------
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

    # ----------------- ABA DE GRÁFICO -----------------
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco")
        df_com_km = df[df["Km Rodado até Aferição"].notna() & (df["Km Rodado até Aferição"] > 0)].copy()
        if not df_com_km.empty:
            def cor_pneu(row):
                if pd.notna(row["Aferição - Sulco"]) and row["Aferição - Sulco"] < 2:
                    return "Crítico"
                else:
                    return row["Marca (Atual)"]

            df_com_km["Cor_Gráfico"] = df_com_km.apply(cor_pneu, axis=1)

            cores_set2 = px.colors.qualitative.Set2
            marcas = df_com_km["Marca (Atual)"].dropna().unique().tolist()
            color_map = {marca: cores_set2[i % len(cores_set2)] for i, marca in enumerate(marcas)}
            color_map["Crítico"] = "#FF0000"

            fig_desgaste = px.scatter(
                df_com_km,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Cor_Gráfico",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Status", "Vida"],
                color_discrete_map=color_map,
                height=500
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)

            st.subheader("📈 Tabela: Relação Km Rodado x Sulco")
            df_tabela = df_com_km.copy().sort_values(by="Km Rodado até Aferição", ascending=True)
            df_tabela["Aferição - Sulco"] = df_tabela["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            df_tabela["Km Rodado até Aferição"] = df_tabela["Km Rodado até Aferição"].map(lambda x: f"{int(x):,} km")
            colunas_tabela = ["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", 
                              "Sulco Novo", "Sulco Consumido", "Desgaste por Km", "Status", 
                              "Km Rodado até Aferição", "Aferição - Sulco"]
            st.dataframe(
                df_tabela[colunas_tabela].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
                use_container_width=True
            )

    # ----------------- ABA DE MEDIDAS DE SULCO -----------------
    with aba4:
        st.subheader("📏 Medidas de Sulco")
        df_sulco = df[(df["Aferição - Sulco"].notna()) & (~df["Referência"].astype(str).str.contains("Extra"))].copy()
        df_sulco = df_sulco.sort_values(by="Aferição - Sulco", ascending=True)
        df_sulco["Aferição - Sulco"] = df_sulco["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        colunas_sulco = ["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", "Sulco Novo", "Sulco Consumido", "Desgaste por Km", "Status", "Aferição - Sulco"]
        st.dataframe(
            df_sulco[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE TABELA COMPLETA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        df_filtrado = df[~df["Referência"].astype(str).str.contains("Extra")].copy()
        status_filter = st.multiselect(
            "Filtrar por Status",
            options=df_filtrado["Status"].unique(),
            default=df_filtrado["Status"].unique()
        )
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filter)].copy()
        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE LEGENDA -----------------
    with aba5:
        st.subheader("ℹ️ Legenda de Informações")
        st.markdown("### Siglas de Posição")
        if "Sigla da Posição" in df.columns:
            st.write(df["Sigla da Posição"].dropna().unique().tolist())

        st.markdown("### Sulco Novo por Modelo")
        st.dataframe(sulco_novo_por_modelo.reset_index().rename(columns={"Aferição - Sulco": "Sulco Novo (médio)"}))

        st.markdown("### Medida de Rodagem por Categoria de Veículo")
        rodagem_categoria = df.groupby("Categoria Veículo")["Km Rodado até Aferição"].mean().dropna().reset_index()
        st.dataframe(rodagem_categoria.rename(columns={"Km Rodado até Aferição": "Km Médio Rodado"}))
