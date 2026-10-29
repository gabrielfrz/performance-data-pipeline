"""python -m scripts.gerar_resultados"""

import hashlib

import pandas as pd
from scripts.dados import DB, ROOT, conectar
from scripts.gerar_sql import FINAIS, gerar


def main():
    gerar(check=True)
    antes = hashlib.sha256(DB.read_bytes()).hexdigest()
    (ROOT / "respostas").mkdir(exist_ok=True)
    with conectar() as conn:
        for nome in FINAIS:
            sql = (ROOT / "sql" / f"{nome}.sql").read_text(encoding="utf-8")
            df = pd.read_sql_query(sql, conn)
            df.to_csv(
                ROOT / "respostas" / f"{nome}.csv",
                index=False,
                float_format="%.2f",
                na_rep="",
                encoding="utf-8",
                lineterminator="\n",
            )
            print(f"{nome}: {len(df)} linhas")
    assert hashlib.sha256(DB.read_bytes()).hexdigest() == antes
    print("SHA-256 da fonte preservada:", antes)


if __name__ == "__main__":
    main()
