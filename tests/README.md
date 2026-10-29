# Testes isolados

Os módulos de produção não importam este diretório. Instale as dependências com o Python do ambiente virtual:

```powershell
python -m pip install -r tests/requirements.txt
python -m pytest -q
```

Por padrão, os 23 casos de integração real ficam deselecionados, mesmo que exista a antiga variável `MEREO_TEST_OLLAMA`.
Os testes determinísticos incluem SQLite em memória, verificações dos CSVs, cliente HTTP simulado em loopback e execução do painel via Streamlit AppTest.
Não exigem serviços externos. O servidor HTTP simulado é criado e encerrado pela própria fixture.

Com Ollama ativo e `qwen3:4b` disponível:

```powershell
python -m pytest --ollama -m ollama -q
```

Para incluir as duas categorias: `python -m pytest --ollama -q`.
A integração pode levar vários minutos. Não usa fallback e falha se o modelo/serviço estiver indisponível.
Cada execução grava o JSON em um diretório temporário do pytest, identificado na saída capturada; `-s` mostra o caminho durante o teste.

## Organização

- `test_regras.py`: limites, regras R1–R11, gestores e sincronismo do SQL.
- `test_agente_painel.py`: consultas, cinco perguntas determinísticas, CSVs e painel.
- `test_contratos_e_limites.py`: HTTP simulado, argumentos, falhas e cenários adicionais do painel.
- `test_seguranca_limites.py`: limites numéricos e entradas inválidas.
- `test_saidas.py`: comparação dos três CSVs com o SQL e regressão da demonstração que antes sobrescrevia respostas entregues.
- `validar_independente.py`: implementação Decimal exclusiva de validação; execute também com `python -m tests.validar_independente`.
- `integracao/`: cenários e testes reais do Ollama.

As alterações de dados nos testes ocorrem em bancos em memória. Novos arquivos usam diretórios temporários.
Uma fixture de sessão confere hashes do banco, SQL, CSVs, documentação e print antes e depois da suíte.
Ela detecta alterações; não substitui o uso de conexões somente leitura e destinos temporários.
