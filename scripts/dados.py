"""Leitura compartilhada por exportação, painel e ferramentas. Fonte somente leitura."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "dados/case_metas.db"


@contextmanager
def conectar(path=DB):
    if not Path(path).is_file():
        raise FileNotFoundError(
            "Banco dados/case_metas.db ausente. Extraia novamente a entrega completa."
        )
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def base_sql():
    return (ROOT / "sql/base_calculo.sql").read_text(encoding="utf-8")


def consulta(conn, select, params=()):
    # select é exclusivamente SQL fixo do código; nunca vem da pergunta do usuário.
    return [dict(r) for r in conn.execute(base_sql() + "\n" + select, params)]


def carregar_painel(conn):
    """DataFrames apenas na fronteira com a visualização; SQL e agente usam sqlite3."""
    import pandas as pd

    return (
        pd.DataFrame(
            consulta(conn, "SELECT * FROM scores ORDER BY id_colaborador"),
            columns=["id_colaborador", "nome", "id_area", "id_gestor", "score"],
        ),
        pd.DataFrame(
            consulta(conn, "SELECT * FROM areas ORDER BY id_area"),
            columns=[
                "id_area",
                "nome",
                "id_area_pai",
                "score_direto",
                "score_consolidado",
            ],
        ),
    )
