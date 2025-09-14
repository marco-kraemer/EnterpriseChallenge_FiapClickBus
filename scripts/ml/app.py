# ============================================
# RoadWise - ClickBus | Dashboard Narrativo (PRO)
# Streamlit App com Storytelling, Filtros e AgGrid
# ============================================

import os
import time
import pandas as pd
import numpy as np
import streamlit as st

# AgGrid é opcional. Se não estiver instalado, o app cai no fallback st.dataframe.
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
    AGGRID_OK = True
except Exception:
    AGGRID_OK = False

# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(
    page_title="RoadWise | Previsão de Recompra",
    page_icon="🚍",
    layout="wide"
)

PRIMARY = "#fff"
ACCENT = "#ec5356"

# -----------------------------
# Branding (CSS)
# -----------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #02262d;
        color: {PRIMARY};
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    }}
    h1, h2, h3 {{
        color: {PRIMARY};
        font-weight: 800;
    }}
    /* KPIs (st.metric) */
    div[data-testid="stMetric"] {{
        background-color: #ec5356;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid {PRIMARY}33;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    div[data-testid="stMetricValue"] {{
        color: {PRIMARY} !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }}
    div[data-testid="stMetricLabel"] {{
        color: #000 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        opacity: 1 !important;
    }}
    /* Botões */
    .stButton > button {{
        background-color: {PRIMARY};
        color: #000;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 700;
    }}
    .stButton > button:hover {{
        background-color: {ACCENT};
        color: {PRIMARY};
    }}
    /* Chips resumo */
    .chip {{
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: {PRIMARY};
        font-size: 12px;
        color: #000;
        font-weight: 600;
    }}
    /* Estilo da tabela AgGrid */
    .ag-theme-balham {{
        --ag-header-foreground-color: {PRIMARY};
        --ag-foreground-color: {PRIMARY};
        --ag-header-background-color: #f9f9f9;
        --ag-selected-row-background-color: {ACCENT}55;
        --ag-row-hover-color: {ACCENT}33;
        --ag-borders: solid 1px {PRIMARY}22;
        border-radius: 12px;
        border: 1px solid {PRIMARY}22;
        overflow: hidden;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Header
# -----------------------------
st.markdown(f"<h1>🚍 RoadWise – Previsão de Recompra</h1>", unsafe_allow_html=True)
st.write(
    "Segmentamos clientes em **personas**, estimamos **probabilidade de recompra** em 7 e 30 dias "
    "e calculamos um **Score de Prioridade** para o time de marketing agir primeiro onde há mais retorno."
)

st.markdown("---")

# -----------------------------
# Leitura e preparação de dados
# -----------------------------
REQUIRED_COLS = {
    "customer_id",
    "segment",
    "ticket_medio",
    "prob_repurchase_7d",
    "prob_repurchase_30d",
    "score_priority"
}

@st.cache_data(show_spinner=False, ttl=300)
def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df_local = pd.read_csv(path)
    if "last_purchase" in df_local.columns:
        df_local["last_purchase"] = pd.to_datetime(df_local["last_purchase"], errors="coerce")
    for col in ["ticket_medio", "prob_repurchase_7d", "prob_repurchase_30d", "score_priority"]:
        if col in df_local.columns:
            df_local[col] = pd.to_numeric(df_local[col], errors="coerce")
    return df_local

DATA_PATH = "predictions.csv"
df = load_data(DATA_PATH)

if df.empty:
    st.error("Arquivo 'predictions.csv' não encontrado ou sem registros.")
    st.stop()

missing = REQUIRED_COLS - set(df.columns)
if missing:
    st.error(f"Colunas ausentes no dataset: {sorted(list(missing))}.")
    st.stop()

# Sanitização
for col in ["prob_repurchase_7d", "prob_repurchase_30d", "score_priority"]:
    df[col] = df[col].fillna(0.0).clip(0, 1)
df["ticket_medio"] = df["ticket_medio"].fillna(0.0).clip(lower=0)
df["customer_id"] = df["customer_id"].astype(str)

# Personas (ajustado conforme análise)
mapa_segmentos = {
    0: "Clientes Regulares de Baixo Ticket",
    1: "Clientes de Alto Ticket e Baixa Frequência",
    2: "Clientes Frequentes e Fiéis",
    3: "Clientes Inativos ou Perdidos"
}
if "persona" not in df.columns:
    df["persona"] = df["segment"].map(mapa_segmentos).fillna("n/a")

# -----------------------------
# Sidebar meta
# -----------------------------
with st.sidebar:
    st.info("RoadWise • Enterprise Challenge FIAP | ClickBus")
    st.caption(f"Registros: **{df.shape[0]:,}**".replace(",", "."))
    try:
        mtime = os.path.getmtime(DATA_PATH)
        st.caption("Atualizado em: **" + time.strftime("%d/%m/%Y %H:%M", time.localtime(mtime)) + "**")
    except Exception:
        pass
    if not AGGRID_OK:
        st.warning("Para a tabela PRO, instale: `pip install streamlit-aggrid`")

# -----------------------------
# KPIs gerais
# -----------------------------
st.subheader("📊 Visão Geral")
col1, col2, col3, col4 = st.columns(4)
total_cli = int(df.shape[0])
ticket_med = float(df["ticket_medio"].mean())
pct_quentes = float((df["score_priority"] >= 0.7).mean() * 100)
receita_pot = float((df["ticket_medio"] * df["prob_repurchase_30d"]).sum())

col1.metric("Clientes Totais", f"{total_cli}", help="Tamanho da base em análise.")
col2.metric("Ticket Médio", f"R$ {ticket_med:.2f}", help="Média do valor de compras por cliente.")
col3.metric("% Clientes Quentes", f"{pct_quentes:.1f}%", help="Score ≥ 0.70.")
col4.metric("Receita Potencial (30d)", f"R$ {receita_pot:,.0f}".replace(",", "."), help="Ticket × Prob. 30d somado na base.")

st.markdown("---")

# -----------------------------
# Personas compactas (ajustado)
# -----------------------------
with st.expander("🧭 Segmentos e características"):
    st.markdown("""
- **Clientes Regulares de Baixo Ticket** — Ticket médio em torno de R$140, cerca de 3 compras na vida, pouca atividade recente (última compra ~500 dias).  
  *Descrição:* compram de forma esporádica, gastos moderados e frequência inconsistente.

- **Clientes de Alto Ticket e Baixa Frequência** — Ticket médio elevado (~R$590), 1 a 2 compras em média, última compra há mais de 800 dias.  
  *Descrição:* clientes de alto valor por transação, porém raros e pouco confiáveis para recorrência.

- **Clientes Frequentes e Fiéis** — Ticket médio menor (~R$134), mas com volume alto (33 compras em média), últimas compras muito recentes (~70 dias).  
  *Descrição:* clientes mais engajados, base ativa e recorrente que sustenta o negócio.

- **Clientes Inativos ou Perdidos** — Ticket médio ~R$146, 1 a 2 compras em média, última compra há mais de 2000 dias.  
  *Descrição:* clientes praticamente abandonados, baixíssima chance de retorno.
""")

# -----------------------------
# Helper para query_params
# -----------------------------
def get_param(params, key, default=""):
    val = params.get(key, default)
    if isinstance(val, list):
        return val[0] if val else default
    return val

# -----------------------------
# Filtros e presets
# -----------------------------
st.subheader("📋 Ranking de Clientes para Marketing")

params_in = st.query_params

persona_default = params_in.get("persona", [])
score_default = float(get_param(params_in, "score_min", "0.70"))
ticket_min_default = float(get_param(params_in, "ticket_min", "0.0"))
search_default = get_param(params_in, "search", "")
topn_default = int(get_param(params_in, "topn", "300"))
days_last_purchase_default = int(get_param(params_in, "days_last_purchase_max", "9999"))

f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 2, 2])

personas_disp = sorted(df["persona"].dropna().unique().tolist())
sel_personas = f1.multiselect("Persona", personas_disp, default=persona_default)

score_min = f2.slider("Score mínimo", 0.0, 1.0, value=score_default, step=0.05)
ticket_min = f3.number_input("Ticket mínimo (R$)", min_value=0.0, value=ticket_min_default, step=10.0, format="%.2f")
search_id = f4.text_input("Buscar por Customer ID", value=search_default, help="Busca parcial. Ex.: 123 ou john")
top_n = f5.number_input("Top N para exibir", min_value=10, max_value=10000, value=topn_default, step=10)

# Filtro opcional por recência
if "last_purchase" in df.columns:
    max_days = int((pd.Timestamp.today() - df["last_purchase"].min()).days) if df["last_purchase"].notna().any() else 3650
    days_last_purchase_max = st.slider(
        "Máx. dias desde a última compra (opcional)",
        min_value=0, max_value=max(30, max_days), value=min(days_last_purchase_default, max_days), step=10,
        help="Filtra clientes que compraram dentro da janela escolhida."
    )
else:
    days_last_purchase_max = 9999

# Presets rápidos
pcol1, pcol2, pcol3, pcol4 = st.columns(4)
if pcol1.button("🔥 Top 100 Quentes"):
    sel_personas = []
    score_min = 0.8
    top_n = 100
if pcol2.button("🏆 Alto Ticket"):
    sel_personas = ["Clientes de Alto Ticket e Baixa Frequência"]
    score_min = 0.5
    top_n = 200
if pcol3.button("🔁 Frequentes"):
    sel_personas = ["Clientes Frequentes e Fiéis"]
    score_min = 0.4
    top_n = 300
if pcol4.button("💤 Inativos"):
    sel_personas = ["Clientes Inativos ou Perdidos"]
    score_min = 0.3
    top_n = 300

# -----------------------------
# Aplicação de filtros
# -----------------------------
fdf = df.copy()
if sel_personas:
    fdf = fdf[fdf["persona"].isin(sel_personas)]

fdf = fdf[
    (fdf["score_priority"].fillna(0) >= float(score_min)) &
    (fdf["ticket_medio"].fillna(0) >= float(ticket_min))
]

if search_id:
    s = search_id.strip().lower()
    fdf = fdf[fdf["customer_id"].str.lower().str.contains(s)]

if "last_purchase" in fdf.columns and pd.api.types.is_datetime64_any_dtype(fdf["last_purchase"]):
    days_since = (pd.Timestamp.today().normalize() - fdf["last_purchase"].dt.normalize()).dt.days
    days_since = days_since.fillna(10**9)
    fdf = fdf[days_since <= days_last_purchase_max]

fdf = fdf.sort_values("score_priority", ascending=False)

# -----------------------------
# Resumo dos filtros
# -----------------------------
filtrados = int(fdf.shape[0])
pct_quentes_f = float((fdf["score_priority"] >= 0.7).mean() * 100) if filtrados else 0.0
ticket_med_f = float(fdf["ticket_medio"].mean()) if filtrados else 0.0
receita_pot_f = float((fdf["ticket_medio"] * fdf["prob_repurchase_30d"]).sum()) if filtrados else 0.0

st.markdown(
    f"""
    <div>
      <span class="chip">Registros filtrados: <b>{filtrados}</b></span>
      <span class="chip">% quentes (≥0.70): <b>{pct_quentes_f:.1f}%</b></span>
      <span class="chip">Ticket médio filtrado: <b>R$ {ticket_med_f:.2f}</b></span>
      <span class="chip">Receita Potencial 30d: <b>R$ {receita_pot_f:,.0f}</b></span>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True
)

conv = st.slider("Se o time converter (%) deste conjunto filtrado", 0, 50, 8, step=1)
impacto = (fdf["ticket_medio"] * (conv / 100.0)).sum() if filtrados else 0.0
st.caption(f"Impacto estimado se {conv}% converterem: **R$ {impacto:,.0f}**".replace(",", "."))

st.markdown("")

# -----------------------------
# Tabela PRO (AgGrid) ou fallback
# -----------------------------
cols_show = ["customer_id", "persona", "ticket_medio", "prob_repurchase_7d", "prob_repurchase_30d", "score_priority"]
cols_show = [c for c in cols_show if c in fdf.columns]
view = fdf[cols_show].head(int(top_n)).copy()

st.download_button(
    label="⬇️ Baixar CSV do conjunto filtrado",
    data=fdf[cols_show].to_csv(index=False).encode("utf-8"),
    file_name="roadwise_ranking_filtrado.csv",
    mime="text/csv",
    use_container_width=True
)

if AGGRID_OK:
    gb = GridOptionsBuilder.from_dataframe(view)
    gb.configure_default_column(filter=True, floatingFilter=True, sortable=True, resizable=True)
    gb.configure_column("customer_id", header_name="Cliente", width=140)
    if "persona" in view.columns:
        gb.configure_column("persona", header_name="Persona", width=220)
    if "ticket_medio" in view.columns:
        gb.configure_column(
            "ticket_medio",
            header_name="Ticket Médio",
            type=["rightAligned", "numericColumn"],
            valueFormatter="value == null ? '' : 'R$ ' + Number(value).toFixed(2)",
            width=140
        )
    for colp, headerp in [
        ("prob_repurchase_7d", "Prob. Recompra 7d"),
        ("prob_repurchase_30d", "Prob. Recompra 30d"),
        ("score_priority", "Score Prioridade"),
    ]:
        if colp in view.columns:
            gb.configure_column(
                colp,
                header_name=headerp,
                type=["rightAligned", "numericColumn"],
                valueFormatter="value == null ? '' : (Number(value)*100).toFixed(1) + '%'",
                width=160
            )
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
    grid_options = gb.build()

    q = st.text_input("🔎 Busca rápida (na tabela)", "")
    if q:
        grid_options["quickFilterText"] = q

    grid = AgGrid(
        view,
        gridOptions=grid_options,
        height=520,
        update_on=["selectionChanged"],
        theme="balham",
        allow_unsafe_jscode=True
    )

    selected = grid.get("selected_rows", [])
    if selected:
        st.success(f"{len(selected)} clientes selecionados para ação")
        st.download_button(
            "⬇️ Baixar seleção",
            data=pd.DataFrame(selected)[cols_show].to_csv(index=False).encode("utf-8"),
            file_name="roadwise_selecao.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("Tabela PRO requer `streamlit-aggrid`. Exibindo versão básica.")
    st.dataframe(view, use_container_width=True, height=520, hide_index=True)

st.markdown("---")

st.write(
    "Resumo: os filtros definem o alvo, o ranking dá o caminho e o simulador converte análise em impacto esperado. "
    "Pronto para o time agir sem achismo."
)

# -----------------------------
# Persistência dos filtros em URL
# -----------------------------
st.query_params.clear()
st.query_params.update({
    "persona": sel_personas,
    "score_min": str(score_min),
    "ticket_min": str(ticket_min),
    "search": search_id,
    "topn": str(top_n),
    "days_last_purchase_max": str(days_last_purchase_max),
})
