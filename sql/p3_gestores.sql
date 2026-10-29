-- Fonte única de R1–R11. scripts/gerar_sql.py gera os três arquivos autônomos.
-- Sem arredondamento intermediário. Datas ISO e ciclo verificados no diagnóstico.
WITH RECURSIVE
metas_ciclo AS (
    SELECT * FROM meta WHERE id_ciclo = 2025 -- R1
),
lancamentos_ordenados AS (
    SELECT v.*, ROW_NUMBER() OVER (
        PARTITION BY v.id_meta, v.mes
        ORDER BY v.data_lancamento DESC, v.id_lancamento DESC
    ) AS ordem
    FROM meta_valor_mensal v JOIN metas_ciclo m USING (id_meta)
),
ultimos_lancamentos AS (
    SELECT * FROM lancamentos_ordenados WHERE ordem = 1 -- R2 antes de R3
),
meses_validos AS (
    SELECT * FROM ultimos_lancamentos
    WHERE nao_se_aplica = 0 AND previsto IS NOT NULL AND realizado IS NOT NULL
),
-- R7: segue referências do mesmo ciclo; o caminho impede recursão circular.
caminho_referencia(id_meta, id_atual, caminho) AS (
    SELECT id_meta, id_meta, '/' || id_meta || '/' FROM metas_ciclo
    UNION ALL
    SELECT c.id_meta, r.id_meta, c.caminho || r.id_meta || '/'
    FROM caminho_referencia c
    JOIN metas_ciclo m ON m.id_meta = c.id_atual
    JOIN metas_ciclo r ON r.id_meta = m.id_meta_referencia
    WHERE m.tipo_meta = 'Compartilhada'
      AND instr(c.caminho, '/' || r.id_meta || '/') = 0
),
fontes AS (
    SELECT c.id_meta, m.id_meta AS id_meta_fonte
    FROM caminho_referencia c JOIN metas_ciclo m ON m.id_meta = c.id_atual
    WHERE m.tipo_meta = 'Individual'
),
acumulados AS (
    SELECT m.id_meta, m.polaridade, m.tipo_acumulacao,
           COUNT(v.id_lancamento) AS meses_validos,
           SUM(v.previsto) AS previsto_total, SUM(v.realizado) AS realizado_total,
           SUM(CASE WHEN (m.polaridade = 'Melhor para cima' AND v.previsto = 0)
                         OR (m.polaridade = 'Melhor para baixo' AND v.realizado = 0)
                    THEN 1 ELSE 0 END) AS meses_divisao_zero,
           AVG(CASE
               WHEN m.polaridade = 'Melhor para cima' AND v.previsto <> 0
                   THEN 1.0 * v.realizado / v.previsto
               WHEN m.polaridade = 'Melhor para baixo' AND v.realizado <> 0
                   THEN 1.0 * v.previsto / v.realizado
           END) AS media_atingimentos
    FROM metas_ciclo m LEFT JOIN meses_validos v USING (id_meta)
    WHERE m.tipo_meta = 'Individual'
    GROUP BY m.id_meta, m.polaridade, m.tipo_acumulacao
),
atingimentos AS (
    SELECT a.*,
        CASE
            WHEN meses_validos = 0 THEN NULL -- R8: ausência não é zero
            WHEN polaridade NOT IN ('Melhor para cima', 'Melhor para baixo') THEN NULL
            -- Média com razão indefinida fica sem nota; não se omite mês silenciosamente.
            WHEN tipo_acumulacao = 'Média' AND meses_divisao_zero = 0
                THEN media_atingimentos
            WHEN tipo_acumulacao = 'Soma' AND polaridade = 'Melhor para cima'
                 AND previsto_total <> 0 THEN 1.0 * realizado_total / previsto_total
            WHEN tipo_acumulacao = 'Soma' AND polaridade = 'Melhor para baixo'
                 AND realizado_total <> 0 THEN 1.0 * previsto_total / realizado_total
            ELSE NULL -- denominador zero ou domínio inválido: cálculo indefinido
        END AS atingimento
    FROM acumulados a
),
notas_fonte AS (
    SELECT a.*, CASE WHEN atingimento IS NULL THEN NULL
                    WHEN atingimento < 0.8 THEN 0.0
                    WHEN atingimento > 1.2 THEN 120.0
                    ELSE atingimento * 100.0 END AS nota
    FROM atingimentos a -- R4, R5 e R6
),
notas_meta AS (
    SELECT m.id_meta, m.id_colaborador, m.nome_meta, m.tipo_meta, m.peso,
           f.id_meta_fonte, n.polaridade, n.tipo_acumulacao, n.meses_validos,
           n.previsto_total, n.realizado_total, n.meses_divisao_zero,
           n.atingimento, n.nota,
           -- R9 filtra pela nota, não pelo sinal do peso. Anomalia não altera a fórmula.
           CASE WHEN n.nota IS NOT NULL THEN 1 ELSE 0 END AS entra_score,
           CASE WHEN f.id_meta_fonte IS NULL THEN 'referencia_invalida'
                WHEN n.meses_validos = 0 THEN 'sem_meses_validos'
                WHEN n.nota IS NULL THEN 'calculo_indefinido'
                WHEN m.peso < 0 THEN 'peso_negativo'
                ELSE 'ok' END AS status
    FROM metas_ciclo m LEFT JOIN fontes f USING (id_meta)
    LEFT JOIN notas_fonte n ON n.id_meta = f.id_meta_fonte
),
elegiveis AS (
    SELECT * FROM colaborador
    WHERE data_admissao <= '2025-09-30'
      AND (data_desligamento IS NULL OR data_desligamento >= '2025-07-01') -- R10
),
scores AS (
    SELECT c.id_colaborador, c.nome, c.id_area, c.id_gestor,
           SUM(CASE WHEN n.entra_score = 1 THEN n.nota * n.peso END)
           -- Soma dos pesos zero: razão indefinida. Soma negativa permanece na fórmula.
           / NULLIF(SUM(CASE WHEN n.entra_score = 1 THEN 1.0 * n.peso END), 0) AS score
    FROM elegiveis c LEFT JOIN notas_meta n USING (id_colaborador)
    GROUP BY c.id_colaborador, c.nome, c.id_area, c.id_gestor -- R9
),
descendentes(id_area, id_descendente) AS (
    SELECT id_area, id_area FROM area
    UNION -- conjunto evita dupla contagem; ciclos são reportados pela auditoria
    SELECT d.id_area, a.id_area FROM descendentes d
    JOIN area a ON a.id_area_pai = d.id_descendente
),
areas AS (
    SELECT a.id_area, a.nome, a.id_area_pai,
           (SELECT AVG(s.score) FROM scores s WHERE s.id_area = a.id_area) AS score_direto,
           (SELECT AVG(s.score) FROM descendentes d JOIN scores s
            ON s.id_area = d.id_descendente WHERE d.id_area = a.id_area) AS score_consolidado
    FROM area a -- R11: média de pessoas, não média de médias de áreas
),
times_gestores AS (
    SELECT g.id_colaborador AS id_gestor, g.nome, COUNT(*) AS subordinados_elegiveis,
           COUNT(s.score) AS subordinados_pontuados, AVG(s.score) AS score_medio_time
    FROM colaborador g JOIN scores s ON s.id_gestor = g.id_colaborador
    WHERE g.data_admissao <= '2025-12-31'
      AND (g.data_desligamento IS NULL OR g.data_desligamento > '2025-12-31')
    GROUP BY g.id_colaborador, g.nome
    HAVING COUNT(*) >= 3 AND COUNT(s.score) > 0
),
ranking_gestores AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY score_medio_time DESC, id_gestor) AS pos_top,
              ROW_NUMBER() OVER (ORDER BY score_medio_time ASC, id_gestor) AS pos_bottom
    FROM times_gestores
)

SELECT grupo, posicao, id_gestor, ROUND(score_medio_time, 2) AS score_medio_time
FROM (
    SELECT 'top' AS grupo, pos_top AS posicao, id_gestor, score_medio_time
    FROM ranking_gestores WHERE pos_top <= 3
    UNION ALL
    SELECT 'bottom', pos_bottom, id_gestor, score_medio_time
    FROM ranking_gestores WHERE pos_bottom <= 3
)
ORDER BY CASE grupo WHEN 'top' THEN 0 ELSE 1 END, posicao;
