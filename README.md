# Performance Analytics Pipeline

Pipeline de processamento e análise de indicadores de desempenho, com SQL, Python, dashboard interativo e consultas assistidas por IA.

O projeto transforma dados de um banco SQLite em três conjuntos de resultados: score por pessoa, score por área e ranking de gestores. O dashboard e o agente consultam a mesma lógica SQL usada na geração dos CSVs.

## Visão geral

O fluxo é deliberadamente simples e reproduzível:

```text
SQLite → SQL de tratamento e regras → CSVs finais → dashboard e agente
```

As regras são implementadas no SQL. Python atua na leitura do banco, na geração dos arquivos finais e nas interfaces de consumo, sem duplicar os cálculos.

## Tecnologias

- Python 3.13+
- SQLite
- SQL com CTEs
- pandas
- Streamlit e Plotly
- Ollama, opcional para consultas em linguagem natural
- pytest

## Estrutura

```text
dados/       Banco SQLite de entrada
sql/         Cálculo central e três consultas executáveis isoladamente
scripts/     Leitura do banco e geração dos resultados
respostas/   CSVs finais gerados pelo pipeline
painel/      Aplicação Streamlit e captura de referência
agente/      Roteamento, ferramentas SQL e integração opcional com Ollama
tests/       Testes determinísticos e integração opcional
docs/        Auditoria, qualidade, fluxo e validação
```

## Instalação

No PowerShell, a partir da raiz do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Em Linux ou macOS, substitua `.venv\Scripts\python.exe` por `.venv/bin/python`.

## Gerar os resultados

```powershell
.venv\Scripts\python.exe -m scripts.gerar_resultados
```

O comando executa as consultas e atualiza somente os três CSVs em `respostas/`:

- `p1_score_colaborador.csv`
- `p2_score_area.csv`
- `p3_gestores.csv`

As consultas autônomas estão em `sql/p1_score_colaborador.sql`, `sql/p2_score_area.sql` e `sql/p3_gestores.sql`. Todas podem ser executadas diretamente no SQLite. `sql/base_calculo.sql` concentra as CTEs comuns e é a fonte usada para gerar as consultas completas.

## Dashboard

```powershell
.venv\Scripts\python.exe -m streamlit run painel/app.py
```

O painel mostra cobertura, média geral, comparação entre diretorias, distribuição individual e scores de área. Ele consulta o banco com a mesma base SQL dos CSVs.

## Agente

O modo padrão usa roteamento determinístico para verificar as consultas sem depender de modelo local:

```powershell
.venv\Scripts\python.exe -m agente.agent "Qual o score da Gerência de Marketing?"
```

Para usar Ollama, instale um modelo local e execute:

```powershell
ollama pull qwen3:4b
.venv\Scripts\python.exe -m agente.agent --modo ollama "Qual diretoria teve o melhor resultado consolidado?"
```

Veja detalhes das ferramentas, limites e perguntas cobertas em [agente/README.md](agente/README.md).

## Testes e validação

```powershell
.venv\Scripts\python.exe -m pip install -r tests/requirements.txt
.venv\Scripts\python.exe -m pytest -q
```

Os testes determinísticos não exigem Ollama. A integração com o modelo é opcional:

```powershell
.venv\Scripts\python.exe -m pytest --ollama -m ollama -q
```

As verificações de qualidade e decisões de cálculo estão em [docs/qualidade.md](docs/qualidade.md), [docs/auditoria_regras.md](docs/auditoria_regras.md) e [docs/validacao.md](docs/validacao.md).

## Decisões e limitações

- Os resultados são reproduzíveis a partir do banco SQLite incluído.
- O banco é tratado como somente leitura; o pipeline escreve apenas os CSVs finais.
- O modelo local é opcional e pode variar conforme o modelo e a infraestrutura disponíveis.
- Não há integração produtiva, autenticação ou memória conversacional.
- Este é um projeto de demonstração técnica; não representa experiência profissional nem um sistema de produção.

## Origem e uso responsável

Esta cópia privada preserva, para fins de transparência, o material de referência e a documentação original em [docs/README_entrega_original.md](docs/README_entrega_original.md). O conjunto contém dados de pessoas e material fornecido para uma avaliação técnica. Não o torne público, não redistribua os dados e não use o conteúdo como base de produção sem autorização explícita dos detentores dos dados e do material.

O apoio de IA na implementação e documentação, bem como as limitações da solução, estão descritos no README original preservado e na documentação técnica.
