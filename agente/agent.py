"""Agente com seleção de ferramentas por Ollama ou roteador determinístico explícito."""

import argparse
import json
from tempfile import mkdtemp
from pathlib import Path

from agente.apresentacao import apresentar
from agente.contratos import validar_argumentos
from agente.llm import ClienteOllama, ErroLLM
from agente.roteamento import argumentos_na_pergunta, bloqueada
from agente.roteamento import rotear as rotear
from agente.tools import Ferramentas
from scripts.dados import ROOT, conectar

PERGUNTAS = [
    "Qual o score da Gerência de Marketing?",
    "Quais colaboradores do time da Sofia Oliveira ficaram com score abaixo de 90?",
    "Qual diretoria teve o melhor resultado consolidado?",
    "Quais metas do Nicolas Vasconcelos ficaram abaixo de 80% de atingimento?",
    "Qual o score da área Vendas Oeste?",
]


def responder(pergunta, conn, modo="deterministico", fallback=False, cliente=None):
    base = {
        "modo": modo,
        "pergunta": pergunta,
        "ferramenta": None,
        "argumentos": {},
        "evidencias": [],
    }
    if not isinstance(pergunta, str) or not pergunta.strip() or len(pergunta) > 2000:
        return {
            **base,
            "status": "argumento_invalido",
            "classificacao": "invalida",
            "resposta": "Informe uma pergunta de até 2000 caracteres.",
        }
    if bloqueada(pergunta):
        return {
            **base,
            "status": "nao_compreendido",
            "classificacao": "nao_suportada",
            "resposta": "Esta solicitação está fora do escopo das consultas de metas 2025.",
        }
    if modo == "ollama":
        try:
            ferramenta, args, rastro = (cliente or ClienteOllama()).selecionar(pergunta)
            base["llm"] = rastro
            if validar_argumentos(ferramenta, args) or not argumentos_na_pergunta(
                args, pergunta
            ):
                raise ErroLLM(
                    "resposta_invalida",
                    "A seleção contém argumentos inválidos ou não informados na pergunta.",
                    rastro,
                )
        except ErroLLM as e:
            if fallback and e.codigo in (
                "llm_indisponivel",
                "modelo_indisponivel",
                "erro_http",
            ):
                r = responder(pergunta, conn)
                r["modo_solicitado"] = "ollama"
                r["fallback_motivo"] = e.codigo
                r["aviso"] = (
                    "Ollama indisponível: resposta produzida pelo roteador determinístico."
                )
                return r
            return {
                **base,
                "status": "erro_llm",
                "classificacao": "erro",
                "erro": e.codigo,
                "resposta": str(e),
                "diagnostico_llm": e.detalhes,
            }
    elif modo == "deterministico":
        ferramenta, args = rotear(pergunta)
    else:
        return {
            **base,
            "status": "argumento_invalido",
            "classificacao": "invalida",
            "resposta": "Modo desconhecido.",
        }
    base.update(ferramenta=ferramenta, argumentos=args)
    if ferramenta is None or ferramenta == "informar_fora_escopo":
        return {
            **base,
            "status": "nao_compreendido",
            "classificacao": "nao_suportada",
            "resposta": "Pergunta não suportada. Use os exemplos em README.md; consultas não explicam causas.",
        }
    if ferramenta == "solicitar_esclarecimento":
        mensagens = {
            "entidade_ausente": "Informe se deseja uma área ou colaborador, com nome completo ou #ID.",
            "limite_ausente": "Informe o limite de score ou atingimento desejado.",
            "pergunta_ambigua": "Especifique a entidade e o resultado desejado; a pergunta está ambígua.",
        }
        return {
            **base,
            "status": "ambiguo",
            "classificacao": "ambigua",
            "resposta": mensagens[args["motivo"]],
        }
    tools = Ferramentas(conn)
    resultado = tools.executar(ferramenta, args)
    categorias = {
        "ok": "respondida",
        "nao_encontrado": "nao_encontrada",
        "ambiguo": "ambigua",
        "argumento_invalido": "invalida",
        "inelegivel": "inelegivel",
        "ferramenta_invalida": "invalida",
    }
    return {
        **base,
        "status": resultado["status"],
        "classificacao": categorias[resultado["status"]],
        "resposta": apresentar(ferramenta, resultado),
        "resultado": resultado,
        "evidencias": tools.evidencias,
    }


def demonstrar(modo="deterministico", fallback=False):
    with conectar() as c:
        respostas = [responder(p, c, modo=modo, fallback=fallback) for p in PERGUNTAS]
    pasta = ROOT / "work/execucoes"
    pasta.mkdir(parents=True, exist_ok=True)
    saida = Path(mkdtemp(prefix=f"{modo}_", dir=pasta))
    sufixo = "_ollama" if modo == "ollama" else ""
    (saida / f"execucoes{sufixo}.json").write_text(
        json.dumps(respostas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    linhas = [
        "# Respostas executadas\n",
        f"Modo solicitado: {modo}. O modo efetivo, os erros e o eventual fallback estão registrados no JSON de execução. Números somente das ferramentas.\n",
    ]
    for i, r in enumerate(respostas, 1):
        linhas.extend(
            [
                f"## {i}. {r['pergunta']}\n",
                r["resposta"] + "\n",
                f"Status: {r['status']}; modo efetivo: {r['modo']}.\n",
                f"Ferramenta: `{r['ferramenta']}`. Argumentos: `{json.dumps(r['argumentos'], ensure_ascii=False)}`.\n",
            ]
        )
        for e in r["evidencias"]:
            linhas.extend(
                [
                    "Consulta após `sql/base_calculo.sql`:\n",
                    "```sql\n" + e["sql"] + "\n```",
                    "Parâmetros: `"
                    + json.dumps(e["parametros"], ensure_ascii=False)
                    + "`.\n",
                ]
            )
    linhas.extend(
        [
            "## Avaliação\n",
            "Esta execução deve ser avaliada pelos estados registrados acima. Área inexistente não equivale a score zero. O modo determinístico não mede a qualidade de um LLM. O cliente Ollama exige serviço e modelo locais; testes com respostas simuladas validam o protocolo, não a compreensão de um modelo.\n",
            "Comparações de duas áreas são suportadas, mas pedidos de causas, previsões e alterações não. Nomes completos e IDs explícitos evitam aproximações silenciosas.",
        ]
    )
    (saida / f"respostas{sufixo}.md").write_text(
        "\n".join(linhas), encoding="utf-8"
    )
    for r in respostas:
        print(r["resposta"])
    print(f"Arquivos desta execução: {saida}")
    return saida


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pergunta", nargs="?")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument(
        "--modo", choices=["deterministico", "ollama"], default="deterministico"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Fallback explícito em caso de indisponibilidade do Ollama",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Mostrar resposta com evidências e modo efetivo",
    )
    args = parser.parse_args()
    if args.demo:
        demonstrar(args.modo, args.fallback)
    elif args.pergunta:
        with conectar() as c:
            r = responder(args.pergunta, c, args.modo, args.fallback)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            if "aviso" in r:
                print(r["aviso"])
            print(r["resposta"])
        if r["status"] == "erro_llm":
            raise SystemExit(2)
    else:
        parser.print_help()
