"""Execute na raiz: python -m streamlit run painel/app.py"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scripts.dados import carregar_painel, conectar

st.set_page_config(page_title="Grupo Aurora | Metas 2025", layout="wide")
st.markdown(
    """<style>
.block-container {padding-top:4.5rem;padding-bottom:1rem;max-width:1440px;}
/* Rolagem no documento permite capturar a página inteira no navegador. */
[data-testid="stApp"], [data-testid="stAppViewContainer"] {position:relative;height:auto;overflow:visible;}
[data-testid="stMain"] {height:auto;overflow:visible;}
h1 {font-size:2rem!important;letter-spacing:-.6px;}
h3 {font-size:1.05rem!important;}
[data-testid="stMetric"] {border-top:3px solid #197c80;padding:12px 14px;background:#f3f6f9;}
[data-testid="stMetricValue"] {color:#17344c;}
</style>""",
    unsafe_allow_html=True,
)

try:
    with conectar() as conn:
        pessoas, areas = carregar_painel(conn)
except (OSError, sqlite3.DatabaseError):
    st.error(
        "Não foi possível carregar os resultados. Verifique se dados/case_metas.db e "
        "sql/base_calculo.sql estão presentes e íntegros. Extraia novamente a entrega, se necessário."
    )
    st.stop()


def numero(valor):
    if valor is None or valor != valor:
        return "Sem score"
    return f"{valor:.2f}".replace(".", ",")


def estilo(fig, height):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=20, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#33485c", size=12),
        legend=dict(orientation="h", y=1.12, x=0),
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf1f5", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


st.caption("GRUPO AURORA  /  FECHAMENTO DO CICLO 2025")
st.title("Resultados de metas")
st.caption(
    "Visão executiva • Notas de metas de 0 a 120 • Elegibilidade conforme o ciclo • Dados fictícios"
)
if pessoas.empty:
    st.info(
        "Nenhum colaborador elegível no ciclo 2025. Não há score médio para apresentar."
    )
    st.stop()
if not pessoas["score"].notna().any():
    st.info(
        "Há colaboradores elegíveis, mas nenhum possui score calculável. Ausência de score não é zero."
    )
pontuados = pessoas["score"].notna()
cols = st.columns(4)
cols[0].metric(
    "Score médio",
    numero(pessoas.loc[pontuados, "score"].mean()) if pontuados.any() else "Sem score",
)
cols[1].metric("Colaboradores elegíveis", len(pessoas))
cols[2].metric("Colaboradores pontuados", int(pontuados.sum()))
cols[3].metric("Sem score", int((~pontuados).sum()))

esquerda, direita = st.columns([1.1, 1])
diretorias = areas[areas.id_area_pai.isna()].sort_values("score_consolidado")
with esquerda:
    st.subheader("Resultado consolidado por diretoria")
    fig = px.bar(
        diretorias,
        x="score_consolidado",
        y="nome",
        orientation="h",
        text=diretorias.score_consolidado.map(numero),
        color_discrete_sequence=["#197c80"],
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Score: %{x:.2f}<extra></extra>",
    )
    fig.update_xaxes(range=[0, 125], title=None)
    fig.update_yaxes(title=None)
    fig.add_vline(x=100, line_dash="dot", line_color="#8a99a8")
    st.plotly_chart(estilo(fig, 245), width="stretch", config={"displayModeBar": False})
with direita:
    st.subheader("Distribuição dos scores individuais")
    fig = go.Figure(
        go.Histogram(
            x=pessoas.loc[pontuados, "score"],
            xbins=dict(start=0, end=120, size=10),
            marker_color="#294d6c",
            hovertemplate="Faixa: %{x}<br>Pessoas: %{y}<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 125], title=None, dtick=20)
    fig.update_yaxes(title="Colaboradores", dtick=5)
    st.plotly_chart(estilo(fig, 245), width="stretch", config={"displayModeBar": False})

st.subheader("Áreas | score direto e consolidado")
ordenadas = areas.sort_values("score_consolidado")
fig = go.Figure()
for coluna, nome, cor, simbolo in [
    ("score_direto", "Direto", "#9aa9b7", "circle-open"),
    ("score_consolidado", "Consolidado", "#197c80", "circle"),
]:
    fig.add_trace(
        go.Scatter(
            x=ordenadas[coluna],
            y=ordenadas.nome,
            name=nome,
            mode="markers",
            marker=dict(size=10, color=cor, symbol=simbolo, line=dict(width=2)),
            hovertemplate="%{y}<br>" + nome + ": %{x:.2f}<extra></extra>",
        )
    )
fig.update_xaxes(range=[0, 125], title="Score", dtick=20)
fig.add_vline(x=100, line_dash="dot", line_color="#8a99a8")
st.plotly_chart(estilo(fig, 350), width="stretch", config={"displayModeBar": False})
st.caption(
    "Direto: pessoas da própria área. Consolidado: inclui todas as subáreas; cada pessoa tem o mesmo peso. "
    "Ausência de score não é zero. As médias usam os valores completos antes do arredondamento."
)
