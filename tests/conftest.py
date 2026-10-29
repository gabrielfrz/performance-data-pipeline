"""Seleção explícita de integração e saídas isoladas do projeto."""
import hashlib
import json
import time
from datetime import datetime, timezone

import pytest
from scripts.dados import ROOT


def pytest_addoption(parser):
    parser.addoption("--ollama", action="store_true", help="Incluir integração com Ollama local")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--ollama"):
        return
    selecionados = [item for item in items if "ollama" not in item.keywords]
    opcionais = [item for item in items if "ollama" in item.keywords]
    config.hook.pytest_deselected(items=opcionais)
    items[:] = selecionados


@pytest.fixture(scope="session", autouse=True)
def preservar_entrega():
    """Detecta alteração na fonte, resultados e documentação durante a suíte."""
    pastas = ("dados", "respostas", "sql", "docs")
    def hashes():
        arquivos = [f for nome in pastas for f in (ROOT / nome).rglob("*") if f.is_file()]
        arquivos += [ROOT / "agente/respostas.md", ROOT / "painel/painel.png"]
        return {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in arquivos}
    antes = hashes()
    yield
    assert hashes() == antes, "Um teste alterou os arquivos da entrega"


@pytest.fixture(scope="session")
def registrar_llm(tmp_path_factory):
    inicio = time.perf_counter()
    registros = []
    arquivo = tmp_path_factory.mktemp("ollama") / "llm_real.json"

    def registrar(resultado):
        registros.append(resultado)
        relatorio = {
            "data_utc": datetime.now(timezone.utc).isoformat(),
            "origem": "pytest: tests/integracao/test_ollama.py",
            "sem_fallback": True,
            "registros": registros,
            "aprovados": sum(r["aprovado"] for r in registros),
            "total": len(registros),
            "duracao_segundos": time.perf_counter() - inicio,
        }
        arquivo.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Evidência desta execução: {arquivo}")
    return registrar
