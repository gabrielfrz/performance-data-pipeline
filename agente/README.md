# Agente de consulta

## Executar

Na raiz do projeto, com Ollama instalado:

```powershell
ollama list
ollama pull qwen3:4b
python -m agente.agent --modo ollama "Qual o score da Gerência de Marketing?"
python -m agente.agent --modo ollama --json "Qual o score da área Vendas Oeste?"
python -m agente.agent --modo ollama --demo
```

Use o Python do ambiente virtual descrito no README. `ollama pull` só é necessário quando o modelo não está disponível.
Se o serviço não estiver ativo, execute `ollama serve` em outro terminal.
A demonstração grava cada execução em uma pasta nova dentro de `work/execucoes/`, cujo caminho aparece no terminal.
Ela não altera [respostas.md](respostas.md), que contém as cinco respostas e a avaliação entregues.

Sem modelo, execute `python -m agente.agent --demo`. Esse modo usa expressões regulares, não IA, e reconhece apenas os padrões definidos em `roteamento.py`.
`--fallback` permite usar esse roteador se o Ollama estiver indisponível. Não há fallback para uma resposta malformada do modelo.

## Fluxo de uma pergunta

1. `agent.responder` valida a pergunta e aplica restrições de escopo.
2. O cliente Ollama recebe o prompt de `llm.py` e os schemas de `contratos.py`; devolve uma ferramenta e seus argumentos.
3. A aplicação verifica contrato, entidade e limite mencionados na pergunta.
4. `Ferramentas.executar` permite apenas consultas previamente definidas. Os valores usam parâmetros SQLite.
5. `apresentacao.apresentar` monta a resposta com os resultados do SQL. O texto livre do LLM não é apresentado como resultado.

| Ferramenta | Resultado |
|---|---|
| `consultar_score_area` | Score direto e consolidado |
| `consultar_score_colaborador` | Score de pessoa elegível |
| `listar_colaboradores_por_gestor` | Time direto abaixo do limite de score |
| `consultar_melhor_diretoria` | Maior consolidado, incluindo empates |
| `consultar_metas_colaborador` | Metas e filtro opcional de atingimento |
| `comparar_areas` | Dois scores de área e suas diferenças |

Há dois controles sem SQL: `solicitar_esclarecimento` e `informar_fora_escopo`.
Ausência de entidade não vira zero; homônimos pedem `#ID`. O banco é aberto somente para leitura.

## Configuração e limites

| Variável | Padrão |
|---|---|
| `OLLAMA_MODEL` | `qwen3:4b` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` (apenas HTTP de loopback) |
| `OLLAMA_TIMEOUT` | `300` segundos; intervalo maior que zero até 300 |

O cliente preserva a configuração anterior: CPU, seis threads, temperatura zero, contexto 4096, até 2048 tokens e `think=true`.
O modelo não faz parte do ZIP. A versão instalada é identificada por digest nos registros de validação, pois uma tag pode mudar.
Não há memória conversacional, explicação causal ou previsão. Conferir a presença dos argumentos na pergunta não garante que o modelo interpretou corretamente seu sentido.

As cinco respostas foram reexecutadas após a correção da R9 e estão em `respostas.md`; as verificações atuais estão em `../docs/validacao.md`.
Os testes HTTP simulados verificam protocolo. Somente `pytest --ollama -m ollama` executa inferências reais.
