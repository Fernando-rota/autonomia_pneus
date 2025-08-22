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
            
    def classificar_veiculo(descricao):
        if pd.isna(descricao):
            return "Não especificado"
        descricao = str(descricao).upper()
        
        if "SAVEIRO" in descricao:
            return "Leve"
        elif "SCUDO" in descricao or "DAILY" in descricao or "RENAULT" in descricao or "IVECO" in descricao:
            return "Utilitário"
        elif "3/4" in descricao or "ACCELO" in descricao:
            return "3/4"
        elif "TOCO" in descricao or "ATRON" in descricao:
            return "Toco"
        elif "TRUCK" in descricao:
            return "Truck"
        elif "CARRETA" in descricao:
            return "Carreta"
        elif "VAN" in descricao or "MASTER" in descricao:
            return "Van"
        else:
            return "Outro"

    # ----------------- DICIONÁRIOS DE REFERÊNCIA -----------------
    # Legenda das siglas de posição
    legenda_posicoes = {
        "ADI": "Dianteiro Esquerdo (Motor)",
        "AEI": "Dianteiro Direito (Motor)",
        "CDI": "Traseiro Interno Esquerdo (Motor)",
        "CDE": "Traseiro Externo Esquerdo (Motor)",
        "CEI": "Traseiro Interno Direito (Motor)",
        "CEE": "Traseiro Externo Direito (Motor)",
        "DDI": "Dianteiro Esquerdo (Reboque)",
        "DDE": "Dianteiro Direito (Reboque)",
        "DEI": "Traseiro Interno Esquerdo (Reboque)",
        "DEE": "Traseiro Externo Esquerdo (Reboque)",
        "EDI": "Traseiro Interno Direito (Reboque)",
        "EDE": "Traseiro Externo Direito (Reboque)",
        "EEI": "Livre Esquerdo (Reboque)",
        "EEE": "Livre Direito (Reboque)",
        "Z1": "Estepe 1",
        "Z2": "Estepe 2"
    }
    
    # Sulco inicial por modelo de pneu (antes de usar)
    sulco_inicial_por_modelo = {
        "275/80": 16.0,
        "295/80": 18.0,
        "225/65": 8.0,
        "225/75": 8.0,
        "205/60": 8.0,
        "215/65": 8.0,
        "215/75": 8.0,
        "235/75": 8.0,
        "175/70": 8.0
    }

    # ----------------- PREPARAR DADOS -----------------
    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]
    
    # Classificar tipo de veículo
    df["Tipo Veículo"] = df["Veículo - Descrição"].apply(classificar_veiculo)
    
    # Adicionar sulco inicial baseado na dimensão do pneu
    def obter_sulco_inicial(dimensoes):
        if pd.isna(dimensoes):
            return None
        for medida, sulco in sulco_inicial_por_modelo.items():
            if medida in str(dimensoes):
                return sulco
        return None
        
    df["Sulco Inicial"] = df["Dimensões"].apply(obter_sulco_inicial)
    
    # Calcular sulco consumido
    df["Sulco Consumido"] = df.apply(
        lambda row: row["Sulco Inicial"] - row["Aferição - Sulco"] 
        if pd.notna(row["Sulco Inicial"]) and pd.notna(row["Aferição - Sulco"]) 
        else None, 
        axis=1
    )
    
    # Calcular sulco consumido por km
    df["Sulco Consumido/Km"] = df.apply(
        lambda row: row["Sulco Consumido"] / row["Km Rodado até Aferição"] 
        if pd.notna(row["Sulco Consumido"]) and pd.notna(row["Km Rodado até Aferição"]) and row["Km Rodado até Aferição"] > 0 
        else None, 
        axis=1
    )

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
        "Vida": ["Ressolado"]*6,
        "Tipo Veículo": ["Não especificado"]*6,
        "Sulco Inicial": [0]*6,
        "Sulco Consumido": [0]*6,
        "Sulco Consumido/Km": [0]*6
    })
    df = pd.concat([df, df_extra], ignore_index=True)

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba4, aba3, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "📖 Legenda"
    ])

    # ----------------- ABA DE INDICADORES -----------------
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
        
        # Adicionar estatísticas por tipo de veículo
        st.subheader("📊 Estatísticas por Tipo de Veículo")
        tipo_stats = df.groupby("Tipo Veículo").agg({
            "Referência": "count",
            "Aferição - Sulco": "mean",
            "Km Rodado até Aferição": "mean",
            "Sulco Consumido/Km": "mean"
        }).rename(columns={
            "Referência": "Quantidade",
            "Aferição - Sulco": "Sulco Médio",
            "Km Rodado até Aferição": "Km Médio",
            "Sulco Consumido/Km": "Desgaste Médio (mm/km)"
        }).round(2)
        
        st.dataframe(tipo_stats, use_container_width=True)

    # ----------------- ABA DE GRÁFICO -----------------
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco")
        st.markdown(
            "Cada ponto representa um pneu. O eixo X mostra a quilometragem rodada até a aferição, "
            "e o eixo Y mostra a profundidade do sulco. Pneus críticos (<2mm) estão em vermelho."
        )

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
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Status", "Vida", "Tipo Veículo"],
                color_discrete_map=color_map,
                height=500
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)

            st.subheader("📈 Tabela: Relação Km Rodado x Sulco")
            df_tabela = df_com_km.copy()
            
            # Ordenar antes de formatar
            df_tabela = df_tabela.sort_values(by="Km Rodado até Aferição", ascending=True)
            
            # Formatar colunas para exibição
            df_tabela["Aferição - Sulco"] = df_tabela["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            df_tabela["Km Rodado até Aferição"] = df_tabela["Km Rodado até Aferição"].map(lambda x: f"{int(x):,} km")
            df_tabela["Sulco Consumido"] = df_tabela["Sulco Consumido"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            df_tabela["Sulco Consumido/Km"] = df_tabela["Sulco Consumido/Km"].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")

            colunas_tabela = ["Referência", "Veículo - Placa", "Tipo Veículo", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Km Rodado até Aferição", "Sulco Inicial", "Aferição - Sulco", "Sulco Consumido", "Sulco Consumido/Km"]
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
        df_sulco["Sulco Inicial"] = df_sulco["Sulco Inicial"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
        df_sulco["Sulco Consumido"] = df_sulco["Sulco Consumido"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        df_sulco["Sulco Consumido/Km"] = df_sulco["Sulco Consumido/Km"].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
        
        colunas_sulco = ["Referência", "Veículo - Placa", "Tipo Veículo", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Sulco Inicial", "Aferição - Sulco", "Sulco Consumido", "Sulco Consumido/Km"]
        st.dataframe(
            df_sulco[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE TABELA COMPLETA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        df_filtrado = df[~df["Referência"].astype(str).str.contains("Extra")].copy()
        
        # Formatar colunas numéricas
        df_filtrado["Aferição - Sulco"] = df_filtrado["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        df_filtrado["Sulco Inicial"] = df_filtrado["Sulco Inicial"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
        df_filtrado["Sulco Consumido"] = df_filtrado["Sulco Consumido"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        df_filtrado["Sulco Consumido/Km"] = df_filtrado["Sulco Consumido/Km"].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
        df_filtrado["Km Rodado até Aferição"] = df_filtrado["Km Rodado até Aferição"].map(lambda x: f"{int(x):,} km" if pd.notna(x) else "")
        
        status_filter = st.multiselect(
            "Filtrar por Status",
            options=df_filtrado["Status"].unique(),
            default=df_filtrado["Status"].unique()
        )
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filter)].copy()
        
        tipo_filter = st.multiselect(
            "Filtrar por Tipo de Veículo",
            options=df_filtrado["Tipo Veículo"].unique(),
            default=df_filtrado["Tipo Veículo"].unique()
        )
        df_filtrado = df_filtrado[df_filtrado["Tipo Veículo"].isin(tipo_filter)].copy()
        
        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )
        
    # ----------------- ABA DE LEGENDA -----------------
    with aba5:
        st.subheader("📖 Legenda do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📍 Siglas de Posição")
            df_legenda_posicoes = pd.DataFrame(list(legenda_posicoes.items()), columns=["Sigla", "Descrição"])
            st.dataframe(df_legenda_posicoes, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### 📏 Sulco Inicial por Modelo")
            df_sulco_inicial = pd.DataFrame(list(sulco_inicial_por_modelo.items()), columns=["Medida", "Sulco Inicial (mm)"])
            st.dataframe(df_sulco_inicial, use_container_width=True, hide_index=True)
        
        st.markdown("### 🚗 Classificação de Veículos")
        st.markdown("""
        - **Leve**: Saveiro
        - **Utilitário**: Scudo, Daily, Renault, Iveco
        - **3/4**: Accelo e veículos classificados como 3/4
        - **Toco**: Toco, Aton
        - **Truck**: Todos os caminhões truck
        - **Carreta**: Todos os veículos classificados como carreta
        - **Van**: Master e outras vans
        """)
