import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# -------------------
# Upload do arquivo Excel
st.sidebar.subheader("Carregar arquivo Excel")
arquivo = st.sidebar.file_uploader("Escolha o arquivo Excel", type="xlsx")

if arquivo is not None:
    # -------------------
    # Ler abas
    try:
        df_pneus = pd.read_excel(arquivo, sheet_name="pneus", engine="openpyxl")
        df_pneus.columns = df_pneus.columns.str.strip()

        df_posicao = pd.read_excel(arquivo, sheet_name="posição", engine="openpyxl")
        df_posicao.columns = df_posicao.columns.str.strip()

        df_sulco = pd.read_excel(arquivo, sheet_name="sulco", engine="openpyxl")
        df_sulco.columns = df_sulco.columns.str.strip()
    except Exception as e:
        st.error(f"Erro ao ler as planilhas: {e}")
        st.stop()

    # -------------------
    # Mapear posição (Sigla da Posição -> Posição)
    df_pneus = df_pneus.merge(
        df_posicao.rename(columns={"SIGLA": "Sigla da Posição", "POSIÇÃO": "Posição"}),
        on="Sigla da Posição",
        how="left"
    )

    # Criar dicionário Modelo -> Sulco Novo
    sulco_novo_dict = df_sulco.set_index("Modelo (Atual)")["Sulco"].to_dict()

    # Mapear Sulco Novo no dataframe principal
    df_pneus["Sulco Novo"] = df_pneus["Modelo (Atual)"].map(sulco_novo_dict)

    # Calcular Sulco Consumido apenas quando houver dados
    df_pneus["Sulco Consumido"] = df_pneus.apply(
        lambda x: x["Sulco Novo"] - x["Aferição - Sulco"]
        if pd.notna(x["Sulco Novo"]) and pd.notna(x["Aferição - Sulco"]) else None,
        axis=1
    )

    # Calcular Desgaste por Km (usando a coluna correta da aba pneus)
    df_pneus["Desgaste por Km"] = df_pneus.apply(
        lambda x: x["Sulco Consumido"] / x["Vida do Pneu - Km. Rodado"]
        if pd.notna(x["Sulco Consumido"]) and pd.notna(x["Vida do Pneu - Km. Rodado"]) and x["Vida do Pneu - Km. Rodado"] > 0 else None,
        axis=1
    )

    # -------------------
    # Filtros interativos
    st.sidebar.subheader("Filtros")
    modelos = st.sidebar.multiselect("Selecione Modelo", df_pneus["Modelo (Atual)"].unique(), default=df_pneus["Modelo (Atual)"].unique())
    posicoes = st.sidebar.multiselect("Selecione Posição", df_pneus["Posição"].unique(), default=df_pneus["Posição"].unique())

    df_filtrado = df_pneus[(df_pneus["Modelo (Atual)"].isin(modelos)) & (df_pneus["Posição"].isin(posicoes))]

    # -------------------
    # Alertas de desgaste
    LIMITE_DESGASTE = 0.03
    df_filtrado["Alerta Desgaste"] = df_filtrado["Desgaste por Km"].apply(
        lambda x: "⚠️ Alto" if pd.notna(x) and x > LIMITE_DESGASTE else "Normal"
    )

    # -------------------
    # Mostrar dataframe filtrado com destaque para pneus críticos
    st.subheader("Dados Atualizados com Alertas")
    def color_desgaste(val):
        if val == "⚠️ Alto":
            return 'background-color: #FFCCCC'  # vermelho claro
        return ''
    st.dataframe(df_filtrado.style.applymap(color_desgaste, subset=["Alerta Desgaste"])
                 .format({
                     "Sulco Novo": "{:.2f}",
                     "Sulco Consumido": "{:.2f}",
                     "Desgaste por Km": "{:.5f}"
                 }))

    # -------------------
    # Gráfico: Desgaste por Km
    st.subheader("Desgaste por Km por Modelo e Posição")
    fig = px.bar(df_filtrado, x="Modelo (Atual)", y="Desgaste por Km", color="Posição", barmode="group")
    fig.add_hline(y=LIMITE_DESGASTE, line_dash="dash", line_color="red", annotation_text="Limite")
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de pneus críticos
    st.subheader("Pneus com Desgaste Alto")
    df_critico = df_filtrado[df_filtrado["Alerta Desgaste"] == "⚠️ Alto"]
    if not df_critico.empty:
        fig_critico = px.bar(df_critico, x="Modelo (Atual)", y="Desgaste por Km",
                             color="Posição", text="Desgaste por Km")
        fig_critico.add_hline(y=LIMITE_DESGASTE, line_dash="dash", line_color="red", annotation_text="Limite")
        st.plotly_chart(fig_critico, use_container_width=True)
    else:
        st.info("Nenhum pneu acima do limite de desgaste.")

else:
    st.info("Aguardando upload do arquivo Excel...")
