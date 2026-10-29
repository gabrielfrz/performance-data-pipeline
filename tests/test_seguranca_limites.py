import pytest
from agente.roteamento import argumentos_na_pergunta
from agente.tools import Ferramentas
from scripts.dados import conectar


@pytest.mark.parametrize("limite", ["-10", "−10", "-10,5", "1e1", "#10"])
def test_nao_aceita_limite_parcial_ou_sinal_trocado(limite):
    assert not argumentos_na_pergunta(
        {"score_maximo": 10}, f"Score abaixo de {limite}?"
    )


@pytest.mark.parametrize(
    "limite,valor", [("90", 90), ("+90", 90), ("89,5", 89.5), ("90.", 90)]
)
def test_preserva_limites_validos(limite, valor):
    assert argumentos_na_pergunta({"score_maximo": valor}, f"Score abaixo de {limite}?")


@pytest.mark.parametrize(
    "metodo,args",
    [
        ("listar_colaboradores_por_gestor", ("Sofia Oliveira", 10**400)),
        ("consultar_metas_colaborador", ("Nicolas Vasconcelos", 10**400)),
    ],
)
def test_inteiro_excessivo_rejeitado_sem_sql(metodo, args):
    with conectar() as conn:
        ferramentas = Ferramentas(conn)
        resultado = getattr(ferramentas, metodo)(*args)
    assert resultado["status"] == "argumento_invalido"
    assert not ferramentas.evidencias
