"""Gera SQL autônomo a partir de uma única definição das regras."""

from scripts.dados import ROOT

FINAIS = {
    "p1_score_colaborador": "SELECT id_colaborador, ROUND(score, 2) AS score FROM scores ORDER BY id_colaborador;",
    "p2_score_area": """SELECT id_area, ROUND(score_direto, 2) AS score_direto,
ROUND(score_consolidado, 2) AS score_consolidado FROM areas ORDER BY id_area;""",
    "p3_gestores": """SELECT grupo, posicao, id_gestor, ROUND(score_medio_time, 2) AS score_medio_time
FROM (
    SELECT 'top' AS grupo, pos_top AS posicao, id_gestor, score_medio_time
    FROM ranking_gestores WHERE pos_top <= 3
    UNION ALL
    SELECT 'bottom', pos_bottom, id_gestor, score_medio_time
    FROM ranking_gestores WHERE pos_bottom <= 3
)
ORDER BY CASE grupo WHEN 'top' THEN 0 ELSE 1 END, posicao;""",
}


def gerar(check=False):
    base = (ROOT / "sql/base_calculo.sql").read_text(encoding="utf-8")
    for nome, final in FINAIS.items():
        path = ROOT / "sql" / f"{nome}.sql"
        texto = base + "\n" + final + "\n"
        if check:
            assert path.read_text(encoding="utf-8") == texto, (
                f"{path.name} desatualizado"
            )
        else:
            path.write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    gerar()
