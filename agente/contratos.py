"""Contratos compartilhados pelo cliente LLM e pelo executor de ferramentas."""

import math
import unicodedata


def nome(descricao):
    return {
        "type": "string",
        "description": descricao,
        "minLength": 1,
        "maxLength": 200,
    }


def contrato(descricao, propriedades, obrigatorios):
    return {
        "description": descricao,
        "parameters": {
            "type": "object",
            "properties": propriedades,
            "required": obrigatorios,
            "additionalProperties": False,
        },
    }


CONTRATOS = {
    "consultar_score_area": contrato(
        "Score direto e consolidado da área no ciclo 2025.",
        {"nome_area": nome("Nome completo da área ou #ID explícito na pergunta.")},
        ["nome_area"],
    ),
    "consultar_score_colaborador": contrato(
        "Score de um colaborador elegível em 2025.",
        {"nome_colaborador": nome("Nome completo ou #ID explícito.")},
        ["nome_colaborador"],
    ),
    "listar_colaboradores_por_gestor": contrato(
        "Subordinados diretos elegíveis com score estritamente abaixo do limite.",
        {
            "nome_gestor": nome("Nome completo do gestor ou #ID explícito."),
            "score_maximo": {"type": "number", "minimum": 0, "maximum": 120},
        },
        ["nome_gestor", "score_maximo"],
    ),
    "consultar_melhor_diretoria": contrato(
        "Diretorias com o maior score consolidado em 2025.", {}, []
    ),
    "consultar_metas_colaborador": contrato(
        "Metas do colaborador; filtro opcional de atingimento estritamente menor.",
        {
            "nome_colaborador": nome("Nome completo ou #ID explícito."),
            "atingimento_maximo": {
                "type": ["number", "null"],
                "minimum": 0,
                "description": "Razão: 80% deve ser 0.8; ausente/null lista todas.",
            },
        },
        ["nome_colaborador"],
    ),
    "comparar_areas": contrato(
        "Compara duas áreas, incluindo direto, consolidado e diferença A menos B.",
        {
            "nome_area_a": nome("Primeira área, nome completo ou #ID."),
            "nome_area_b": nome("Segunda área, nome completo ou #ID."),
        },
        ["nome_area_a", "nome_area_b"],
    ),
    "solicitar_esclarecimento": contrato(
        "Use para pergunta ambígua ou sem entidade/limite necessário.",
        {
            "motivo": {
                "type": "string",
                "enum": ["entidade_ausente", "limite_ausente", "pergunta_ambigua"],
            }
        },
        ["motivo"],
    ),
    "informar_fora_escopo": contrato(
        "Use para causas, previsões, alterações, SQL livre ou assunto fora de metas 2025.",
        {},
        [],
    ),
}


def validar_argumentos(ferramenta, argumentos):
    if not isinstance(ferramenta, str) or ferramenta not in CONTRATOS:
        return "ferramenta_invalida"
    if not isinstance(argumentos, dict):
        return "argumento_invalido"
    schema = CONTRATOS[ferramenta]["parameters"]
    if set(argumentos) - set(schema["properties"]) or set(schema["required"]) - set(
        argumentos
    ):
        return "argumento_invalido"
    for chave, valor in argumentos.items():
        regra = schema["properties"][chave]
        tipos = regra["type"]
        if isinstance(tipos, str):
            tipos = [tipos]
        if valor is None and "null" in tipos:
            continue
        if "string" in tipos:
            if (
                not isinstance(valor, str)
                or not valor.strip()
                or len(valor) > regra.get("maxLength", 200)
            ):
                return "argumento_invalido"
            if "enum" in regra and valor not in regra["enum"]:
                return "argumento_invalido"
            if chave.startswith("nome_") and valor.strip().startswith("#"):
                id_texto = valor.strip()[1:]
                if (
                    not id_texto.isascii()
                    or not id_texto.isdigit()
                    or not 0 < int(id_texto) <= 2**63 - 1
                ):
                    return "argumento_invalido"
        elif "number" in tipos:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                return "argumento_invalido"
            try:
                finito = math.isfinite(valor)
            except OverflowError:
                finito = False
            if (
                not finito
                or valor < regra.get("minimum", -math.inf)
                or valor > regra.get("maximum", math.inf)
            ):
                return "argumento_invalido"
        else:
            return "argumento_invalido"
    return None


def schemas_ollama():
    return [
        {"type": "function", "function": {"name": n, **c}} for n, c in CONTRATOS.items()
    ]


def normalizar(texto):
    return " ".join(
        "".join(
            ch
            for ch in unicodedata.normalize("NFKD", texto)
            if not unicodedata.combining(ch)
        )
        .casefold()
        .split()
    )
