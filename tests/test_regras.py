import sqlite3

import pytest
from scripts.dados import ROOT, carregar_painel, conectar, consulta
from scripts.gerar_sql import gerar


@pytest.fixture
def db():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    with conectar() as original:
        for row in original.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
            c.execute(row[0])
    c.execute("INSERT INTO area VALUES (1, 'Diretoria', NULL)")
    c.execute(
        "INSERT INTO ciclo VALUES (2025, 'Ciclo 2025', '2025-01-01', '2025-12-31')"
    )
    c.execute("INSERT INTO colaborador VALUES (1,'Pessoa',1,NULL,'2020-01-01',NULL)")
    yield c
    c.close()


def meta(
    c,
    id=1,
    pessoa=1,
    peso=100,
    acumulacao="Soma",
    polaridade="Melhor para cima",
    ref=None,
):
    c.execute(
        "INSERT INTO meta VALUES (?,2025,?,?,?,?,?,?,?)",
        (
            id,
            pessoa,
            f"Meta {id}",
            "Individual" if ref is None else "Compartilhada",
            ref,
            polaridade,
            acumulacao,
            peso,
        ),
    )


def mes(c, p=100, r=100, id_meta=1, mes=1, nsa=0, data="2025-02-01"):
    c.execute(
        "INSERT INTO meta_valor_mensal VALUES (NULL,?,?,?,?,?,?)",
        (id_meta, mes, p, r, nsa, data),
    )


def nota(c, id=1):
    return consulta(c, "SELECT * FROM notas_meta WHERE id_meta=?", (id,))[0]


@pytest.mark.parametrize(
    "atingimento,esperada", [(0.7999, 0), (0.8, 80), (1.2, 120), (1.5, 120), (0, 0)]
)
def test_limites(db, atingimento, esperada):
    meta(db)
    mes(db, p=1, r=atingimento)
    assert nota(db)["nota"] == pytest.approx(esperada)


@pytest.mark.parametrize(
    "acumulacao,polaridade,esperado",
    [
        ("Soma", "Melhor para cima", 150 / 300),
        ("Média", "Melhor para cima", (100 / 100 + 50 / 200) / 2),
        ("Soma", "Melhor para baixo", 300 / 150),
        ("Média", "Melhor para baixo", (100 / 100 + 200 / 50) / 2),
    ],
)
def test_acumulacao_polaridade(db, acumulacao, polaridade, esperado):
    meta(db, acumulacao=acumulacao, polaridade=polaridade)
    mes(db, p=100, r=100)
    mes(db, p=200, r=50, mes=2)
    assert nota(db)["atingimento"] == pytest.approx(esperado)


def test_duplicado_mais_recente(db):
    meta(db)
    mes(db, r=50)
    mes(db, r=110, data="2025-03-01")
    assert nota(db)["nota"] == pytest.approx(110)


@pytest.mark.parametrize("p,r,nsa", [(None, 100, 0), (100, None, 0), (100, 100, 1)])
def test_recente_invalido_nao_recupera_anterior(db, p, r, nsa):
    meta(db)
    mes(db)
    mes(db, p=p, r=r, nsa=nsa, data="2025-03-01")
    assert nota(db)["nota"] is None


def test_empate_data_usa_maior_id(db):
    meta(db)
    mes(db, r=90)
    mes(db, r=110)
    assert nota(db)["nota"] == pytest.approx(110)


def test_sem_meses_e_sem_score(db):
    meta(db)
    assert nota(db)["nota"] is None
    assert consulta(db, "SELECT score FROM scores")[0]["score"] is None


@pytest.mark.parametrize(
    "acum,pol,p,r",
    [
        ("Soma", "Melhor para cima", 0, 10),
        ("Soma", "Melhor para baixo", 10, 0),
        ("Média", "Melhor para cima", 0, 10),
        ("Média", "Melhor para baixo", 10, 0),
        ("Soma", "Melhor para cima", 0, 0),
    ],
)
def test_divisao_zero(db, acum, pol, p, r):
    meta(db, acumulacao=acum, polaridade=pol)
    mes(db, p=p, r=r)
    assert nota(db)["nota"] is None


def test_media_nao_omite_mes_indefinido(db):
    meta(db, acumulacao="Média")
    mes(db)
    mes(db, p=0, r=10, mes=2)
    assert nota(db)["nota"] is None


def test_soma_zero_mensal_nao_invalida_total(db):
    meta(db)
    mes(db, p=0, r=10)
    mes(db, p=100, r=90, mes=2)
    assert nota(db)["nota"] == 100


def test_compartilhada_usa_fonte_e_peso_proprio(db):
    meta(db, peso=20)
    mes(db, r=80)
    meta(db, id=2, peso=80, ref=1, acumulacao="Média", polaridade="Melhor para baixo")
    mes(db, id_meta=2, r=0)
    meta(db, id=3, peso=100)
    mes(db, id_meta=3, r=120)
    assert nota(db, 2)["nota"] == 80
    assert consulta(db, "SELECT score FROM scores")[0]["score"] == 100


def test_sem_nota_excluida_denominador_e_peso_negativo(db):
    meta(db, peso=10)
    mes(db, r=90)
    meta(db, id=2, peso=90)
    meta(db, id=3, peso=-5)
    mes(db, id_meta=3, r=120)
    # R9: (90*10 + 120*(-5)) / (10-5) = 60. A meta sem nota não entra.
    assert consulta(db, "SELECT score FROM scores")[0]["score"] == 60
    assert nota(db, 3)["status"] == "peso_negativo"
    assert nota(db, 3)["entra_score"] == 1


@pytest.mark.parametrize(
    "adm,desl,elegivel",
    [
        ("2025-09-30", None, True),
        ("2025-10-01", None, False),
        ("2020-01-01", "2025-07-01", True),
        ("2020-01-01", "2025-06-30", False),
    ],
)
def test_elegibilidade_limites(db, adm, desl, elegivel):
    db.execute(
        "UPDATE colaborador SET data_admissao=?,data_desligamento=?", (adm, desl)
    )
    assert bool(consulta(db, "SELECT * FROM scores")) == elegivel


def test_area_vazia_e_hierarquia_media_de_pessoas(db):
    db.executemany(
        "INSERT INTO area VALUES (?,?,?)",
        [(2, "Gerência", 1), (3, "Coordenação", 2), (4, "Vazia", None)],
    )
    db.executemany(
        "INSERT INTO colaborador VALUES (?,?,?,NULL,?,NULL)",
        [(2, "B", 3, "2020-01-01"), (3, "C", 3, "2020-01-01")],
    )
    for i, r in [(1, 80), (2, 100), (3, 120)]:
        meta(db, id=i, pessoa=i)
        mes(db, id_meta=i, r=r)
    rows = {r["id_area"]: r for r in consulta(db, "SELECT * FROM areas")}
    assert rows[1]["score_consolidado"] == 100
    assert rows[2]["score_consolidado"] == 110
    assert rows[4]["score_direto"] is None and rows[4]["score_consolidado"] is None


def test_circular_referencia_inexistente_e_cadeia(db):
    meta(db, id=1, ref=2)
    meta(db, id=2, ref=1)
    meta(db, id=3, ref=999)
    for i in [1, 2, 3]:
        assert nota(db, i)["nota"] is None
    meta(db, id=4)
    mes(db, id_meta=4, r=90)
    meta(db, id=5, ref=4)
    meta(db, id=6, ref=5)
    assert nota(db, 6)["nota"] == 90


def test_outro_ciclo_nao_entra(db):
    meta(db)
    mes(db)
    db.execute("UPDATE meta SET id_ciclo=2024")
    assert consulta(db, "SELECT score FROM scores")[0]["score"] is None


def preparar_times(c):
    c.execute("DELETE FROM colaborador")
    for g in range(1, 5):
        c.execute(
            "INSERT INTO colaborador VALUES (?,?,1,NULL,?,NULL)",
            (g, f"Gestor {g}", "2020-01-01"),
        )
        for j in range(3):
            i = g * 10 + j
            c.execute(
                "INSERT INTO colaborador VALUES (?,?,1,?,?,NULL)",
                (i, f"Pessoa {i}", g, "2020-01-01"),
            )
            meta(c, id=i, pessoa=i)
            mes(c, id_meta=i)


def test_gestores_empate_e_minimo(db):
    preparar_times(db)
    db.execute(
        "UPDATE colaborador SET data_admissao=? WHERE id_colaborador=10",
        ("2025-10-01",),
    )
    rows = consulta(db, "SELECT * FROM ranking_gestores ORDER BY pos_top")
    assert [r["id_gestor"] for r in rows] == [2, 3, 4]
    assert [r["pos_bottom"] for r in rows] == [1, 2, 3]


def test_gestor_ativo_e_contagem_elegiveis_sem_score(db):
    preparar_times(db)
    db.execute(
        "UPDATE colaborador SET data_desligamento='2025-12-31' WHERE id_colaborador=1"
    )
    db.execute("DELETE FROM meta_valor_mensal WHERE id_meta=20")
    rows = {r["id_gestor"]: r for r in consulta(db, "SELECT * FROM times_gestores")}
    assert 1 not in rows
    assert (
        rows[2]["subordinados_elegiveis"] == 3
        and rows[2]["subordinados_pontuados"] == 2
    )


def test_sql_gerado_sincronizado():
    gerar(check=True)


def test_fonte_somente_leitura():
    with conectar() as c:
        with pytest.raises(sqlite3.OperationalError):
            c.execute("DELETE FROM meta")


def test_painel_mesmos_scores():
    with conectar() as c:
        pessoas, areas = carregar_painel(c)
        p1 = c.execute(
            (ROOT / "sql/p1_score_colaborador.sql").read_text(encoding="utf-8")
        ).fetchall()
        p2 = c.execute(
            (ROOT / "sql/p2_score_area.sql").read_text(encoding="utf-8")
        ).fetchall()
        assert len(pessoas) == len(p1)
        for r in p1:
            assert pessoas.set_index("id_colaborador").loc[
                r[0], "score"
            ] == pytest.approx(r[1], abs=0.005)
        for r in p2:
            assert areas.set_index("id_area").loc[
                r[0], "score_consolidado"
            ] == pytest.approx(r[2], abs=0.005)


@pytest.mark.parametrize("peso_segunda,esperado", [(-10, None), (-20, 150), (0, 90)])
def test_r9_denominador_zero_negativo_e_peso_zero(db, peso_segunda, esperado):
    meta(db, peso=10)
    mes(db, r=90)
    meta(db, id=2, peso=peso_segunda)
    mes(db, id_meta=2, r=120)
    # Pesos originais: denominador nulo é indefinido; negativo não autoriza exclusão/teto.
    assert consulta(db, "SELECT score FROM scores")[0]["score"] == esperado


@pytest.mark.parametrize("peso,esperado", [(-5, 90), (0, None)])
def test_r9_unica_meta_com_peso_nao_positivo(db, peso, esperado):
    meta(db, peso=peso)
    mes(db, r=90)
    assert nota(db)["entra_score"] == 1
    assert consulta(db, "SELECT score FROM scores")[0]["score"] == esperado


@pytest.mark.parametrize("acumulacao", ["Soma", "Média"])
@pytest.mark.parametrize("polaridade,p,r", [
    ("Melhor para cima", 100, 0),
    ("Melhor para baixo", 0, 100),
])
def test_atingimento_zero_tem_nota_zero(db, acumulacao, polaridade, p, r):
    meta(db, acumulacao=acumulacao, polaridade=polaridade)
    mes(db, p=p, r=r)
    assert nota(db)["atingimento"] == 0
    assert nota(db)["nota"] == 0
    assert nota(db)["entra_score"] == 1


@pytest.mark.parametrize("polaridade", ["Melhor para cima", "Melhor para baixo"])
@pytest.mark.parametrize("acumulacao", ["Soma", "Média"])
def test_zero_sobre_zero_indefinido(db, polaridade, acumulacao):
    meta(db, polaridade=polaridade, acumulacao=acumulacao)
    mes(db, p=0, r=0)
    assert nota(db)["atingimento"] is None
    assert nota(db)["nota"] is None


@pytest.mark.parametrize("polaridade", ["Melhor para cima", "Melhor para baixo"])
@pytest.mark.parametrize("acumulacao", ["Soma", "Média"])
def test_valor_mensal_negativo_nao_e_nulo(db, polaridade, acumulacao):
    meta(db, polaridade=polaridade, acumulacao=acumulacao)
    mes(db, p=100, r=-100)
    assert nota(db)["atingimento"] == -1
    assert nota(db)["nota"] == 0


def test_nota_aplicada_depois_da_media_de_atingimentos(db):
    meta(db, acumulacao="Média")
    mes(db, p=100, r=50)
    mes(db, p=100, r=150, mes=2)
    assert nota(db)["atingimento"] == 1
    assert nota(db)["nota"] == 100  # Não é a média das notas mensais 0 e 120.


def test_lancamento_apos_fim_ciclo_conta(db):
    meta(db)
    mes(db, mes=12, data="2026-01-15", r=90)
    assert nota(db)["nota"] == 90  # R1 filtra o ciclo, não a data da importação.


def test_compartilhada_com_peso_negativo_usa_peso_proprio(db):
    meta(db, peso=20)
    mes(db, r=80)
    meta(db, id=2, peso=-5, ref=1)
    meta(db, id=3, peso=10)
    mes(db, id_meta=3, r=120)
    assert nota(db, 2)["nota"] == 80
    assert consulta(db, "SELECT score FROM scores")[0]["score"] == 96


def test_area_exclui_score_indefinido_sem_remover_elegivel(db):
    meta(db, peso=0)
    mes(db, r=120)
    db.execute("INSERT INTO colaborador VALUES (2,'Outra pessoa',1,NULL,'2020-01-01',NULL)")
    meta(db, id=2, pessoa=2)
    mes(db, id_meta=2, r=90)
    assert len(consulta(db, "SELECT * FROM scores")) == 2
    assert consulta(db, "SELECT score_direto FROM areas")[0]["score_direto"] == 90


@pytest.mark.parametrize("admissao,desligamento,entra", [
    ("2025-10-01", None, True),
    ("2026-01-01", None, False),
    ("2020-01-01", "2025-12-31", False),
    ("2020-01-01", "2026-01-01", True),
])
def test_gestor_ativo_independe_da_elegibilidade_propria(db, admissao, desligamento, entra):
    preparar_times(db)
    db.execute("UPDATE colaborador SET data_admissao=?,data_desligamento=? WHERE id_colaborador=1", (admissao, desligamento))
    ids = [r["id_gestor"] for r in consulta(db, "SELECT * FROM times_gestores")]
    assert (1 in ids) == entra


def test_todos_subordinados_sem_score_nao_produz_ranking(db):
    preparar_times(db)
    db.execute("DELETE FROM meta_valor_mensal WHERE id_meta BETWEEN 10 AND 12")
    assert 1 not in [r["id_gestor"] for r in consulta(db, "SELECT * FROM times_gestores")]
