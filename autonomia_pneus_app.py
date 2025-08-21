import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # Função para extrair km da observação
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # ----------------- AJUSTE DE ESTOQUE -----------------
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

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba3, aba4 = st.tabs(["📌 Indicadores", "📈 Gráficos", "📑 Tabela Completa", "📏 Medidas de Sulco"])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        st.markdown(
            """
            Este painel de BI apresenta a **gestão de pneus das 3 unidades**.  
            Os indicadores refletem os dados cadastrados no sistema a partir de **maio/2025**.  

            O objetivo deste BI é fornecer uma visão geral do estoque, sucata, pneus em uso nos caminhões e alertas de pneus críticos.  
            Ele permite monitorar a **vida útil dos pneus**, identificar pneus próximos do limite de segurança e otimizar o gerenciamento da frota.
            """
        )

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

    # ----------------- GRÁFICO -----------------
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco")
        st.markdown(
            "Cada ponto representa um pneu. O eixo X mostra a quilometragem rodada até a aferição, "
            "e o eixo Y mostra a profundidade do sulco. Pneus críticos (<2mm) estão em vermelho."
        )

        # Filtrar apenas pneus com km rodado > 0
        df_com_km = df[df["Km Rodado até Aferição"].notna() & (df["Km Rodado até Aferição"] > 0)].copy()

        if not df_com_km.empty:
            # Criar coluna para cor, destacando críticos
            def cor_pneu(row):
                if pd.notna(row["Aferição - Sulco"]) and row["Aferição - Sulco"] < 2:
                    return "Crítico"
                else:
                    return row["Marca (Atual)"]

            df_com_km["Cor_Gráfico"] = df_com_km.apply(cor_pneu, axis=1)

            # Definir cores: vermelho para críticos, cores Set2 para as marcas
            cores_set2 = px.colors.qualitative.Set2
            marcas = df_com_km["Marca (Atual)"].dropna().unique().tolist()
            color_map = {marca: cores_set2[i % len(cores_set2)] for i, marca in enumerate(marcas)}
            color_map["Crítico"] = "#FF0000"  # vermelho para críticos

            # Gráfico
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

            # ----------------- TABELA DO GRÁFICO -----------------
            st.subheader("📈 Tabela: Relação Km Rodado x Sulco")

            df_tabela = df_com_km.copy()
            df_tabela["Aferição - Sulco"] = df_tabela["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            df_tabela["Km Rodado até Aferição"] = df_tabela["Km Rodado até Aferição"].map(lambda x: f"{int(x):,} km")

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

            colunas_tabela = ["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Km Rodado até Aferição", "Aferição - Sulco"]
            st.dataframe(
                df_tabela[colunas_tabela].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
                use_container_width=True
            )

    # ----------------- TABELA COMPLETA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        status_filter = st.multiselect("Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique())
        df_filtrado = df[df["Status"].isin(status_filter)].copy()

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

        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE MEDIDAS -----------------
    with aba4:
        st.subheader("📏 Medidas de Sulco")
        # Exibir apenas pneus com valores de sulco
        df_sulco = df[df["Aferição - Sulco"].notna()].copy()
        df_sulco["Aferição - Sulco"] = df_sulco["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")

        colunas_sulco = ["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Aferição - Sulco"]
        st.dataframe(
            df_sulco[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )
