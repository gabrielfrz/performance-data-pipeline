# Auditoria da fonte

Escopo bruto: ambos os ciclos, salvo indicação de 2025. As contagens de verificações sobrepostas não devem ser somadas. `CTE:` indica consulta após `sql/base_calculo.sql`.

## duplicados — problema

Lançamentos em pares meta/mês repetidos, ambos os ciclos.

**Contagens:** registros: 90, id_meta_unicos: 43, id_colaborador_unicos: 32, pares_meta_mes: 45.

R2 mantém o mais recente; os demais não contribuem. Contar linhas, pares e metas separadamente.

```sql
SELECT v.*,m.id_colaborador,m.id_ciclo FROM meta_valor_mensal v JOIN meta m USING(id_meta)
 WHERE (v.id_meta,v.mes) IN (SELECT id_meta,mes FROM meta_valor_mensal GROUP BY id_meta,mes HAVING COUNT(*)>1)
```

## duplicados_2025 — problema

Lançamentos em pares repetidos do ciclo 2025.

**Contagens:** registros: 66, id_meta_unicos: 31, id_colaborador_unicos: 26, pares_meta_mes: 33.

Subconjunto do item anterior, não somar as contagens. Evita inflar acumulados.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE m.id_ciclo=2025
 AND (v.id_meta,v.mes) IN (SELECT id_meta,mes FROM meta_valor_mensal GROUP BY id_meta,mes HAVING COUNT(*)>1)
```

## previsto_nulo — contexto

Previsto ausente no dado bruto, ambos os ciclos.

**Contagens:** registros: 138, id_meta_unicos: 115, id_colaborador_unicos: 63, pares_meta_mes: 138.

R3 exclui o mês somente depois da deduplicação; pode reduzir a cobertura.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE previsto IS NULL
```

## realizado_nulo — contexto

Realizado ausente no dado bruto, ambos os ciclos.

**Contagens:** registros: 181, id_meta_unicos: 123, id_colaborador_unicos: 64, pares_meta_mes: 181.

R3; pode sobrepor previsto ausente. Não somar as duas contagens.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE realizado IS NULL
```

## qualquer_nulo — contexto

Previsto ou realizado ausente no dado bruto.

**Contagens:** registros: 181, id_meta_unicos: 123, id_colaborador_unicos: 64, pares_meta_mes: 181.

União dos dois itens anteriores, com sobreposição eliminada.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE previsto IS NULL OR realizado IS NULL
```

## realizado_ausente_aplicavel — problema

Realizado ausente apesar de nao_se_aplica=0, ambos os ciclos.

**Contagens:** registros: 43, id_meta_unicos: 17, id_colaborador_unicos: 16, pares_meta_mes: 43.

Ausência de preenchimento em mês aplicável. R3 exclui após R2; solicitar preenchimento à origem. Os outros 138 nulos brutos acompanham o marcador não se aplica.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE realizado IS NULL AND nao_se_aplica=0
```

## realizado_ausente_2025 — problema

Últimos lançamentos de 2025 aplicáveis, mas sem realizado.

**Contagens:** registros: 38, id_meta_unicos: 14, pares_meta_mes: 38.

Subconjunto efetivo em 2025: excluído por R3, reduz cobertura sem gerar nota zero.

```sql
CTE: SELECT * FROM ultimos_lancamentos WHERE realizado IS NULL AND nao_se_aplica=0
```

## nsa — contexto

Marcador não se aplica no dado bruto.

**Contagens:** registros: 138, id_meta_unicos: 115, id_colaborador_unicos: 63, pares_meta_mes: 138.

Exclusão prevista em R3; não é automaticamente erro de qualidade.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE nao_se_aplica=1
```

## ultimos_invalidos — contexto

Últimos lançamentos de 2025 desconsiderados por R3.

**Contagens:** registros: 146, id_meta_unicos: 95, pares_meta_mes: 146.

A seleção do último lançamento é definitiva; não recuperar uma versão antiga válida.

```sql
CTE: SELECT * FROM ultimos_lancamentos WHERE nao_se_aplica<>0 OR previsto IS NULL OR realizado IS NULL
```

## recente_invalido_anterior_valido — problema

Últimos lançamentos inválidos com versão antiga válida em 2025.

**Contagens:** registros: 0.

R2 antes de R3; evita ressuscitar um mês descartado pela última importação.

```sql
CTE: SELECT u.* FROM ultimos_lancamentos u WHERE (u.nao_se_aplica<>0 OR u.previsto IS NULL OR u.realizado IS NULL)
 AND EXISTS (SELECT 1 FROM lancamentos_ordenados a WHERE a.id_meta=u.id_meta AND a.mes=u.mes
 AND a.ordem>1 AND a.nao_se_aplica=0 AND a.previsto IS NOT NULL AND a.realizado IS NOT NULL)
```

## zero — problema

Lançamentos brutos com previsto ou realizado zero.

**Contagens:** registros: 12, id_meta_unicos: 1, id_colaborador_unicos: 1, pares_meta_mes: 12.

Zero não é nulo. Em Soma usa-se o total; denominador total zero deixa a meta sem nota. Em Média, qualquer razão indefinida deixa a meta sem nota.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE previsto=0 OR realizado=0
```

## peso_nao_positivo — problema

Metas com peso não positivo (alerta de cadastro, sem exclusão automática).

**Contagens:** registros: 1, id_meta_unicos: 1, id_colaborador_unicos: 1.

R9 usa o peso original de toda meta com nota, inclusive negativo. A anomalia permanece reportada; não excluir nem transformar o peso. Soma de pesos zero deixa o score indefinido.

```sql
SELECT * FROM meta WHERE peso<=0
```

## soma_pesos — problema

Colaboradores com soma de pesos diferente de 100 em 2025.

**Contagens:** registros: 7, id_colaborador_unicos: 7.

Anomalia de cadastro, não violação explícita de R9. Aplicar a fórmula às metas com nota, preservando o sinal de cada peso; não forçar total 100 nem ajustar valores.

```sql
SELECT id_colaborador,SUM(peso) AS soma_pesos FROM meta WHERE id_ciclo=2025 GROUP BY id_colaborador HAVING SUM(peso)<>100
```

## compartilhada_proprios — problema

Lançamentos próprios de metas compartilhadas.

**Contagens:** registros: 60, id_meta_unicos: 5, id_colaborador_unicos: 5, pares_meta_mes: 60.

R7 ignora todos estes lançamentos, usando a meta referenciada. Evita resultados conflitantes.

```sql
SELECT v.*,m.id_colaborador FROM meta_valor_mensal v JOIN meta m USING(id_meta) WHERE m.tipo_meta='Compartilhada'
```

## sem_lancamento — problema

Metas individuais sem qualquer lançamento.

**Contagens:** registros: 4, id_meta_unicos: 4, id_colaborador_unicos: 4.

Sem nota, fora do denominador (R8); não atribuir zero.

```sql
SELECT m.* FROM meta m WHERE tipo_meta='Individual' AND NOT EXISTS (SELECT 1 FROM meta_valor_mensal v WHERE v.id_meta=m.id_meta)
```

## sem_meses — problema

Metas de 2025 cuja fonte não tem meses válidos.

**Contagens:** registros: 4, id_meta_unicos: 4, id_colaborador_unicos: 4.

Sem nota (R8), inclui metas que tenham lançamentos mas nenhum mês válido.

```sql
CTE: SELECT * FROM notas_meta WHERE status='sem_meses_validos'
```

## indefinidas — problema

Metas de 2025 com cálculo indefinido.

**Contagens:** registros: 1, id_meta_unicos: 1, id_colaborador_unicos: 1.

Sem nota; divisão por zero explicitamente documentada, sem teto arbitrário.

```sql
CTE: SELECT * FROM notas_meta WHERE status='calculo_indefinido'
```

## sem_score — problema

Colaboradores elegíveis sem score.

**Contagens:** registros: 0.

Preservar no P1 com campo vazio; excluir apenas da média, não da contagem de elegíveis.

```sql
CTE: SELECT * FROM scores WHERE score IS NULL
```

## gestor_desligado — problema

Colaboradores ainda ativos em 31/12 vinculados a gestor já desligado.

**Contagens:** registros: 8, id_colaborador_unicos: 8, id_gestor_unicos: 1.

Manter vínculo informado: não há histórico para reconstruir a chefia. Gestor inativo fica fora de P3; colaboradores elegíveis continuam em P1/P2.

```sql
SELECT c.*,g.nome AS nome_gestor,g.data_desligamento AS desligamento_gestor
 FROM colaborador c JOIN colaborador g ON g.id_colaborador=c.id_gestor
 WHERE (c.data_desligamento IS NULL OR c.data_desligamento>'2025-12-31')
 AND c.data_admissao<='2025-12-31' AND g.data_desligamento<='2025-12-31' 
```

## refs_invalidas — checagem

Referências compartilhadas sem destino individual alcançável no ciclo.

**Contagens:** registros: 0.

Referências ausentes, fora do ciclo e circulares ficam sem nota; nenhuma inferência automática de destino.

```sql
CTE: SELECT * FROM notas_meta WHERE status='referencia_invalida'
```

## dominios — checagem

Domínios inválidos de tipo, polaridade ou acumulação em metas.

**Contagens:** registros: 0.

Campos nulos de compartilhadas são esperados: a configuração vem da referência.

```sql
SELECT * FROM meta WHERE tipo_meta NOT IN ('Individual','Compartilhada')
 OR (tipo_meta='Individual' AND (polaridade IS NULL OR polaridade NOT IN ('Melhor para cima','Melhor para baixo')
 OR tipo_acumulacao IS NULL OR tipo_acumulacao NOT IN ('Soma','Média')))
```

## mes_dominio — checagem

Meses ou marcador fora do domínio.

**Contagens:** registros: 0.

Se surgirem, corrigir a ingestão antes de publicar; não existem na fonte entregue.

```sql
SELECT * FROM meta_valor_mensal WHERE mes NOT BETWEEN 1 AND 12 OR nao_se_aplica NOT IN (0,1)
```

## negativos — checagem

Previsto ou realizado negativo.

**Contagens:** registros: 0.

Não existem; exigir regra de negócio antes de generalizar para métricas com negativos.

```sql
SELECT * FROM meta_valor_mensal WHERE previsto<0 OR realizado<0
```

## empate_lancamento — checagem

Pares com data de lançamento empatada.

**Contagens:** registros: 0.

Desempate determinístico pelo maior id_lancamento; não afeta esta base.

```sql
SELECT id_meta,mes,data_lancamento,COUNT(*) n FROM meta_valor_mensal GROUP BY 1,2,3 HAVING COUNT(*)>1
```

## datas_ordem — checagem

Desligamento anterior à admissão.

**Contagens:** registros: 0.

Sem ocorrência; não alterar datas por suposição.

```sql
SELECT * FROM colaborador WHERE data_desligamento<data_admissao
```

## autogestor — checagem

Colaborador gestor de si mesmo.

**Contagens:** registros: 0.

Sem ocorrência; seria necessário corrigir o cadastro.

```sql
SELECT * FROM colaborador WHERE id_gestor=id_colaborador
```

## nomes_duplicados — checagem

Nomes de colaboradores repetidos.

**Contagens:** registros: 0.

Sem ocorrência; ferramentas ainda tratam ambiguidade e aceitam ID explícito.

```sql
SELECT nome,COUNT(*) n FROM colaborador GROUP BY nome HAVING COUNT(*)>1
```

## fk — checagem

Referências inexistentes em todas as tabelas.

**Contagens:** registros: 0.

Validação explícita, pois a declaração de FK não garante que ela estava habilitada na carga.

```sql
PRAGMA foreign_key_check
```

## lancamentos_apos_ciclo — contexto

Lançamentos datados após o fim do ciclo da meta.

**Contagens:** registros: 305, id_meta_unicos: 299, pares_meta_mes: 299.

Não são excluídos: o enunciado filtra o ciclo da meta, não impõe corte na data de lançamento. Inclui competência dezembro lançada em janeiro.

```sql
SELECT v.*,m.id_ciclo FROM meta_valor_mensal v JOIN meta m USING(id_meta) JOIN ciclo c USING(id_ciclo) WHERE v.data_lancamento>c.data_fim
```

## ciclos_area — checagem

Entidades em ciclos de area.

**Contagens:** registros: 0.

Percorrer cada relação até raiz, referência ausente ou repetição. Não publicar hierarquia cíclica.

```sql
SELECT * FROM area; depois ciclos(rows, 'id_area', 'id_area_pai')
```

## ciclos_colaborador — checagem

Entidades em ciclos de colaborador.

**Contagens:** registros: 0.

Percorrer cada relação até raiz, referência ausente ou repetição. Não publicar hierarquia cíclica.

```sql
SELECT * FROM colaborador; depois ciclos(rows, 'id_colaborador', 'id_gestor')
```

## datas_formato — checagem

Datas fora do formato ISO válido.

**Contagens:** registros: 0.

Comparação textual das queries é válida porque todas as datas foram verificadas.

```sql
SELECT * de colaborador, ciclo e meta_valor_mensal; date.fromisoformat em todos os campos de data não nulos
```
