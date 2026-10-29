# Cinco perguntas — execução após a auditoria de regras

Executadas com `qwen3:4b`, sem fallback, após incluir o peso negativo conforme R9. O modelo selecionou ferramentas e argumentos; os números foram obtidos no SQLite somente leitura.

## 1. Qual o score da Gerência de Marketing?

Gerência de Marketing (ID 5): score direto 84,43; consolidado 84,43.

Ferramenta: `consultar_score_area`. Argumentos: `{"nome_area": "Gerência de Marketing"}`.

Estado: `ok`; duração: 57.44 s.

## 2. Quais colaboradores do time da Sofia Oliveira ficaram com score abaixo de 90?

Time direto elegível de Sofia Oliveira, score estritamente abaixo de 90,00: Sabrina Cardoso (ID 148): 54,85; Manuela Oliveira (ID 157): 63,67; Gabriela Ferraz (ID 155): 89,30. Elegíveis sem score: 0; não incluídos na comparação.

Ferramenta: `listar_colaboradores_por_gestor`. Argumentos: `{"nome_gestor": "Sofia Oliveira", "score_maximo": 90}`.

Estado: `ok`; duração: 75.86 s.

## 3. Qual diretoria teve o melhor resultado consolidado?

Diretoria Financeira (ID 10): consolidado 102,90.

Ferramenta: `consultar_melhor_diretoria`. Argumentos: `{}`.

Estado: `ok`; duração: 34.02 s.

## 4. Quais metas do Nicolas Vasconcelos ficaram abaixo de 80% de atingimento?

Metas de Nicolas Vasconcelos: Leads gerados (ID 5121): atingimento 77,07%, nota 0,00, peso 35, status ok; Número de reuniões qualificadas (ID 5122): atingimento 70,19%, nota 0,00, peso 30, status ok. Metas sem nota: 0; não tratadas como atingimento zero.

Ferramenta: `consultar_metas_colaborador`. Argumentos: `{"nome_colaborador": "Nicolas Vasconcelos", "atingimento_maximo": 0.8}`.

Estado: `ok`; duração: 67.82 s.

## 5. Qual o score da área Vendas Oeste?

Área não encontrada: vendas oeste.

Ferramenta: `consultar_score_area`. Argumentos: `{"nome_area": "Vendas Oeste"}`.

Estado: `nao_encontrado`; duração: 36.63 s.

## Avaliação

As cinco ferramentas, seus argumentos e os resultados corresponderam às consultas de referência. A Diretoria Financeira permanece líder, agora com consolidado 102,90. As outras quatro respostas não mudaram. Vendas Oeste retornou área inexistente, sem score inventado.

Não houve erro nas cinco perguntas desta execução. Isso não garante compreensão universal: o agente cobre consultas de resultados, não causas, previsões ou memória conversacional. Os testes determinísticos verificam argumentos inválidos e falhas de protocolo; os 18 outros testes opcionais reais não foram reexecutados nesta auditoria. Para melhorar, ampliaria casos a partir dos erros observados e mediria acerto e latência ao trocar o modelo.

As respostas registram a execução final da entrega. O histórico de desenvolvimento não integra este pacote.
