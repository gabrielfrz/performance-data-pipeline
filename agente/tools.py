"""Seis ferramentas fixas: sem SQL fornecido pelo usuário ou modelo."""

from agente.contratos import normalizar as normalizar
from agente.contratos import validar_argumentos
from scripts.dados import consulta


class Ferramentas:
    def __init__(self, conn):
        self.conn = conn
        self.conn.create_function("normalizar", 1, normalizar)
        self.evidencias = []

    def _query(self, sql, params=()):
        rows = consulta(self.conn, sql, params)
        self.evidencias.append(
            {
                "base": "sql/base_calculo.sql",
                "sql": sql,
                "parametros": list(params),
                "resultado": rows,
            }
        )
        return rows

    def _resolver(self, nome, entidade):
        if not isinstance(nome, str) or not nome.strip() or len(nome) > 200:
            return {
                "status": "argumento_invalido",
                "mensagem": "Informe um nome ou #ID válido.",
            }
        nome = nome.strip()
        tabela, chave = {
            "area": ("area", "id_area"),
            "colaborador": ("colaborador", "id_colaborador"),
        }[entidade]
        if nome.startswith("#") and nome[1:].isdigit():
            if not nome[1:].isascii() or not 0 < int(nome[1:]) <= 2**63 - 1:
                return {
                    "status": "argumento_invalido",
                    "mensagem": "ID fora do intervalo permitido.",
                }
            sql = f"SELECT * FROM {tabela} WHERE {chave}=?"
            params = (int(nome[1:]),)
        else:
            sql = f"SELECT * FROM {tabela} WHERE normalizar(nome)=? ORDER BY {chave}"
            params = (normalizar(nome),)
        rows = self._query(sql, params)
        if not rows:
            rotulo = (
                "Área não encontrada"
                if entidade == "area"
                else "Colaborador não encontrado"
            )
            return {
                "status": "nao_encontrado",
                "mensagem": f"{rotulo}: {normalizar(nome)}.",
            }
        if len(rows) > 1:
            return {
                "status": "ambiguo",
                "mensagem": "Há nomes repetidos. Repita com #ID.",
                "opcoes": [{"id": r[chave], "nome": r["nome"]} for r in rows],
            }
        return {"status": "ok", "entidade": rows[0]}

    def consultar_score_area(self, nome_area):
        r = self._resolver(nome_area, "area")
        if r["status"] != "ok":
            return r
        dados = self._query(
            "SELECT * FROM areas WHERE id_area=?", (r["entidade"]["id_area"],)
        )[0]
        return {"status": "ok", "dados": dados}

    def consultar_score_colaborador(self, nome_colaborador):
        r = self._resolver(nome_colaborador, "colaborador")
        if r["status"] != "ok":
            return r
        pessoa = r["entidade"]
        rows = self._query(
            "SELECT * FROM scores WHERE id_colaborador=?", (pessoa["id_colaborador"],)
        )
        if not rows:
            return {
                "status": "inelegivel",
                "mensagem": f"{pessoa['nome']} não é elegível no ciclo 2025.",
            }
        return {"status": "ok", "dados": rows[0]}

    def listar_colaboradores_por_gestor(self, nome_gestor, score_maximo):
        if validar_argumentos(
            "listar_colaboradores_por_gestor",
            {"nome_gestor": nome_gestor, "score_maximo": score_maximo},
        ):
            return {
                "status": "argumento_invalido",
                "mensagem": "score_maximo deve ser um número de 0 a 120.",
            }
        r = self._resolver(nome_gestor, "colaborador")
        if r["status"] != "ok":
            return r
        g = r["entidade"]
        gid = g["id_colaborador"]
        rows = self._query(
            "SELECT id_colaborador,nome,score FROM scores WHERE id_gestor=? AND score<? ORDER BY score,id_colaborador",
            (gid, score_maximo),
        )
        sem = self._query(
            "SELECT id_colaborador,nome FROM scores WHERE id_gestor=? AND score IS NULL ORDER BY id_colaborador",
            (gid,),
        )
        return {
            "status": "ok",
            "gestor": g["nome"],
            "score_maximo": score_maximo,
            "dados": rows,
            "sem_score": sem,
        }

    def consultar_melhor_diretoria(self):
        # Na base, as três raízes são diretorias. Devolve todos os empates reais.
        rows = self._query("""SELECT id_area,nome,score_consolidado FROM areas
WHERE id_area_pai IS NULL AND score_consolidado=(
 SELECT MAX(score_consolidado) FROM areas WHERE id_area_pai IS NULL)
ORDER BY id_area""")
        return {"status": "ok", "dados": rows}

    def consultar_metas_colaborador(self, nome_colaborador, atingimento_maximo=None):
        if validar_argumentos(
            "consultar_metas_colaborador",
            {
                "nome_colaborador": nome_colaborador,
                "atingimento_maximo": atingimento_maximo,
            },
        ):
            return {
                "status": "argumento_invalido",
                "mensagem": "Informe um limite de atingimento não negativo.",
            }
        r = self._resolver(nome_colaborador, "colaborador")
        if r["status"] != "ok":
            return r
        p = r["entidade"]
        pid = p["id_colaborador"]
        if not self._query(
            "SELECT id_colaborador FROM elegiveis WHERE id_colaborador=?", (pid,)
        ):
            return {
                "status": "inelegivel",
                "mensagem": f"{p['nome']} não é elegível no ciclo 2025.",
            }
        sql = "SELECT * FROM notas_meta WHERE id_colaborador=?"
        params = (pid,)
        if atingimento_maximo is not None:
            sql += " AND atingimento<?"
            params += (atingimento_maximo,)
        rows = self._query(sql + " ORDER BY id_meta", params)
        sem = self._query(
            "SELECT id_meta,nome_meta,status FROM notas_meta WHERE id_colaborador=? AND nota IS NULL ORDER BY id_meta",
            (pid,),
        )
        return {
            "status": "ok",
            "colaborador": p["nome"],
            "dados": rows,
            "sem_nota": sem,
            "atingimento_maximo": atingimento_maximo,
        }

    def comparar_areas(self, nome_area_a, nome_area_b):
        a = self.consultar_score_area(nome_area_a)
        if a["status"] != "ok":
            return a
        b = self.consultar_score_area(nome_area_b)
        if b["status"] != "ok":
            return b
        a, b = a["dados"], b["dados"]
        diferencas = {
            c: a[c] - b[c] if a[c] is not None and b[c] is not None else None
            for c in ("score_direto", "score_consolidado")
        }
        return {"status": "ok", "dados": [a, b], "diferencas_a_menos_b": diferencas}

    def executar(self, nome, argumentos):
        permitidas = {
            n: getattr(self, n)
            for n in (
                "consultar_score_area",
                "consultar_score_colaborador",
                "listar_colaboradores_por_gestor",
                "consultar_melhor_diretoria",
                "consultar_metas_colaborador",
                "comparar_areas",
            )
        }
        self.evidencias = []
        if not isinstance(nome, str) or nome not in permitidas:
            return {
                "status": "ferramenta_invalida",
                "mensagem": "Ferramenta não permitida.",
            }
        if validar_argumentos(nome, argumentos):
            return {
                "status": "argumento_invalido",
                "mensagem": "Argumentos não correspondem à ferramenta.",
            }
        return permitidas[nome](**argumentos)
