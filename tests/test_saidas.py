"""Regressão: a demonstração não pode substituir respostas já entregues."""

import csv

import pytest
from agente import agent
from scripts.dados import ROOT, conectar
from scripts.gerar_sql import FINAIS


@pytest.mark.parametrize("nome", FINAIS)
def test_csv_entregue_corresponde_ao_sql(nome):
    with conectar() as conn:
        cursor = conn.execute((ROOT / "sql" / f"{nome}.sql").read_text(encoding="utf-8"))
        esperado = [[coluna[0] for coluna in cursor.description]]
        esperado.extend([
            "" if valor is None else f"{valor:.2f}" if isinstance(valor, float) else str(valor)
            for valor in linha
        ] for linha in cursor.fetchall())
    with (ROOT / "respostas" / f"{nome}.csv").open(encoding="utf-8", newline="") as arquivo:
        assert list(csv.reader(arquivo)) == esperado


def test_demonstracao_preserva_respostas_e_separa_execucoes(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "ROOT", tmp_path)
    respostas = tmp_path / "agente/respostas.md"
    respostas.parent.mkdir()
    respostas.write_text("Evidência entregue", encoding="utf-8")

    primeira = agent.demonstrar()
    segunda = agent.demonstrar()

    assert respostas.read_text(encoding="utf-8") == "Evidência entregue"
    assert primeira != segunda
    assert primeira.parent == tmp_path / "work/execucoes"
    for pasta in (primeira, segunda):
        assert (pasta / "execucoes.json").is_file()
        texto = (pasta / "respostas.md").read_text(encoding="utf-8")
        assert "84,43" in texto and "Área não encontrada" in texto
