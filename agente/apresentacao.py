"""Respostas produzidas exclusivamente a partir dos resultados SQL."""


def fmt(v):
    return "sem score" if v is None else f"{v:.2f}".replace(".", ",")


def apresentar(ferramenta, r):
    if r["status"] != "ok":
        texto = r["mensagem"]
        if "opcoes" in r:
            texto += " " + ", ".join(f"#{o['id']} — {o['nome']}" for o in r["opcoes"])
        return texto
    d = r["dados"]
    if ferramenta == "comparar_areas":
        a, b = d
        dif = r["diferencas_a_menos_b"]
        return (
            f"{a['nome']}: direto {fmt(a['score_direto'])}, consolidado {fmt(a['score_consolidado'])}; "
            f"{b['nome']}: direto {fmt(b['score_direto'])}, consolidado {fmt(b['score_consolidado'])}. "
            f"Diferença A menos B: direto {fmt(dif['score_direto'])}, consolidado {fmt(dif['score_consolidado'])} pontos."
        )
    if ferramenta == "consultar_score_area":
        return f"{d['nome']} (ID {d['id_area']}): score direto {fmt(d['score_direto'])}; consolidado {fmt(d['score_consolidado'])}."
    if ferramenta == "consultar_score_colaborador":
        return f"{d['nome']} (ID {d['id_colaborador']}): {fmt(d['score'])}."
    if ferramenta == "consultar_melhor_diretoria":
        return (
            "; ".join(
                f"{v['nome']} (ID {v['id_area']}): consolidado {fmt(v['score_consolidado'])}"
                for v in d
            )
            + "."
            if d
            else "Nenhuma diretoria com score."
        )
    if ferramenta == "listar_colaboradores_por_gestor":
        texto = f"Time direto elegível de {r['gestor']}, score estritamente abaixo de {fmt(r['score_maximo'])}: "
        texto += (
            "; ".join(
                f"{v['nome']} (ID {v['id_colaborador']}): {fmt(v['score'])}" for v in d
            )
            if d
            else "nenhum colaborador pontuado encontrado"
        )
        return (
            texto
            + f". Elegíveis sem score: {len(r['sem_score'])}; não incluídos na comparação."
        )
    texto = f"Metas de {r['colaborador']}: "
    texto += (
        "; ".join(
            f"{v['nome_meta']} (ID {v['id_meta']}): atingimento {fmt(v['atingimento'] * 100) if v['atingimento'] is not None else 'indefinido'}%, nota {fmt(v['nota'])}, peso {v['peso']}, status {v['status']}"
            for v in d
        )
        if d
        else "nenhuma meta encontrada para o filtro"
    )
    return (
        texto
        + f". Metas sem nota: {len(r['sem_nota'])}; não tratadas como atingimento zero."
    )
