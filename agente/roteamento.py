"""Roteamento explícito e conferência dos argumentos contra a pergunta."""

import re

from agente.contratos import normalizar


def rotear(pergunta):
    texto = normalizar(pergunta).rstrip("?.! ")
    if re.fullmatch(
        r"(qual (?:e a )?diretoria (?:teve o melhor resultado consolidado|tem o maior score consolidado)|melhor diretoria)",
        texto,
    ):
        return "consultar_melhor_diretoria", {}
    m = re.fullmatch(
        r"(?:quais colaboradores|quem|liste os colaboradores) (?:do time|da equipe) (?:da|do|de) (.+?) (?:ficaram com score abaixo de|com score menor que|ficou abaixo de) (\d+(?:[.,]\d+)?)",
        texto,
    )
    if m:
        return "listar_colaboradores_por_gestor", {
            "nome_gestor": m[1],
            "score_maximo": float(m[2].replace(",", ".")),
        }
    m = re.fullmatch(
        r"(?:quais|liste as) metas (?:da|do|de) (.+?) (?:ficaram abaixo de|com atingimento menor que) (\d+(?:[.,]\d+)?)%(?: de atingimento)?",
        texto,
    )
    if m:
        return "consultar_metas_colaborador", {
            "nome_colaborador": m[1],
            "atingimento_maximo": float(m[2].replace(",", ".")) / 100,
        }
    m = re.fullmatch(
        r"(?:qual (?:e )?o score|mostre o score) (?:da colaboradora|do colaborador) (.+)",
        texto,
    )
    if m:
        return "consultar_score_colaborador", {"nome_colaborador": m[1]}
    m = re.fullmatch(
        r"(?:qual (?:e )?o score|mostre o score) (?:da|do) (?:area )?(.+)", texto
    )
    if m:
        return "consultar_score_area", {"nome_area": m[1]}
    m = re.fullmatch(
        r"(?:compare|compare os scores das areas) (.+?) (?:e|com) (.+)", texto
    )
    if m:
        return "comparar_areas", {"nome_area_a": m[1], "nome_area_b": m[2]}
    if texto in (
        "qual o score",
        "qual e o score",
        "como foi o resultado",
        "score de quem",
    ):
        return "solicitar_esclarecimento", {"motivo": "entidade_ausente"}
    return None, {}


def bloqueada(pergunta):
    texto = normalizar(pergunta)
    return bool(
        re.search(
            r"\b(ignore|ignorar|apague|apagar|delete|drop|insert|update|sql|senha|token|execute|executar|invente|invente numeros)\b",
            texto,
        )
        or re.search(r"explique (?:as )?causas|por que|preveja|202[0-46-9]", texto)
    )


def argumentos_na_pergunta(args, pergunta):
    """Rejeita entidades e limites inventados pelo modelo; não valida sua semântica."""
    texto = normalizar(pergunta)
    for chave, valor in args.items():
        if chave.startswith("nome_"):
            if not re.search(
                r"(?<!\w)" + re.escape(normalizar(valor)) + r"(?!\w)", texto
            ):
                return False
        elif chave in ("score_maximo", "atingimento_maximo") and valor is not None:
            valores = [
                float(n.replace(",", ".").replace("−", "-"))
                for n in re.findall(
                    r"(?<![\w#.,+−-])[+−-]?\d+(?:[.,]\d+)?(?!\w|[.,]\d)", texto
                )
            ]
            esperado = valor * 100 if chave == "atingimento_maximo" else valor
            if not any(abs(v - esperado) < 1e-9 for v in valores):
                return False
    return True
