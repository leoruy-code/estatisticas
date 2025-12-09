# Plano de melhorias para probabilidades e ajuste por escalação

Este documento resume pontos de melhoria para aumentar a precisão das probabilidades finais, combinando médias de time, contexto de liga e impacto da escalação escolhida.

## 1. Fortalecer âncoras de liga e ajuste de força
- **Refinar médias da liga**: as médias globais são derivadas apenas das estatísticas agregadas por jogador. Calcule médias de gols, chutes, faltas e escanteios a partir de partidas históricas reais e use suavização por tamanho de amostra (ex.: média ponderada entre liga e time quando o time tem poucos jogos). Atualize `calcular_league_averages` e `_calcular_forcas` para aceitar esse mix explícito.
- **Separar casa/fora**: armazene médias de gols/escanteios sofridos e marcados por mando para cada time, e replique a mesma separação nas âncoras da liga. Use esses valores na estimativa de λ (`estimar_lambda_gols`, `estimar_lambda_escanteios`) em vez de um único número médio.
- **Manter coerência de ataque x defesa**: ao derivar `attack_strength` e `defense_weakness`, normalize ambos com a mesma base (mando correspondente) e garanta clipping em faixas realistas (ex.: 0.6–1.6) para evitar lambdas extremos quando houver poucos dados.

## 2. Ligar lambdas base ao impacto da escalação
- **Expor os lambdas base por time**: `prever_partida` calcula λ de gols, escanteios e faltas sem olhar a escalação. Faça o método retornar (ou permitir exportar) um dicionário de lambdas por time para que outras camadas possam ajustá-los.
- **Usar `PlayerModel` no pipeline**: `PlayerModel` já converte a escalação em `off_ratio`, `cross_ratio` e `foul_ratio`. Conecte-o ao `PoissonAnalyzer` para que, dado um conjunto de 11 jogadores, os lambdas de gols/escanteios/cartões sejam multiplicados pelos ratios antes de gerar probabilidades (over/under, BTTS, 1X2). Mantenha defaults neutros quando a escalação for incompleta.
- **Propagar metadados**: inclua no resultado final os ratios aplicados e, opcionalmente, as top contribuições individuais (ex.: jogadores com maior `off_index`) para facilitar auditoria e debugging.

## 3. Escolher distribuição e calibração com dados recentes
- **Checar overdispersão por mercado**: a troca para Binomial Negativa hoje depende de um threshold fixo. Calcule média/variância específicas por mercado (gols, escanteios, cartões) na janela recente e aplique o critério por tipo de evento, não apenas em um vetor genérico.
- **Calibração baseada em backtest**: expanda o uso do `Calibrator` para mais mercados (BTTS, 1X2) treinando calibradores separados por período (temporada/competição). Armazene parâmetros versionados para reproduzir resultados.

## 4. Entradas de dados e controles de qualidade
- **Validação de `times.json` e `jogadores.json`**: antes do cálculo, garanta que cada time tenha partidas mínimas, campos de escanteios, gols sofridos e forma recente; substitua valores ausentes por médias de liga e registre warnings.
- **Consistência temporal**: quando o usuário selecionar a escalação, permita informar se é provável ou confirmada e aplique pesos diferentes (ex.: ratio blend 70/30 entre lineup provável e média do time). Recalcule as métricas recentes (`metricas_5/10/20`) com datas para evitar misturar temporadas.

## 5. Fluxo sugerido de uso
1. Carregar dados e construir âncoras de liga (casa/fora).
2. Gerar lambdas base por time no `PoissonAnalyzer`.
3. Receber escalações prováveis e ajustar lambdas via `PlayerModel`.
4. Calcular probabilidades (gols, escanteios, cartões, 1X2) com a distribuição adequada e, se disponível, calibração treinada.
5. Exportar odds justas e metadados de ajuste para monitoramento.