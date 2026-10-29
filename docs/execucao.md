# Ambiente Python e execução local

O projeto foi executado com Python 3.13.7. Use `python -m pip` e `python -m pytest` para garantir que a instalação e os comandos usem o mesmo interpretador.
No ambiente virtual, prefira `.venv\Scripts\python.exe` no Windows; não é necessário ativar scripts do PowerShell.

## Problemas encontrados nesta máquina

1. `python` resolve para o Python 3.13.7 instalado, mas `py -0p` não lista instalações. O launcher `py` não foi usado nem alterado.
2. O Python global não tinha pytest e as demais dependências. Foi criado um ambiente virtual isolado.
3. O `ensurepip` falhou por permissões no diretório temporário e porque `SSLKEYLOGFILE` apontava para um arquivo fora da pasta permitida. A instalação funcionou usando uma pasta temporária gravável e removendo essa variável apenas do processo de instalação.
4. A primeira tentativa de baixar pacotes não tinha acesso à rede no ambiente restrito. A instalação foi repetida com acesso autorizado, sem mudar versões.

Se aparecerem os mesmos erros de permissão ao criar o ambiente, os comandos abaixo ajustam somente a sessão atual do terminal:

```powershell
New-Item -ItemType Directory -Force work/tmp | Out-Null
$env:TEMP = (Resolve-Path work/tmp).Path
$env:TMP = $env:TEMP
Remove-Item Env:SSLKEYLOGFILE -ErrorAction SilentlyContinue
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Esses ajustes não são requisitos do código e não alteram as variáveis persistentes do Windows.
Se um ambiente parcial ficou sem pip, execute `.venv\Scripts\python.exe -m ensurepip --upgrade` depois dos ajustes acima.

## Conferências

```powershell
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m scripts.gerar_resultados
.venv\Scripts\python.exe -m streamlit run painel/app.py
```

Use um segundo terminal para o agente. O painel e o agente consultam o mesmo banco, sem necessidade de manter um processo ETL ativo.
O histórico das verificações desta reorganização está em `validacao.md`.
