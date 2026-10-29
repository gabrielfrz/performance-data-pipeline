"""Oráculo em Python/Decimal: reimplementação independente usada só na validação."""

from decimal import ROUND_HALF_UP, Decimal

from scripts.dados import ROOT, conectar, consulta


def validar():
    with conectar() as c:
        tabelas = {
            t: [dict(r) for r in c.execute("SELECT * FROM " + t)]
            for t in ["colaborador", "area", "meta", "meta_valor_mensal"]
        }
        metas = {m["id_meta"]: m for m in tabelas["meta"] if m["id_ciclo"] == 2025}
        ultimos = {}
        for v in tabelas["meta_valor_mensal"]:
            chave = (v["id_meta"], v["mes"])
            ant = ultimos.get(chave)
            if ant is None or (v["data_lancamento"], v["id_lancamento"]) > (
                ant["data_lancamento"],
                ant["id_lancamento"],
            ):
                ultimos[chave] = v
        notas = {}
        for id, m in metas.items():
            if m["tipo_meta"] != "Individual":
                continue
            meses = [
                v
                for (mid, _), v in ultimos.items()
                if mid == id
                and v["nao_se_aplica"] == 0
                and v["previsto"] is not None
                and v["realizado"] is not None
            ]
            if not meses:
                notas[id] = None
                continue
            pares = [
                (Decimal(str(v["realizado"])), Decimal(str(v["previsto"])))
                for v in meses
            ]
            if m["polaridade"] == "Melhor para baixo":
                pares = [(b, a) for a, b in pares]
            if m["tipo_acumulacao"] == "Soma":
                numer = sum(a for a, b in pares)
                denom = sum(b for a, b in pares)
                at = numer / denom if denom else None
            else:
                at = (
                    sum(a / b for a, b in pares) / len(pares)
                    if all(b != 0 for a, b in pares)
                    else None
                )
            notas[id] = (
                None
                if at is None
                else (Decimal(0) if at < Decimal(".8") else min(at * 100, Decimal(120)))
            )
        scores = {}
        for p in tabelas["colaborador"]:
            if p["data_admissao"] > "2025-09-30" or (
                p["data_desligamento"] and p["data_desligamento"] < "2025-07-01"
            ):
                continue
            valores = []
            for m in metas.values():
                if m["id_colaborador"] != p["id_colaborador"]:
                    continue
                fonte = m
                visitados = set()
                while fonte and fonte["tipo_meta"] == "Compartilhada":
                    if fonte["id_meta"] in visitados:
                        fonte = None
                        break
                    visitados.add(fonte["id_meta"])
                    fonte = metas.get(fonte["id_meta_referencia"])
                n = notas.get(fonte["id_meta"]) if fonte else None
                if n is not None:
                    valores.append((n, Decimal(str(m["peso"]))))
            denominador = sum(peso for nota, peso in valores)
            scores[p["id_colaborador"]] = (
                sum(nota * peso for nota, peso in valores) / denominador
                if denominador != 0
                else None
            )

        def media(ids):
            vs = [scores[i] for i in ids if i in scores and scores[i] is not None]
            return sum(vs) / len(vs) if vs else None

        def iguais(a, b):
            assert (a is None and b is None) or (
                a is not None and b is not None and abs(float(a) - b) < 1e-10
            ), (a, b)

        rows = consulta(c, "SELECT * FROM scores")
        assert {r["id_colaborador"] for r in rows} == set(scores)
        for row in rows:
            iguais(scores[row["id_colaborador"]], row["score"])
        for row in consulta(c, "SELECT * FROM areas"):
            filhos = {row["id_area"]}
            while True:
                novos = filhos | {
                    a["id_area"] for a in tabelas["area"] if a["id_area_pai"] in filhos
                }
                if novos == filhos:
                    break
                filhos = novos
            iguais(
                media(
                    [
                        p["id_colaborador"]
                        for p in tabelas["colaborador"]
                        if p["id_area"] == row["id_area"]
                    ]
                ),
                row["score_direto"],
            )
            iguais(
                media(
                    [
                        p["id_colaborador"]
                        for p in tabelas["colaborador"]
                        if p["id_area"] in filhos
                    ]
                ),
                row["score_consolidado"],
            )
        times = {}
        for g in tabelas["colaborador"]:
            if g["data_admissao"] > "2025-12-31" or (
                g["data_desligamento"] and g["data_desligamento"] <= "2025-12-31"
            ):
                continue
            ids = [
                p["id_colaborador"]
                for p in tabelas["colaborador"]
                if p["id_gestor"] == g["id_colaborador"]
                and p["id_colaborador"] in scores
            ]
            if len(ids) >= 3 and media(ids) is not None:
                times[g["id_colaborador"]] = media(ids)
        rows = consulta(c, "SELECT * FROM times_gestores")
        assert {r["id_gestor"] for r in rows} == set(times)
        for row in rows:
            iguais(times[row["id_gestor"]], row["score_medio_time"])
        import csv

        with (ROOT / "respostas/p3_gestores.csv").open(
            encoding="utf-8", newline=""
        ) as f:
            for row in csv.DictReader(f):
                ranking = sorted(
                    times,
                    key=lambda i: (
                        (-times[i] if row["grupo"] == "top" else times[i]),
                        i,
                    ),
                )
                assert int(row["id_gestor"]) == ranking[int(row["posicao"]) - 1]
                assert Decimal(row["score_medio_time"]) == times[
                    int(row["id_gestor"])
                ].quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        resultado = {
            "scores_conferidos": len(scores),
            "areas_conferidas": len(tabelas["area"]),
            "gestores_conferidos": len(times),
            "media_geral": str(media(list(scores))),
        }
        print(resultado)
        return resultado


if __name__ == "__main__":
    validar()
