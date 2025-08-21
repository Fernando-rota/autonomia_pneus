import re
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------
# Configuração do app
# ------------------------------------
st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# ------------------------------------
# Helpers
# ------------------------------------
def to_datetime_safe(s):
    """Converte para datetime (pt-BR) com segurança."""
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

def to_numeric_safe(s):
    """Converte para número aceitando vírgula decimal e pontuação de milhar."""
    if s is None:
        return np.nan
    return pd.to_numeric(
        pd.Series(s).astype(str)
        .str.replace(r"\.", "", regex=True)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    ).iloc[0]

def extract_obs(texto):
    """
    Extrai Data e Km da coluna Observação.
    Ex.: 'Aferição 20/08/25 - 109418 km' -> (2025-08-20, 109418)
    """
    if pd.isna(texto):
        return pd.NaT, np.nan
    t = str(texto)

    # data dd/mm/aa(aa)
    m_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", t)
    data = to_datetime_safe(m_data.group(1)) if m_data else pd.NaT

    # km com ou sem milhares + 'km'
    m_km = re.search(r"([\d\.]+|\d+)\s*km", t.replace("KM", "km"))
    if m_km:
        km_txt = m_km.group(1)
        km_num = pd.to_numeric(km_txt.replace(".", ""), errors="coerce")
    else:
        km_num = np.nan
    return data, km_num

def download_excel(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Dados")
    return out.getvalue()

# ------------------------------------
# Upload
# ------------------------------------
arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])
if not arquivo:
    st.info("⬆️ Envie um arquivo Excel (.xlsx) para começar.")
    st.stop()

# Suporte a múltiplas abas do Excel
xf = pd.ExcelFile(arquivo, engine="openpyxl")
sheet = st.selectbox("Escolha a aba da planilha:", xf.sheet_names)
df = xf.parse(sheet)

# Padronizações leves (não quebra nomes originais)
# Datas conhecidas
for c in [c for c in df.columns if "Data" in c]:
    df[c] = to_datetime_safe(df[c])

# Sulco para numérico
if "Aferição - Sulco" in df.columns:
    df["Aferição - Sulco"] = df["Aferição - Sulco"].apply(to_numeric_safe)

# Hodômetro Inicial para numérico
if "Hodômetro Inicial" in df.columns:
    df["Hodômetro Inicial"] = df["Hodômetro Inicial"].apply(to_numeric_safe)

# Extrair Observação - Data e Observação - Km
if "Observação" in df.columns:
    extra = df["Observação"].apply(extract_obs)
    df["Observação - Data"] = extra.apply(lambda x: x[0])
    df["Observação - Km"] = extra.apply(lambda x: x[1])

# Km Rodado até Aferição = Observação - Km - Hodômetro Inicial
if {"Observação - Km", "Hodômetro Inicial"}.issubset(df.columns):
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

# ------------------------------------
# Filtros laterais (opcional, úteis p/ analisar por recortes)
# ------------------------------------
st.sidebar.header("🔎 Filtros")
def multiselect_or_all(label, series):
    vals = series.dropna().unique().tolist()
    if not vals:
        return []
    return st.sidebar.multiselect(label, vals, default=vals)

val_status = multiselect_or_all("Status", df["Status"]) if "Status" in df.columns else []
val_marca  = multiselect_or_all("Marca (Atual)", df["Marca (Atual)"]) if "Marca (Atual)" in df.columns else []
val_veic   = multiselect_or_all("Veículo - Descrição", df["Veículo - Descrição"]) if "Veículo - Descrição" in df.columns else []

df_filtrado = df.copy()
if val_status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(val_status)]
if val_marca:
    df_filtrado = df_filtrado[df_filtrado["Marca (Atual)"].isin(val_marca)]
if val_veic:
    df_filtrado = df_filtrado[df_filtrado["Veículo - Descrição"].isin(val_veic)]

# ------------------------------------
# Abas
# ------------------------------------
abas = st.tabs([
    "📌 Indicadores Gerais",
    "📊 Análises por Status",
    "🏷️ Marcas e Modelos",
    "🚚 Veículos",
    "📍 Posição dos Pneus",
    "🏆 Rankings",
    "📥 Exportação",
])

# ====================================
# 1) Indicadores Gerais
# ====================================
with abas[0]:
    st.subheader("📌 Indicadores Gerais")

    # Total de pneus (por 'Referência' se existir; senão linhas)
    total_pneus = df_filtrado["Referência"].nunique() if "Referência" in df_filtrado.columns else len(df_filtrado)

    # Contagem por status
    estoque = sucata = caminhao = 0
    if "Status" in df_filtrado.columns:
        vc = df_filtrado["Status"].value_counts()
        estoque  = int(vc.get("Estoque", 0))
        sucata   = int(vc.get("Sucata", 0))
        caminhao = int(vc.get("Caminhão", 0))

    # Métricas de sulco e km
    media_sulco = float(df_filtrado["Aferição - Sulco"].dropna().mean()) if "Aferição - Sulco" in df_filtrado.columns else np.nan
    media_km_afe = float(df_filtrado["Km Rodado até Aferição"].dropna().mean()) if "Km Rodado até Aferição" in df_filtrado.columns else np.nan
    max_km = float(df_filtrado["Km Rodado até Aferição"].dropna().max()) if "Km Rodado até Aferição" in df_filtrado.columns else np.nan
    min_sulco = float(df_filtrado["Aferição - Sulco"].dropna().min()) if "Aferição - Sulco" in df_filtrado.columns else np.nan

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Pneus", f"{total_pneus:,}".replace(",", "."))
    c2.metric("Estoque", f"{estoque}")
    c3.metric("Sucata", f"{sucata}")
    c4.metric("Caminhão", f"{caminhao}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Média de Sulco (mm)", f"{media_sulco:.2f}" if not np.isnan(media_sulco) else "—")
    c6.metric("Média Km até Aferição", f"{media_km_afe:,.0f} km".replace(",", ".") if not np.isnan(media_km_afe) else "—")
    c7.metric("Máximo Km até Aferição", f"{max_km:,.0f} km".replace(",", ".") if not np.isnan(max_km) else "—")
    c8.metric("Menor Sulco", f"{min_sulco:.2f} mm" if not np.isnan(min_sulco) else "—")

# ====================================
# 2) Análises por Status
# ====================================
with abas[1]:
    st.subheader("📊 Distribuição por Status")
    if "Status" in df_filtrado.columns and not df_filtrado.empty:
        base = df_filtrado["Status"].value_counts().rename_axis("Status").reset_index(name="Quantidade")
        base["%"] = 100 * base["Quantidade"] / base["Quantidade"].sum()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_bar = px.bar(base, x="Status", y="Quantidade", text="Quantidade", title="Quantidade por Status")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_g2:
            fig_pie = px.pie(base, names="Status", values="Quantidade", title="Proporção por Status", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.caption("Resumo por Status")
        st.dataframe(base, use_container_width=True)
    else:
        st.info("Coluna 'Status' não encontrada ou não há dados após filtros.")

# ====================================
# 3) Marcas e Modelos
# ====================================
with abas[2]:
    st.subheader("🏷️ Desgaste por Marca/Modelo")

    if "Aferição - Sulco" in df_filtrado.columns and "Marca (Atual)" in df_filtrado.columns:
        g_marca = df_filtrado.groupby("Marca (Atual)", dropna=True)["Aferição - Sulco"].mean().reset_index(name="Sulco Médio")
        fig_marca = px.bar(g_marca.sort_values("Sulco Médio", ascending=False),
                           x="Marca (Atual)", y="Sulco Médio", title="Sulco Médio por Marca")
        st.plotly_chart(fig_marca, use_container_width=True)
    else:
        st.info("Necessário ter 'Aferição - Sulco' e 'Marca (Atual)'.")

    if "Km Rodado até Aferição" in df_filtrado.columns and "Modelo (Atual)" in df_filtrado.columns:
        g_modelo = df_filtrado.groupby("Modelo (Atual)", dropna=True)["Km Rodado até Aferição"].mean().reset_index(name="Km Médio até Aferição")
        fig_modelo = px.bar(g_modelo.sort_values("Km Médio até Aferição", ascending=False).head(20),
                            x="Modelo (Atual)", y="Km Médio até Aferição",
                            title="Top 20 Modelos por Km Médio até Aferição")
        st.plotly_chart(fig_modelo, use_container_width=True)
    else:
        st.info("Necessário ter 'Km Rodado até Aferição' e 'Modelo (Atual)'.")

# ====================================
# 4) Veículos
# ====================================
with abas[3]:
    st.subheader("🚚 Comparativo por Veículo")

    if "Veículo - Descrição" in df_filtrado.columns and "Km Rodado até Aferição" in df_filtrado.columns:
        g_veic_sum = df_filtrado.groupby("Veículo - Descrição", dropna=True)["Km Rodado até Aferição"].sum().reset_index(name="Km Total até Aferição")
        g_veic_mean = df_filtrado.groupby("Veículo - Descrição", dropna=True)["Aferição - Sulco"].mean().reset_index(name="Sulco Médio")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            fig_v1 = px.bar(g_veic_sum.sort_values("Km Total até Aferição", ascending=False).head(20),
                            x="Veículo - Descrição", y="Km Total até Aferição",
                            title="Top 20 Veículos por Km Total até Aferição")
            st.plotly_chart(fig_v1, use_container_width=True)
        with col_v2:
            if "Aferição - Sulco" in df_filtrado.columns:
                fig_v2 = px.bar(g_veic_mean.sort_values("Sulco Médio", ascending=True).head(20),
                                x="Veículo - Descrição", y="Sulco Médio",
                                title="Top 20 Veículos com Menor Sulco Médio")
                st.plotly_chart(fig_v2, use_container_width=True)
            else:
                st.info("Necessário ter 'Aferição - Sulco' para esta análise.")
    else:
        st.info("Necessário ter 'Veículo - Descrição' e 'Km Rodado até Aferição'.")

# ====================================
# 5) Posição dos Pneus
# ====================================
with abas[4]:
    st.subheader("📍 Posição (Sigla) x Desgaste/Quilometragem")

    if "Sigla da Posição" in df_filtrado.columns:
        if "Km Rodado até Aferição" in df_filtrado.columns:
            g_pos_km = df_filtrado.groupby("Sigla da Posição", dropna=True)["Km Rodado até Aferição"].mean().reset_index(name="Km Médio até Aferição")
            fig_pk = px.bar(g_pos_km.sort_values("Km Médio até Aferição", ascending=False),
                            x="Sigla da Posição", y="Km Médio até Aferição",
                            title="Km Médio até Aferição por Posição")
            st.plotly_chart(fig_pk, use_container_width=True)
        if "Aferição - Sulco" in df_filtrado.columns:
            g_pos_sulco = df_filtrado.groupby("Sigla da Posição", dropna=True)["Aferição - Sulco"].mean().reset_index(name="Sulco Médio")
            fig_ps = px.bar(g_pos_sulco.sort_values("Sulco Médio", ascending=True),
                            x="Sigla da Posição", y="Sulco Médio",
                            title="Sulco Médio por Posição")
            st.plotly_chart(fig_ps, use_container_width=True)
    else:
        st.info("Coluna 'Sigla da Posição' não encontrada.")

# ====================================
# 6) Rankings
# ====================================
with abas[5]:
    st.subheader("🏆 Rankings")

    cols_show = [c for c in [
        "Referência", "Marca (Atual)", "Modelo (Atual)",
        "Veículo - Descrição", "Veículo - Placa",
        "Sigla da Posição", "Aferição - Sulco",
        "Hodômetro Inicial", "Observação - Km", "Km Rodado até Aferição"
    ] if c in df_filtrado.columns]

    # Top 5 por Km Rodado até Aferição
    if "Km Rodado até Aferição" in df_filtrado.columns:
        top_km = df_filtrado.sort_values("Km Rodado até Aferição", ascending=False).head(5)
        st.markdown("**Top 5 pneus que MAIS rodaram até a aferição**")
        st.dataframe(top_km[cols_show], use_container_width=True)
    else:
        st.info("Sem coluna 'Km Rodado até Aferição' para ranking de km.")

    # Top 5 pneus mais gastos (menor sulco)
    if "Aferição - Sulco" in df_filtrado.columns:
        top_gasto = df_filtrado.sort_values("Aferição - Sulco", ascending=True).head(5)
        st.markdown("**Top 5 pneus mais gastos (menor sulco)**")
        st.dataframe(top_gasto[cols_show], use_container_width=True)
    else:
        st.info("Sem coluna 'Aferição - Sulco' para ranking de sulco.")

# ====================================
# 7) Exportação
# ====================================
with abas[6]:
    st.subheader("📥 Exportar dados enriquecidos")
    st.write("O arquivo inclui as colunas derivadas **'Observação - Data'**, **'Observação - Km'** e **'Km Rodado até Aferição'** (quando disponíveis).")
    data_xlsx = download_excel(df_filtrado.copy())
    st.download_button(
        label="📥 Baixar Excel enriquecido",
        data=data_xlsx,
        file_name="pneus_enriquecido.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ------------------------------------
# Observações de compatibilidade
# ------------------------------------
# Requisitos mínimos no requirements.txt:
# streamlit
# pandas
# plotly
# openpyxl
# xlsxwriter
