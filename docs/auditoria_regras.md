# Auditoria final das regras de negócio — Mereo

Auditoria realizada em 29/10/2026 sobre a entrega reorganizada e o ZIP original fornecido pela Mereo. Prioridade: texto do enunciado, matemática e consistência entre regras. O banco não foi modificado.

## Decisões

**R9 corrigida:** toda meta com nota participa com seu peso original, inclusive negativo. A regra não autoriza descartar pesos negativos. A meta 5286 tem nota calculável e a soma dos pesos de Quésia é 90; não há inconsistência matemática que justifique excluí-la. O alerta de qualidade permanece.

**Divisão por zero mantida como indefinida:** nenhuma regra autoriza transformar denominador zero em nota 0, 100 ou 120. A meta 5094 continua sem atingimento e sem nota. Essa é uma decisão necessária em uma lacuna do enunciado, não uma aplicação direta de R8: R8 trata especificamente da ausência de meses válidos, e aqui há 12 meses válidos.

**R10, R11 e P3 mantidas:** não foram encontrados desvios na população, hierarquia, média por pessoa ou ranking. Os oito elegíveis vinculados ao gestor desligado continuam em P1/P2; o gestor não entra em P3. Não há informação para reconstruir ou transferir a chefia.

## Matriz das regras

| Regra | Exigência do enunciado | Implementação | Resultado da auditoria | Impacto |
|---|---|---|---|---|
| R1 | Apenas ciclo 2025 | `metas_ciclo`, filtro `id_ciclo=2025` | Mantida: 316 metas; tabela ciclo confirma ano e datas. Não há corte adicional de data de importação | 60 metas de 2024 fora; 243 lançamentos brutos de 2025 posteriores a 31/12 mantidos |
| R2 | Último lançamento de cada meta/mês | `ROW_NUMBER`, data decrescente e ID no empate | Mantida: 2.901 linhas → 2.868 pares, 33 versões descartadas | Evita duplicação dos acumulados; não há empate de datas na fonte |
| R3 | Aplicável e previsto/realizado preenchidos | Filtro depois da escolha do último | Mantida: exclui 108 não aplicáveis e 38 incompletos; 2.722 meses restantes | Não recupera versão antiga válida; nenhum caso real dessa recuperação foi encontrado, mas há teste sintético |
| R4 | Soma = razão dos totais; Média = média dos atingimentos | `acumulados`, `atingimentos` | Mantida e conferida em Decimal a partir dos CSVs originais | Evita média das notas mensais e média de valores no lugar de média das razões |
| R5 | Melhor para cima: realizado/previsto; para baixo: previsto/realizado | Inversão do numerador/denominador no mês ou total | Mantida; quatro combinações de polaridade/acumulação presentes | Meta 5094 permanece indefinida; nenhum valor mensal negativo na base |
| R6 | <80%: 0; 80–120%: atingimento×100; >120%: 120 | `notas_fonte`, após acumulação | Mantida: fronteiras inclusivas; sem arredondamento prévio | Entre individuais: 18 abaixo de 80%, uma exatamente em 120%, 19 acima de 120% |
| R7 | Compartilhada usa fonte, polaridade e acumulação referenciadas; peso próprio | `caminho_referencia`, `fontes`, `notas_meta` | Mantida: 78 referências válidas, todas diretamente a individuais | 60 lançamentos próprios de cinco compartilhadas são ignorados |
| R8 | Sem mês válido: sem nota e fora do score | Nulo na nota e filtro de nota em R9 | Mantida: quatro individuais sem meses; uma pertence a inelegível | Ausência não vira nota zero; há ainda a exceção matemática de divisão indefinida |
| R9 | Soma(nota×peso)/soma(peso), apenas metas com nota | Removido `peso>0`; `NULLIF` no denominador | Corrigida; preserva sinal, inclusive denominador negativo não nulo | Uma pessoa, duas áreas e um gestor mudam; soma de pesos zero gera score nulo |
| R10 | Admissão até 30/09 e não desligado antes de 01/07 | `<=2025-09-30` e `>=2025-07-01` ou nulo | Mantida: 72 elegíveis de 81; datas consistentes | Três admissões tardias e seis desligamentos precoces; nenhuma mudança de população |
| R11 | Média de scores por pessoa na área, direta ou com descendentes | `descendentes` como conjunto; `AVG` de scores | Mantida; conferência independente sobe a árvore por pessoa | 11 áreas; sem ciclos, dupla contagem ou média de médias |
| P3 | Três melhores/piores, gestor ativo em 31/12, ≥3 subordinados diretos elegíveis | `times_gestores`, `ranking_gestores` | Mantida: nove gestores aptos; desempate por ID | Seis linhas e mesmas posições; muda apenas a média do gestor 171 |

Os 2.722 meses da R3 incluem 60 lançamentos próprios de compartilhadas, depois ignorados por R7. Não são 2.722 contribuições distintas ao score. As contagens de problemas sobrepostos não devem ser somadas.

## R9 — memória de cálculo e denominadores

Quésia Nogueira, ID 174, possui estas quatro metas com nota. Os valores abaixo são exibidos com seis casas; o cálculo usa precisão completa.

| Meta | Nota | Peso | Nota × peso |
|---|---:|---:|---:|
| 5285 — Despesa administrativa, compartilhada | 112,405011 | 20 | 2.248,100226 |
| 5286 — Inadimplência (%) | 94,753544 | −5 | −473,767718 |
| 5287 — Economia em contratos | 0,000000 | 50 | 0,000000 |
| 5288 — Relatórios gerenciais | 96,823204 | 25 | 2.420,580110 |

Novo score: **4.194,912618913915 ÷ 90 = 46,610140210155**. A política anterior removia a meta 5286: **4.668,680336416317 ÷ 95 = 49,144003541224**.

A nota zero da meta 5287 permanece no denominador. Ela não é ausência de nota. O peso da compartilhada 5285 é seu próprio peso 20, não o peso da meta de origem.

As somas de pesos das metas com nota dos 72 elegíveis variam de **70 a 120**. Nenhuma é zero ou negativa na base. Há exatamente um peso negativo, nenhum peso zero ou nulo.

Para cenários de fronteira, a aplicação mantém a fórmula:

- Soma dos pesos zero: score nulo, inclusive quando o numerador também é zero. `NULLIF` explicita a indefinição, sem atribuir zero.
- Soma negativa não nula: divisão normalmente. Excluir essas metas ou o colaborador acrescentaria regra não solicitada.
- Peso zero em meta com nota: entra na seleção R9 e contribui zero ao numerador e denominador. Se todos os pesos forem zero, o score é indefinido.
- Pesos negativos podem produzir scores fora de 0–120. R6 limita a nota da meta, não o score. Nenhum teto adicional foi aplicado. Na base real, os scores estão entre 18,174477 e 117,721503.

O status da meta 5286 passou de `peso_invalido` para `peso_negativo`, indicando uma anomalia sem sugerir exclusão da fórmula.

## R4/R5/R6/R8 — zero, nulos e acumulação

Há 238 metas individuais em 2025: 101 Soma/melhor para cima, 41 Média/melhor para cima, 18 Soma/melhor para baixo e 78 Média/melhor para baixo. Todas foram conferidas, além das 78 compartilhadas.

| Situação | Tratamento adotado |
|---|---|
| Soma | Agrega numerador e denominador dos meses válidos e divide uma vez |
| Média | Calcula cada razão de mês válido e tira a média sem pesos mensais |
| Numerador zero e denominador não zero | Atingimento zero, nota zero, peso participa de R9 |
| Denominador total zero em Soma | Atingimento/nota nulos; não usa infinito nem teto |
| Denominador zero em um mês de Média | A média completa é indefinida; toda a meta fica sem nota. Não omite silenciosamente um mês que R3 considera válido |
| Zero mensal em Soma, total não zero | O mês participa do total; zero mensal não invalida o cálculo agregado |
| Sem mês válido | Ausência de nota por R8 |
| Previsto/realizado negativos | Não existem na fonte. Testes confirmam a razão literal e aplicação de R6, sem transformar negativo em nulo |

A meta 5094 (Lucas Teixeira, ID 125) tem **12 meses válidos**, previsto total **0**, realizado total **1.610**, polaridade melhor para cima e acumulação Soma. Seu peso 25 não participa de R9 porque não há nota calculável. As três outras metas totalizam peso 75 e score **100,835940919489**, exportado **100,84**.

Atribuir 120 à meta seria uma política alternativa, não um resultado da divisão: Lucas iria a **105,626955689617**. Não foi adotada.

Não há previsto/realizado negativo, realizado zero ou outro denominador mensal zero na fonte. Os 12 registros com zero pertencem à meta 5094. As outras quatro metas sem nota são 5014, 5063, 5146 e 5188, sem lançamentos.

R6 é aplicada ao atingimento acumulado, sem arredondar antes dos limites. Há uma meta individual exatamente em 120% e nenhuma exatamente em 80%; testes sintéticos cobrem ambos os extremos. A menor distância real de 80% é aproximadamente 0,000528588 na razão. A conferência Decimal validou também os valores finais arredondados.

## R10 — datas e elegibilidade

“Até 30/09” é inclusivo e “não desligado antes de 01/07” inclui desligamento em 01/07. Assim, as comparações atuais são fiéis ao enunciado. Não é exigido estar ativo em 31/12 para P1/P2, nem ratear metas pelos meses de vínculo.

Foram conferidas as 81 pessoas: 72 elegíveis e nove excluídas. IDs excluídos: **112, 114, 118, 119, 124, 164, 167, 170, 175**. São três admissões após 30/09 e seis desligamentos antes de 01/07, sem sobreposição. Nenhuma data inválida ou desligamento anterior à admissão foi encontrado.

Não existem registros exatamente em 30/09 para admissão ou 01/07 para desligamento; essas fronteiras foram testadas em bancos sintéticos. Flávia Barros (112), admitida em 01/10/2025, fica corretamente fora.

## R11/P3 — pessoas, hierarquia e chefia

As 11 áreas formam uma árvore sem ciclos, com três raízes. O consolidado foi recalculado independentemente, percorrendo os ancestrais da área de cada pessoa. Isso evita repetir a estratégia SQL de descer a árvore e confirma os conjuntos de pessoas, não apenas médias finais.

As diretorias Comercial, Operações e Financeira têm respectivamente **33, 27 e 12 elegíveis** no consolidado. Cada pessoa é contada uma vez por área consolidada. Uma pessoa aparecer no consolidado de sua gerência e de sua diretoria é intencional; não é duplicidade dentro da mesma média.

Score nulo não é zero: fica fora de `AVG`, mas a pessoa continua em P1 e na contagem mínima de elegíveis do time. Não há elegível sem score na base. Para um time sem nenhum score calculável, o ranking não é definido; o gestor não recebe zero nem posição artificial.

P3 usa **subordinados diretos por `id_gestor`**, não descendentes da área nem o score do próprio gestor. O gestor precisa estar ativo no fim de 31/12; desligamento exatamente nessa data foi tratado como inatividade. Não há tal ocorrência real; testes cobrem a fronteira. Admissão do gestor após 30/09 não o exclui automaticamente de P3 se estiver ativo em 31/12: o corte R10 vale para a população do time.

O mínimo de três conta elegíveis, mesmo se algum não tiver score. A ordenação usa a média sem arredondamento; ID crescente resolve empates. Não houve empate na base. Top: **171, 139, 103**. Bottom: **129, 158, 145**. O gestor 171 continua em primeiro lugar após a correção.

O gestor 118, Nicolas Duarte, desligou-se em 16/05/2025. Os oito subordinados ativos/elegíveis são **120, 121, 122, 123, 125, 126, 127 e 128**; permanecem em P1 e nos consolidados da Coordenação Vendas Norte (4), Gerência de Vendas (2) e Diretoria Comercial (1). O gestor 118 é excluído de P3 por inatividade. Não são automaticamente transferidos para o gestor 103: não há histórico ou instrução que autorize essa mudança.

## Impactos numéricos completos

| Entidade / resultado | Antes | Depois |
|---|---:|---:|
| Quésia Nogueira (174), score | 49,14 | **46,61** |
| Diretoria Financeira (10), consolidado | 103,11 | **102,90** |
| Gerência de Controladoria (11), direto | 102,87 | **102,62** |
| Gerência de Controladoria (11), consolidado | 102,87 | **102,62** |
| Sofia Queiroz (171), média do time direto | 101,75 | **101,47** |
| Média geral do painel | 95,71 | **95,67** |

Não mudou o score direto da Diretoria Financeira, que permanece 104,33. Não mudaram as posições de nenhum dos nove gestores aptos, a diretoria líder, as notas das metas ou a população elegível. Todas as demais pessoas, áreas e médias de gestores foram comparadas e permaneceram iguais.

P1 mudou uma de 72 linhas; P2, duas de 11; P3, uma de seis. São cinco campos de score alterados nos CSVs. Os cabeçalhos e a formatação com duas casas foram preservados.

## Arquivos afetados e motivo

| Arquivos | Alteração |
|---|---|
| `sql/base_calculo.sql` | R9 sem filtro de sinal, denominador zero explícito e status de alerta |
| `sql/p1_score_colaborador.sql`, `p2_score_area.sql`, `p3_gestores.sql` | Regenerados a partir da base corrigida |
| `respostas/p1_score_colaborador.csv`, `p2_score_area.csv`, `p3_gestores.csv` | Regenerados e comparados integralmente |
| `tests/validar_independente.py` | Ponderação Decimal literal, tratamento de denominador zero e conferência dos conjuntos de pessoas/gestores |
| `tests/test_regras.py` | Expectativa de R9 corrigida após conferência independente; 26 novos casos de fronteira |
| `tests/test_agente_painel.py` | Média esperada do painel atualizada para 95,67 após validação Decimal |
| `painel/app.py` | Legenda esclarece que 0–120 é intervalo da nota, não garantia para score com pesos negativos |
| `painel/painel.png` | Nova captura real no navegador com valores corrigidos |
| `agente/respostas.md`, `agente/README.md` | Cinco respostas reexecutadas e procedência atualizada; ferramentas/consultas do agente não precisaram mudar |
| `README.md`, `docs/fluxo.md`, `docs/qualidade.md`, `docs/validacao.md`, `docs/auditoria_regras.md` | Decisões, resultados, matriz de regras e validação coerentes com a correção |

Não houve refatoração de arquitetura, mudança no banco ou funcionalidade nova.

## Validação executada

- **150 testes determinísticos aprovados, zero falhas**; 23 testes reais deselecionados nessa execução.
- **Cinco perguntas oficiais aprovadas com Ollama real, sem fallback**. Os outros 18 testes opcionais não foram reexecutados nesta auditoria.
- Implementação independente em Python/Decimal da base SQLite: 72 scores, 11 áreas, nove gestores e ranking.
- Segunda conferência independente, lendo diretamente os CSVs do ZIP original: 316 notas/atingimentos, 72 pessoas, 11 áreas e nove gestores. Hierarquia calculada por ancestrais de cada pessoa. Concordância com o SQL com tolerância de 1e-10 antes do arredondamento.
- Três consultas executadas; linhas, cabeçalhos e todos os valores comparados com os CSVs, antes e depois.
- Dashboard executado por AppTest e aberto no navegador. Média 95,67, 72 elegíveis, 72 pontuados, zero sem score; Diretoria Financeira 102,90. Nova captura incluída.
- Cinco perguntas determinísticas executadas. A resposta da melhor diretoria mudou para 102,90; as outras quatro permaneceram iguais.
- Banco original e cópia da entrega idênticos por SHA-256: `479936c41728296b8bd8ce9767dc7ea2061639b2aa133e02bb8a90e67f2750e5`.

Os testes não foram usados como gabarito: a decisão e os novos valores foram primeiro conferidos por fórmula e pelos CSVs originais; só então as expectativas antigas foram ajustadas.

## Ambiguidades e riscos restantes

1. **Divisão por zero:** o enunciado não define nota. A ausência de nota é matematicamente defensável, mas um gabarito que atribua teto produzirá outro resultado para Lucas e suas áreas.
2. **Peso negativo:** a regra literal favorece a inclusão adotada. Um gabarito que acrescente exclusão por qualidade poderá divergir; essa política não está expressa na R9.
3. **Score nulo:** excluir da média, mantendo a pessoa elegível, evita inventar zero. O enunciado não detalha esse cenário; não ocorre na base.
4. **Empates e desligamento em 31/12:** desempate por ID e inatividade ao fim do dia foram documentados. Não há ocorrências reais afetadas.
5. **Referências encadeadas/circulares:** a proteção já existente permanece, mas a fonte contém apenas referências diretas válidas. Não foi necessário decidir um resultado novo para esses casos hipotéticos.
6. O agente e o painel continuam limitados à base fornecida. Os contratos de consulta de score usam limites de 0 a 120; isso cobre a base real, mas não é uma garantia matemática para futuras bases com pesos negativos. Generalização não foi adicionada ao case.

Essas ressalvas não indicam falha nos cenários executados; delimitam onde o enunciado não determina uma resposta única.
