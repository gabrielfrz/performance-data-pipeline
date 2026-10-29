"""Integração real: nenhuma resposta simulada e nenhum fallback."""

import pytest
from scripts.dados import conectar
from tests.integracao.cenarios_ollama import CASOS, avaliar
from agente.agent import PERGUNTAS, responder

pytestmark = pytest.mark.ollama


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_cenario_modelo_real(caso, registrar_llm):
    with conectar() as conn:
        resultado = avaliar(caso, conn)
    registrar_llm(resultado)
    assert resultado["aprovado"], resultado


def test_ollama_real_cinco_perguntas():
    with conectar() as c:
        for p in PERGUNTAS:
            real = responder(p, c, modo="ollama")
            assert real["status"] in ("ok", "nao_encontrado"), real
            assert real["resultado"] == responder(p, c)["resultado"]
