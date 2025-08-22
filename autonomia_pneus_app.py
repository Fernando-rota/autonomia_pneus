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
    """Converte strings com vírgula/ponto em float de forma segura."""
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    # Caso típico BR: 1.234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return np.nan

def extrair_km_observacao(texto):
    """Extrai '109418' de textos tipo 'Aferição 20/08/25 - 109418 km'."""
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
    """Normaliza texto para comparações: remove acento, caixa alta, espaços extras."""
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = " ".join(s.split())  # colapsa espaços
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper()

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
        return "Outro"
    d = str(desc).lower()
    # Mapas pedidos
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

if arquivo:
    # ----------------- LEITURA DAS ABAS -----------------
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    if not {"pneus", "posição", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    # strip de colunas
    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns  = df_sulco.columns.str.strip()

    # ----------------- NORMALIZAÇÕES NUMÉRICAS -----------------
    # Aferição - Sulco e Sulco (aba sulco) podem vir com vírgula
    if "Aferição - Sulco" in df_pneus.columns:
        df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    else:
        st.error("Coluna 'Aferição - Sulco' não encontrada em 'pneus'.")
        st.stop()

    if "Sulco" in df_sulco.columns:
        df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    else:
        st.error("Coluna 'Sulco' não encontrada em 'sulco'.")
        st.stop()

    # Hodômetro Inicial
    if "Hodômetro Inicial" in df_pneus.columns:
        df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)

    # Vida do Pneu - Km. Rodado (preferencial para km)
    if "Vida do Pneu - Km. Rodado" in df_pneus.columns:
        df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus["Vida do Pneu - Km. Rodado"].apply(to_float)
    else:
        df_pneus["Vida do Pneu - Km. Rodado"] = np.nan

    # Extrai km de Observação quando existir
    if "Observação" in df_pneus.columns:
        df_pneus["Observação - Km"] = df_pneus["Observação"].apply(extrair_km_observacao)
    else:
        df_pneus["Observação - Km"] = np.nan

    # Km Rodado até Aferição: preferir a coluna oficial; senão, Observação - Hodômetro
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = (
        df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    )
    # se seguiu NaN ou <=0, deixa como NaN
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # ----------------- MAPA DE POSIÇÃO -----------------
    # Renomeia para casar com a coluna de sigla
    col_map_pos = {}
    if "SIGLA" in df_posicao.columns:
        col_map_pos["SIGLA"] = "Sigla da Posição"
    if "POSIÇÃO" in df_posicao.columns:
        col_map_pos["POSIÇÃO"] = "Posição"
    df_posicao = df_posicao.rename(columns=col_map_pos)

    if "Sigla da Posição" in df_pneus.columns and "Sigla da Posição" in df_posicao.columns:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # ----------------- SULCO INICIAL (ROBUSTO) -----------------
    # Normaliza chaves (Vida + Modelo) nas duas abas
    for col in ["Vida", "Modelo (Atual)"]:
        if col not in df_pneus.columns:
            st.error(f"Coluna '{col}' não encontrada em 'pneus'.")
            st.stop()
    for col in ["Vida", "Modelo (Atual)"]:
        if col not in df_sulco.columns:
            st.error(f"Coluna '{col}' não encontrada em 'sulco'.")
            st.stop()

    df_pneus["_VIDA"]   = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"]   = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)

    # Merge por (VIDA + MODELO)
    base = df_sulco[["_VIDA", "_MODELO", "Sulco"]].dropna(subset=["Sulco"]).copy()
    base = base.drop_duplicates(subset=["_VIDA", "_MODELO"], keep="first")
    df_pneus = df_pneus.merge(
        base.rename(columns={"Sulco": "Sulco Inicial"}),
        on=["_VIDA", "_MODELO"],
        how="left"
    )

    # Fallback 1: se Vida == NOVO, tenta por MODELO com vida NOVO
    map_model_novo = (
        df_sulco[df_sulco["_VIDA"] == "NOVO"]
        .dropna(subset=["Sulco"])
        .drop_duplicates("_MODELO")
        .set_index("_MODELO")["Sulco"]
        .to_dict()
    )
    cond_f1 = df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"] == "NOVO")
    df_pneus.loc[cond_f1, "Sulco Inicial"] = df_pneus.loc[cond_f1, "_MODELO"].map(map_model_novo)

    # Fallback 2: qualquer vida -> por MODELO (mediana por modelo da aba sulco)
    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    cond_f2 = df_pneus["Sulco Inicial"].isna()
    df_pneus.loc[cond_f2, "Sulco Inicial"] = df_pneus.loc[cond_f2, "_MODELO"].map(map_model_any)

    # Fallback 3: mediana por VIDA
    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    cond_f3 = df_pneus["Sulco Inicial"].isna()
    df_pneus.loc[cond_f3, "Sulco Inicial"] = df_pneus.loc[cond_f3, "_VIDA"].map(mediana_por_vida)

    # Fallback 4: mediana global
    if df_pneus["Sulco Inicial"].isna().any():
        global_med = df_sulco["Sulco"].dropna().median()
        df_pneus["Sulco Inicial"] = df_pneus["Sulco Inicial"].fillna(global_med)

    # ----------------- CÁLCULOS DERIVADOS -----------------
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    # evita divisões inválidas
    df_pneus["Desgaste (mm/km)"] = np.where(
        (df_pneus["Km Rodado até Aferição"].notna()) & (df_pneus["Km Rodado até Aferição"] > 0),
        df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"],
        np.nan
    )

    # Classificação do tipo de veículo (com base na descrição)
    if "Veículo - Descrição" in df_pneus.columns:
        df_pneus["Tipo Veículo"] = df_pneus["Veículo - Descrição"].apply(classificar_veiculo)
    else:
        df_pneus["Tipo Veículo"] = "Outro"

    # ----------------- ORDEM DE COLUNAS: colocar Sulco Inicial entre Vida e Status -----------------
    cols = df_pneus.columns.tolist()
    def insert_after(col_list, new_col, after_col):
        if new_col not in col_list:
            return col_list
        col_list = [c for c in col_list if c != new_col]
        if after_col in col_list:
            idx = col_list.index(after_col) + 1
        else:
            idx = 0
        return col_list[:idx] + [new_col] + col_list[idx:]

    if "Vida" in cols and "Sulco Inicial" in cols:
        cols = insert_after(cols, "Sulco Inicial", "Vida")
    # garantir Status mais à frente (se quiser manter logo após Sulco Inicial)
    if "Status" in cols and "Sulco Inicial" in cols:
        # move Status para ficar depois de Sulco Inicial
        cols = [c for c in cols if c != "Status"]
        si_idx = cols.index("Sulco Inicial")
        cols = cols[:si_idx+1] + ["Status"] + cols[si_idx+1:]
    df_pneus = df_pneus[cols]

    # ----------------- ABAS -----------------
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "📖 Legenda"
    ])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus.columns else len(df_pneus)
        status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus.columns else pd.Series()
        estoque = int(status_counts.get("Estoque", 0))
        sucata = int(status_counts.get("Sucata", 0))
        caminhao = int(status_counts.get("Caminhão", 0))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        col5, col6, col7 = st.columns(3)
        media_sulco = df_pneus["Aferição - Sulco"].dropna().mean()
        media_km = df_pneus["Km Rodado até Aferição"].dropna().mean()
        crit = df_pneus[df_pneus["Aferição - Sulco"] < 2]
        perc_crit = (len(crit) / len(df_pneus) * 100) if len(df_pneus) else 0.0

        col5.metric("🟢 Média Sulco (mm)", f"{media_sulco:.2f}" if pd.notna(media_sulco) else "-")
        col6.metric("🛣️ Média Km até Aferição", f"{media_km:,.0f} km" if pd.notna(media_km) else "-")
        col7.metric("⚠️ Pneus Críticos (<2mm)", len(crit), f"{perc_crit:.1f}%")

    # ----------------- GRÁFICOS -----------------
    with aba2:
        st.subheader("📊 Distribuição do Sulco Atual por Tipo de Veículo")
        fig1 = px.box(
            df_pneus,
            x="Tipo Veículo",
            y="Aferição - Sulco",
            color="Tipo Veículo",
            points="all",
            title="Sulco Atual (mm) por Tipo de Veículo"
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📊 Sulco Consumido por Tipo de Veículo")
        fig2 = px.box(
            df_pneus,
            x="Tipo Veículo",
            y="Sulco Consumido",
            color="Tipo Veículo",
            points="all",
            title="Sulco Consumido (mm) por Tipo de Veículo"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📊 Desgaste Relativo (mm/km) por Tipo de Veículo")
        fig3 = px.box(
            df_pneus,
            x="Tipo Veículo",
            y="Desgaste (mm/km)",
            color="Tipo Veículo",
            points="all",
            title="Sulco Consumido / Km Rodado"
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("📈 Aferição de Sulco vs. Hodômetro (quando disponível)")
        fig4 = px.scatter(
            df_pneus,
            x="Observação - Km",
            y="Aferição - Sulco",
            color="Tipo Veículo",
            hover_data=["Referência", "Modelo (Atual)", "Veículo - Placa"] if "Referência" in df_pneus.columns else ["Modelo (Atual)","Veículo - Placa"],
            title="Sulco x Hodômetro"
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ----------------- MEDIDAS DE SULCO -----------------
    with aba3:
        st.subheader("📏 Medidas de Sulco (com cálculos)")
        cols_show = [c for c in [
            "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
            "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição",
            "Desgaste (mm/km)","Posição","Sigla da Posição"
        ] if c in df_pneus.columns]
        df_show = df_pneus[cols_show].copy()
        st.dataframe(
            df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]) \
                         .format({"Sulco Inicial":"{:.2f}","Aferição - Sulco":"{:.2f}","Sulco Consumido":"{:.2f}","Desgaste (mm/km)":"{:.6f}"}),
            use_container_width=True
        )

    # ----------------- TABELA COMPLETA -----------------
    with aba4:
        st.subheader("📑 Tabela Completa")
        df_filtrado = df_pneus.copy()
        if "Status" in df_pneus.columns:
            status_filter = st.multiselect(
                "Filtrar por Status",
                options=sorted(df_pneus["Status"].dropna().unique().tolist()),
                default=sorted(df_pneus["Status"].dropna().unique().tolist())
            )
            df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filter)]
        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]) \
                             .format({"Sulco Inicial":"{:.2f}","Aferição - Sulco":"{:.2f}","Sulco Consumido":"{:.2f}","Desgaste (mm/km)":"{:.6f}"}),
            use_container_width=True
        )

    # ----------------- LEGENDA -----------------
    with aba5:
        st.subheader("📖 Siglas de Posição")
        if {"Sigla da Posição","Posição"}.issubset(df_pneus.columns.union(df_posicao.columns)):
            st.dataframe(df_posicao.rename(columns={"Sigla da Posição":"SIGLA","Posição":"POSIÇÃO"}), use_container_width=True)
        else:
            st.info("Não foi possível montar a legenda de posição (verifique as colunas na aba 'posição').")

        st.subheader("📖 Sulco Inicial por Modelo (Novos)")
        df_leg = df_sulco[df_sulco["_VIDA"]=="NOVO"][["Modelo (Atual)","Sulco"]].dropna()
        df_leg = df_leg.sort_values("Modelo (Atual)")
        st.dataframe(df_leg.rename(columns={"Sulco":"Sulco (mm)"}), use_container_width=True)

        st.subheader("📊 Medida da Rodagem por Tipo de Veículo (média de mm/km)")
        df_rod = df_pneus.groupby("Tipo Veículo", dropna=False)["Desgaste (mm/km)"].mean().reset_index()
        df_rod = df_rod.sort_values("Desgaste (mm/km)")
        st.dataframe(df_rod, use_container_width=True)
else:
    st.info("Aguardando upload do arquivo Excel…")
