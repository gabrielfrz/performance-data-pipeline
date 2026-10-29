# Validação vigente — após a auditoria de regras

A versão atual inclui o peso negativo conforme a fórmula literal da R9. O banco original permanece intacto.

| Verificação | Resultado |
|---|---|
| Testes determinísticos | 150 aprovados, zero falhas; 23 integrações deselecionadas |
| Cinco perguntas no Ollama real | Cinco aprovadas, sem fallback |
| SQL e CSV | 72 / 11 / 6 linhas, cabeçalhos preservados e comparação integral |
| Validação independente SQLite/Decimal | 72 pessoas, 11 áreas e nove gestores conferidos |
| Validação independente CSV/Decimal | 316 metas, 72 pessoas, 11 áreas e nove gestores conferidos |
| Painel | AppTest, navegador e nova captura com média 95,67 e Financeira 102,90 |
| Fonte | SHA-256 original preservado |

A [auditoria completa](auditoria_regras.md) contém matriz R1–R11, decisões, fronteiras, todos os scores modificados, arquivos afetados e riscos restantes.
Os 18 testes opcionais de Ollama além das cinco perguntas não foram reexecutados. O histórico de desenvolvimento foi removido desta cópia de entrega; os resultados e limitações vigentes estão resumidos nesta página e em [auditoria_regras.md](auditoria_regras.md).

## Reproduzir

Na raiz do projeto, com as dependências instaladas:

```powershell
.venv\Scripts\python.exe -m scripts.gerar_resultados
.venv\Scripts\python.exe -m tests.validar_independente
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest --ollama -m ollama -k oficial -q
.venv\Scripts\python.exe -m streamlit run painel/app.py
.venv\Scripts\python.exe -m agente.agent --modo ollama --demo
```

`python -m scripts.gerar_sql` regenera as três consultas autônomas se a base SQL for alterada. O uso cotidiano da entrega não exige essa etapa.
As dificuldades de instalação encontradas nesta máquina estão em [execucao.md](execucao.md).
