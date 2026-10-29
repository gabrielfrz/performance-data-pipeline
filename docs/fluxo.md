# Como acompanhar o código

## Caminho dos dados

```text
dados/case_metas.db (somente leitura)
  └─ sql/base_calculo.sql
       ├─ tratamento de lançamentos e referências
       ├─ atingimento e nota por meta
       ├─ elegibilidade e score por pessoa
       └─ agregações de áreas e gestores
            ├─ sql/p1, p2 e p3 → scripts/gerar_resultados.py → respostas/*.csv
            ├─ scripts/dados.py:carregar_painel → painel/app.py
            └─ agente/tools.py → agente/apresentacao.py → resposta
```

O tratamento ocorre durante a consulta. O banco original não é atualizado e não existe uma segunda base tratada persistida.
Os CSVs são entregáveis exportados; não são a fonte do painel ou do agente. Todos compartilham o SQL central.

## Onde cada regra está

As CTEs abaixo estão em `sql/base_calculo.sql`, na ordem de leitura.

| Etapa | CTEs | Regra e efeito |
|---|---|---|
| Ciclo | `metas_ciclo` | R1: restringe a 2025 |
| Último lançamento | `lancamentos_ordenados`, `ultimos_lancamentos` | R2: ordena por data e ID dentro de meta/mês |
| Meses aplicáveis | `meses_validos` | R3: exclui nulos e não aplicáveis depois da deduplicação |
| Origem da meta | `caminho_referencia`, `fontes` | R7: encontra a individual de origem e evita circularidade |
| Acumulação | `acumulados`, `atingimentos` | R4/R5: razão dos totais ou média das razões, conforme polaridade |
| Nota | `notas_fonte` | R6/R8: aplica limites 80% e 120%; ausência permanece nula |
| Meta do colaborador | `notas_meta` | R7/R9: associa a nota da fonte ao peso próprio, inclusive negativo; registra status e entrada no score |
| População | `elegiveis` | R10: aplica admissão e desligamento |
| Score individual | `scores` | R9: ponderação de todas as metas com nota; soma dos pesos zero resulta em nulo |
| Hierarquia | `descendentes`, `areas` | R11: média simples por pessoa, direta ou incluindo subáreas |
| Gestores | `times_gestores`, `ranking_gestores` | P3: gestor ativo, ao menos três elegíveis e ordenação top/bottom |

As políticas de peso negativo, divisão por zero, empates e ausência de score estão no README e em `docs/auditoria_regras.md`.
`atingimento` é uma razão (0,8 = 80%); `nota` e `score` são pontos. A nota tem teto 120; um score ponderado com pesos negativos não recebe teto adicional. Só a seleção final dos SQLs P1/P2/P3 arredonda para duas casas.

## Responsabilidade dos arquivos Python

| Arquivo | Responsabilidade |
|---|---|
| `scripts/dados.py` | Resolve caminhos, abre SQLite em leitura, anexa CTEs às consultas fixas; prepara DataFrames para o painel |
| `scripts/gerar_sql.py` | Junta a base SQL com as três seleções finais; `gerar(check=True)` só confere sincronismo |
| `scripts/gerar_resultados.py` | Confere sincronismo, executa os SQLs e exporta CSVs no formato exigido |
| `painel/app.py` | Exibe métricas e gráficos dos resultados SQL; formata números sem recalcular scores |
| `agente/agent.py` | Recebe a pergunta, coordena seleção, execução e resposta; oferece CLI e demonstração |
| `agente/roteamento.py` | Roteador sem LLM e conferência de entidades/limites presentes na pergunta |
| `agente/contratos.py` | Nomes de ferramentas, campos permitidos, validação e normalização de nomes |
| `agente/llm.py` | Configura e chama Ollama; converte falhas HTTP/protocolo em erros da aplicação |
| `agente/tools.py` | Resolve entidades, executa consultas SQL fixas parametrizadas e registra evidências |
| `agente/apresentacao.py` | Constrói texto a partir dos resultados consultados |

Os caminhos ficam em `scripts/dados.py`; não há configuração de infraestrutura separada.
Pandas é importado apenas quando o painel carrega DataFrames, ou pela exportação/inspeção. O agente e o cálculo SQL podem funcionar com a biblioteca padrão do Python.

## Por que algumas separações e classes foram mantidas

- `Ferramentas` mantém a conexão e as evidências de uma resposta. Uma classe evita passar esses dois objetos por todos os métodos; não há hierarquia de classes.
- `ClienteOllama` mantém URL, modelo e timeout e permite injetar um cliente de teste. `ErroLLM` carrega o código de falha; `SemRedirecionamento` adapta a biblioteca HTTP padrão para impedir redirecionamentos.
- `contratos.py` é usado tanto pelo cliente quanto pelas ferramentas. Centralizá-lo impede que os dois aceitem argumentos diferentes.
- A apresentação e o transporte HTTP permanecem separados das consultas. Cada arquivo pode ser lido sem misturar SQL com protocolo e texto de resposta.
- Os SQLs autônomos têm repetição gerada, não três implementações manuais. Uma alteração no cálculo deve ser feita na base e seguida de `python -m scripts.gerar_sql`.
- O cálculo em Decimal está apenas em `tests/validar_independente.py`. É uma comparação independente para detectar erros de implementação, não uma segunda regra usada pelo produto.

## Auditoria entregue

Os achados de qualidade, as decisões de R1–R11, os cenários de fronteira e os impactos numéricos estão documentados em `qualidade.md` e `auditoria_regras.md`. A cópia de entrega contém a documentação final, sem logs e relatórios intermediários.
