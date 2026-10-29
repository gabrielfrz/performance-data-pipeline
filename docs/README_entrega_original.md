# Case Mereo — Grupo Aurora, ciclo 2025

Cálculo de metas em SQL, auditoria da base, painel executivo e agente com ferramentas de consulta.
A entrega contém 72 colaboradores elegíveis, 11 áreas e o ranking de gestores. O score médio é 95,67.

## Executar

Ambiente validado: Python 3.13.7. SQLite faz parte do Python; pandas exporta os CSVs, e Streamlit/Plotly compõem o painel.
Na pasta deste README, execute no PowerShell:

```powershell
python --version
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m scripts.gerar_resultados
.venv\Scripts\python.exe -m streamlit run painel/app.py
```

Abra o endereço local mostrado no terminal. Ctrl+C encerra o painel. Em Linux/macOS, substitua `.venv\Scripts\python.exe` por `.venv/bin/python`.
Não é necessário executar testes, auditoria ou Ollama para gerar os CSVs e abrir o painel.
Se a criação do ambiente falhar, veja [diagnóstico do Python](docs/execucao.md).

## Onde encontrar

```text
dados/                  Banco original SQLite, somente leitura
sql/                    Cálculo central e três consultas autônomas
respostas/              Os três CSVs exigidos
painel/                 Aplicação Streamlit e print
agente/                 Agente, ferramentas, instruções e cinco respostas
scripts/                Leitura, exportação e auditoria
tests/                  Testes determinísticos e integração opcional
docs/                   Fluxo do código, auditoria detalhada e validação
```

O fluxo é **banco → CTEs de tratamento e cálculo → resultados SQL → CSVs**.
Painel e agente consultam esses mesmos resultados SQL diretamente; não leem os CSVs nem recalculam as regras em Python.
O [mapa do código](docs/fluxo.md) identifica cada etapa e regra.

Os SQLs `p1_score_colaborador.sql`, `p2_score_area.sql` e `p3_gestores.sql` executam diretamente no banco, sem views ou preparação.
São gerados a partir de `sql/base_calculo.sql`; a repetição permite avaliá-los isoladamente.

## Agente e testes

O agente usa Ollama local no modo LLM. Com o serviço ativo e o modelo instalado:

```powershell
ollama pull qwen3:4b
.venv\Scripts\python.exe -m agente.agent --modo ollama "Qual o score da Gerência de Marketing?"
```

Sem `--modo ollama`, usa um roteador determinístico limitado, útil para conferir a aplicação sem modelo.
Veja [instruções do agente](agente/README.md) e [as cinco respostas entregues](agente/respostas.md).

Os testes têm dependências próprias e não são necessários à execução:

```powershell
.venv\Scripts\python.exe -m pip install -r tests/requirements.txt
.venv\Scripts\python.exe -m pytest -q
```

Esse comando executa apenas testes determinísticos. A integração real é opcional:
`python -m pytest --ollama -m ollama -q`. Use o Python do ambiente virtual.
Detalhes de isolamento e saídas: [tests/README.md](tests/README.md).

## Decisões de cálculo

R2 seleciona o último lançamento antes de R3 retirar meses não aplicáveis ou incompletos; uma versão antiga válida não é recuperada. Em Soma, usa-se a razão dos totais; em Média, a média das razões. A polaridade determina numerador e denominador. Compartilhadas usam a fonte referenciada, com o próprio peso. Metas sem nota não ponderam o score. O consolidado é a média de pessoas da área e descendentes, não uma média de médias. Não há arredondamento intermediário.

| Ambiguidade | Política e efeito quantificado |
|---|---|
| Peso negativo | R9 considera toda meta com nota, usando o peso original. A meta 5286 entra com −5; Quésia Nogueira tem score **46,61**. O peso continua registrado como anomalia de cadastro. Soma dos pesos zero gera score nulo; soma negativa é usada literalmente, sem aplicar teto ao score. |
| Denominador zero | A meta 5094 fica sem nota, sem atribuir zero ou teto arbitrário. Lucas Teixeira: **100,84**, contra **105,63** atribuindo teto 120 à meta. Em Média, qualquer razão indefinida deixa a meta sem nota. |
| Ausência de score | Campo vazio no CSV; excluído da média, preservado na contagem de elegíveis. Não há ocorrência nesta base. |
| Empates | Maior `id_lancamento` em datas iguais; menor ID nas posições de P3. A melhor diretoria retorna todos os empates. |
| Datas e gestores | Gestor desligado em 31/12 é considerado inativo nessa data. Não se reconstrói histórico de chefia nem se rateiam meses por vínculo, pois o enunciado não pede esses ajustes. |

Os cenários alternativos e seus impactos estão descritos em [docs/auditoria_regras.md](docs/auditoria_regras.md). A auditoria confirmou datas ISO, hierarquias sem ciclos e três raízes que são diretorias. Os CSVs usam vírgula entre colunas, ponto decimal, UTF-8, duas casas e nenhum índice. A conferência independente em Python/Decimal está em `tests/validar_independente.py`.

## Qualidade dos dados

Contagens da fonte inteira, salvo indicação de 2025. Achados sobrepostos não devem ser somados.

| Problema | Registros afetados | Tratamento |
|---|---|---|
| Duplicação meta/mês | 90 linhas em 45 pares; em 2025, 66 linhas em 33 pares | Retém o lançamento mais recente por R2, antes de aplicar R3. |
| Realizado ausente em mês aplicável | 43 linhas, 17 metas e 16 pessoas; após deduplicar 2025, 38 linhas em 14 metas | Exclui o mês incompleto; solicitar preenchimento na origem. |
| Previsto zero | 12 linhas da meta 5094, uma pessoa | Meta sem nota; decisão e impacto na seção anterior. |
| Peso negativo | Uma meta, 5286, peso −5 | Mantém o peso original na ponderação por R9 e reporta a anomalia; não altera a fonte. |
| Pesos não somam 100 | Sete colaboradores em 2025 | Divide pela soma dos pesos das metas com nota, como R9; não ajusta o cadastro. |
| Lançamentos em compartilhadas | 60 linhas em cinco metas de cinco pessoas | Ignora lançamentos próprios e usa a referência por R7. |
| Individuais sem lançamentos | Quatro metas: 5014, 5063, 5146 e 5188 | Ficam sem nota por R8; uma pertence a pessoa inelegível. |
| Chefia desatualizada | Oito pessoas ativas ligadas ao gestor 118, desligado em 16/05/2025 | Mantém o vínculo informado; gestor fora de P3, pessoas seguem R10. |

**Ausências previstas:** 138 linhas com `nao_se_aplica=1` têm previsto/realizado nulos; não são falha de preenchimento. Há 181 realizados nulos no total (138 não aplicáveis e 43 aplicáveis). Após deduplicar 2025, R3 exclui 146 meses: 108 não aplicáveis e 38 sem realizado. Campos de polaridade/acumulação nulos nas 78 compartilhadas são esperados.

Sem ocorrência de referências ausentes/circulares/fora do ciclo, ciclos organizacionais, autogestão, nomes repetidos, datas/domínios inválidos, valores mensais negativos ou elegível sem score. Esses limites continuam cobertos por testes sintéticos. IDs, contagens e tratamento estão em [docs/qualidade.md](docs/qualidade.md).


Há ainda 305 lançamentos posteriores ao fim do respectivo ciclo; são mantidos porque o enunciado não fixa corte de carga. CSV, Excel e SQLite fornecidos foram comparados célula a célula e são equivalentes.

## Painel

[Print entregue](painel/painel.png) e código em `painel/app.py`.
A página mostra cobertura dos scores, média geral, comparação das diretorias, distribuição individual e scores direto/consolidado das áreas.
A escolha permite observar dispersão e hierarquia além da média. A referência visual de 100 representa o score de atingimento integral.

## Perguntas abertas

### 1. Integração diária de colaboradores via API

Assumo que o Aurora envia os dados para uma API nossa, em lotes diários.  
Usaria uma API Python com autenticação, contrato de campos e identificação única do lote.  
Validaria o formato e salvaria os dados brutos com origem, data e ID da execução antes de confirmar o recebimento.  
Processaria os lotes de forma assíncrona, com retentativas e registro dos erros de validação.  
Validaria chaves, datas e referências e carregaria staging no BigQuery.  
Aplicaria `MERGE` por ID estável e versão/data de atualização, evitando duplicar reenvios.  
Preservaria histórico de área, gestor e desligamento quando necessário.  
Monitoraria volume, atraso e falhas, com reprocessamento a partir dos dados brutos.  
Se o Aurora disponibilizasse uma API para consulta, a entrada seria uma extração agendada com paginação e controle incremental.

### 2. Como detectar respostas erradas do agente

Eu registraria pergunta, ferramenta, parâmetros, resultado, resposta e versão das regras, com retenção adequada.  
Manteria perguntas conhecidas e respostas esperadas obtidas de consultas SQL de referência.  
Rodaria esses testes a cada mudança, medindo acerto da ferramenta, valores corretos, falhas e latência.  
Criaria alertas para aumento de divergências e erros, separando área inexistente de falha técnica.  
Revisaria amostras e feedback dos usuários para encontrar ambiguidades e lacunas de cobertura.  
Cada erro reproduzível viraria teste; versões dos dados, regras e modelo ajudariam a explicar mudanças.

### 3. Divergência entre painel e planilha de RH

Eu começaria pela origem, atualização e regra de cálculo de cada resultado.  
Confirmaria o mesmo ciclo, data de referência, filtros e elegibilidade.  
Verificaria se ambos usam score direto ou consolidado e as mesmas pessoas.  
Reconciliaria colaborador e meta, conferindo compartilhamento, peso, polaridade e acumulação.  
No nível mensal, compararia duplicatas, última versão, meses não aplicáveis e valores ausentes.  
Conferiria metas sem nota no denominador e deixaria o arredondamento para o final.  
Entregaria ao RH as diferenças e suas causas, corrigindo a fonte ou a regra responsável.  
Não ajustaria números manualmente para fazer o painel coincidir com a planilha.

## Uso de IA e limitações

O Codex foi usado na inspeção, implementação, testes, documentação e reorganização. O código foi produzido com esse apoio.
As regras, decisões e evidências ficam disponíveis para revisão; não há atribuição de experiências pessoais ao autor.

O escopo é a base fornecida e o ciclo 2025. Não há integração em produção, autenticação ou memória conversacional.
A auditoria final corrigiu R9 para incluir pesos negativos e manteve a ausência de nota em divisões indefinidas. As demais regras e o banco original foram preservados. A [matriz R1–R11 e os impactos completos](docs/auditoria_regras.md) registram a justificativa e as verificações.
A concordância entre SQL, CSV e testes não garante concordância com um gabarito que adote outras políticas nessas ambiguidades.
O modelo exige instalação separada e pode demorar minutos por pergunta em CPU. Os testes de linguagem cobrem apenas os cenários registrados.

Resultados das execuções, mudanças e pendências: [docs/validacao.md](docs/validacao.md).
