Vou estruturar em Milestones e, dentro de cada uma, issues numeradas com:

Título

Objetivo

Tarefas (Checklist)

Critérios de aceite

# Plano de Implementação por Tarefas (GitHub Issues)
Baseado no documento: `sistema_previsao_rag_sem_llm_preditivo.md`

---

## Milestone 1 – Camada de Dados (Times, Partidas, Jogadores)

### Issue 1 – Definir e criar schema de times (`teams` e `team_stats`)

**Objetivo**  
Criar tabelas para armazenar informações básicas e estatísticas agregadas dos times.

**Tarefas**
- [ ] Definir campos da tabela `teams`:
  - `id`, `nome`, `liga`, `sofascore_id`, `ativo`
- [ ] Definir campos da tabela `team_stats`:
  - `team_id`, `jogos_total`, `gols_marcados_media`, `gols_sofridos_media`,  
    `escanteios_for_media`, `escanteios_against_media`,  
    `chutes_for_media`, `chutes_against_media`,  
    `cartoes_for_media`, `cartoes_against_media`,  
    `faltas_for_media`, `faltas_against_media`,  
    `forma_multiplicador`, `updated_at`
- [ ] Escrever migrations/DDL (SQL) para criar as tabelas.
- [ ] Atualizar `init.sql` (se estiver usando) ou script equivalente de criação de schema.

**Critérios de aceite**
- [ ] Tabelas `teams` e `team_stats` existem no banco.
- [ ] Consegue-se inserir e consultar registros de exemplo sem erro.

---

### Issue 2 – Definir e criar schema de partidas (`matches` e opcional `team_games`)

**Objetivo**  
Armazenar o histórico de partidas com estatísticas básicas.

**Tarefas**
- [ ] Definir tabela `matches`:
  - `id`, `data`, `home_team_id`, `away_team_id`,  
    `home_goals`, `away_goals`,  
    `home_corners`, `away_corners`,  
    `home_shots`, `away_shots`,  
    `home_fouls`, `away_fouls`,  
    `home_cards`, `away_cards`,  
    `status`, `liga`, `fonte_event_id`
- [ ] (Opcional mas recomendado) Definir tabela `team_games`:
  - `match_id`, `team_id`, `opponent_id`, `mandante`,  
    `gols_pro`, `gols_contra`,  
    `escanteios_pro`, `escanteios_contra`,  
    `chutes_pro`, `chutes_contra`,  
    `faltas_pro`, `faltas_contra`,  
    `cartoes_pro`, `cartoes_contra`
- [ ] Escrever migrations/DDL.
- [ ] Criar índices básicos (por exemplo, por `team_id`, `data`).

**Critérios de aceite**
- [ ] Conseguimos salvar uma partida real com todas as estatísticas.
- [ ] Consultas simples (por time, por data) funcionam.

---

### Issue 3 – Definir e criar schema de jogadores (`players` e `player_stats`)

**Objetivo**  
Armazenar os jogadores e suas estatísticas agregadas.

**Tarefas**
- [ ] Definir tabela `players`:
  - `id`, `nome`, `time_atual_id`, `posicao`, `nascimento` (opcional), `ativo`
- [ ] Definir tabela `player_stats`:
  - `player_id`, `minutos_total`, `jogos_total`, `minutos_por_jogo`,  
    `gols_total`, `gols_por_90`,  
    `finalizacoes_total`, `finalizacoes_por_90`,  
    `assistencias_total`,  
    `xg_total`, `xg_por_90` (se disponível),  
    `passes_chave_por_90`,  
    `escanteios_cobrados_por_90`, `cruzamentos_por_90`,  
    `faltas_cometidas_por_90`, `faltas_sofridas_por_90`,  
    `cartoes_amarelos_total`, `cartoes_vermelhos_total`,  
    `periodo`, `updated_at`
- [ ] Escrever migrations/DDL.
- [ ] Criar índices por `player_id`, `time_atual_id`.

**Critérios de aceite**
- [ ] Conseguimos salvar stats agregadas de um jogador real.
- [ ] Consegue-se consultar todos os jogadores de um time com suas médias.

---

### Issue 4 – ETL: carregar e atualizar estatísticas de times

**Objetivo**  
Ler dados brutos (scrapers/JSONs) e consolidar em `team_stats`.

**Tarefas**
- [ ] Mapear de onde vêm os dados (SofaScore ou outro).
- [ ] Ajustar scrapers existentes para:
  - salvar dados brutos no BD (`matches`),
  - não descartar jogos com 0 (escanteios, chutes etc.).
- [ ] Implementar job/rotina que:
  - calcula médias por time (gols, escanteios, chutes, faltas, cartões),
  - calcula `forma_multiplicador` (últimos 5 vs janela longa),
  - salva em `team_stats`.
- [ ] Criar comando/CLI para rodar o ETL manualmente (ex.: `python -m etl.team_stats`).

**Critérios de aceite**
- [ ] `team_stats` está preenchida para todos os times da liga.
- [ ] Campos como `gols_marcados_media`, `escanteios_for_media` fazem sentido comparados com dados brutos.

---

### Issue 5 – ETL: carregar e atualizar estatísticas de jogadores

**Objetivo**  
Popular `players` e `player_stats` com dados agregados por jogador.

**Tarefas**
- [ ] Ajustar scrapers (ou fontes) para identificar jogadores, minutos, gols, chutes etc.
- [ ] Implementar rotina que:
  - preenche/atualiza tabela `players` (nome, time, posição).
  - agrega eventos em nível de jogador e salva em `player_stats`.
- [ ] Calcular:
  - `gols_por_90`, `finalizacoes_por_90`, `xg_por_90`,  
    `passes_chave_por_90`, `escanteios_cobrados_por_90`, `cruzamentos_por_90` etc.
- [ ] Definir política para `periodo` (temporada inteira vs janela de jogos).

**Critérios de aceite**
- [ ] `player_stats` contém dados coerentes para jogadores titulares recorrentes.
- [ ] Conseguimos consultar os jogadores mais finalizadores de um time.

---

## Milestone 2 – Modelo de Times (λ por time)

### Issue 6 – Calcular média da liga e forças de ataque/defesa

**Objetivo**  
Criar funções que calculam estatísticas da liga e definem força de ataque/defesa dos times.

**Tarefas**
- [ ] Implementar função que calcula `league_avg_goals_for` a partir de `matches` ou `team_games`.
- [ ] Implementar cálculo de:
  ```python
  attack_strength_goals  = team.gols_marcados_media  / league_avg_goals_for
  defense_weakness_goals = team.gols_sofridos_media / league_avg_goals_for


 Repetir a lógica (se desejado) para escanteios, chutes etc.

 Salvar esses valores em team_stats ou calcular sob demanda.

Critérios de aceite

 Para cada time, temos attack_strength e defense_weakness.

 Médias extremas fazem sentido (time mais ofensivo ≫ 1.0, pior ≪ 1.0).

Issue 7 – Implementar cálculo de λ_gols para um confronto

Objetivo
Dado Time A (casa) e Time B (fora), calcular λ de gols para os dois lados.

Tarefas

 Implementar função:

def compute_goal_lambdas(team_home, team_away, league_avg_goals, home_advantage, form_home, form_away):
    ...
    return lambda_goals_home, lambda_goals_away


 Aplicar fórmula:

lambda_goals_home = μ_goals * A.attack_strength_goals * B.defense_weakness_goals * home_advantage * form_home
lambda_goals_away = μ_goals * B.attack_strength_goals * A.defense_weakness_goals * form_away


 Permitir parametrização de home_advantage.

Critérios de aceite

 Dado um confronto real, a saída de λ é numérica e razoável (ex.: não explode).

 Variações de força/forma refletem em mudanças nos λ.

Issue 8 – Implementar cálculo de λ para escanteios, faltas, cartões

Objetivo
Gerar λ para outros mercados além de gols.

Tarefas

 Implementar função para λ de escanteios:

def compute_corner_lambdas(team_home, team_away, form_home, form_away):
    ...


 Basear-se em escanteios_for_media casa/fora (ou abordagem semelhante).

 Implementar funções equivalentes para faltas e cartões, se forem usados.

Critérios de aceite

 λ de escanteios condiz com médias dos times em casa/fora.

 λ de faltas/cartões fazem sentido para times mais agressivos.

Milestone 3 – Modelo de Jogadores (impacto na partida)
Issue 9 – Calcular índices por jogador (ofensivo, cruzamento, faltas)

Objetivo
Criar métricas resumidas por jogador que representem seu impacto.

Tarefas

 Definir fórmula do índice ofensivo:

off_index = w1*gols_90 + w2*finalizacoes_90 + w3*xg_90 + w4*passes_chave_90


 Definir índice de cruzamentos/bola parada:

cross_index = w5*escanteios_cobrados_90 + w6*cruzamentos_90


 Definir índice de faltas/cartões:

foul_index = w7*faltas_cometidas_90 + w8*cartoes_por_90


 Implementar função que, dado player_stats, calcula esses índices.

 Armazenar índices em campos extras de player_stats ou em tabela auxiliar.

Critérios de aceite

 Consegue-se listar, por time, os jogadores mais ofensivos, os que mais cruzam, e os mais faltosos.

 Índices são reprodutíveis e consistentes.

Issue 10 – Agregar índices da escalação e gerar ratios

Objetivo
Dado um 11 inicial, calcular o impacto da escalação nos λ do time.

Tarefas

 Implementar função:

def compute_lineup_ratios(team_id, lineup_player_ids):
    # retorna off_ratio, cross_ratio, foul_ratio


 Passos:

Calcular off_index_lineup = soma dos off_index dos 11.

Calcular off_index_team_avg = média dos off_index do elenco.

off_ratio = off_index_lineup / off_index_team_avg

Repetir para cross_ratio e foul_ratio.

 Implementar clipping (por exemplo 0.7 a 1.3).

Critérios de aceite

 Substituir um craque ofensivo por um jogador defensivo reduz off_ratio.

 Escalações mais ofensivas geram >1.0, defensivas ≲1.0.

Issue 11 – Ajustar λ de time com base nos jogadores

Objetivo
Aplicar os ratios da escalação nos λ calculados na camada Time.

Tarefas

 Implementar função:

def adjust_lambdas_with_lineup(lambda_team, ratios):
    # aplica off_ratio, cross_ratio, foul_ratio conforme tipo de métrica


 Exemplo:

lambda_goals_home_aj   = lambda_goals_home   * off_ratio_A
lambda_corners_home_aj = lambda_corners_home * cross_ratio_A
lambda_fouls_home_aj   = lambda_fouls_home   * foul_ratio_A


 Repetir para o time visitante.

Critérios de aceite

 λ ajustados variam de forma coerente com a escalação.

 Valores não saem de faixas realistas devido ao clipping.

Milestone 4 – Distribuições & Simulador (Monte Carlo)
Issue 12 – Implementar Poisson e Negative Binomial

Objetivo
Criar funções utilitárias para trabalhar com Poisson e NegBin.

Tarefas

 Implementar poisson_pmf(k, λ) e prob_over_poisson(λ, x).

 Implementar função que calcula variance/mean por mercado (ex.: total de escanteios).

 Implementar função utilitária para escolher:

def choose_distribution(mean, var):
    return "poisson" if var/mean <= threshold else "negbin"


 Implementar Negative Binomial (usando biblioteca estatística) parametrizada por média e variância.

Critérios de aceite

 Testes unitários passando (para alguns casos simples conhecidos).

 Escolha de distribuição condizente com a variância dos dados históricos.

Issue 13 – Implementar simulador Monte Carlo de partidas

Objetivo
Dado λ ajustado para gols, escanteios etc., simular N partidas.

Tarefas

 Implementar função:

def simulate_match(lambda_params, N=50000):
    # retorna distribuição de resultados e estatísticas agregadas


 Para cada simulação:

sortear gols A / B (Poisson ou NegBin),

sortear escanteios A / B (idem),

sortear faltas / cartões, se necessário.

 Agregar:

frequência de placares,

P(over X gols),

P(over X escanteios),

P(A vence), P(empate), P(B vence).

Critérios de aceite

 Saída contém campos claros (probabilidades e contagens).

 Resultados mudam de forma coerente ao alterar λ.

Milestone 5 – RAG (Consulta / Explicação, sem previsão)
Issue 14 – Preparar dados textuais para RAG

Objetivo
Transformar dados estruturados em documentos de texto consultáveis.

Tarefas

 Criar scripts que geram “fichas” de times:

resumo das médias, forças, formas.

 Criar scripts que geram “fichas” de jogadores:

estatísticas principais, índices, histórico resumido.

 (Opcional) Criar relatórios de confrontos passados em texto.

Critérios de aceite

 Existem documentos em texto descrevendo times e jogadores.

 Conteúdo é legível e informativo.

Issue 15 – Indexar dados no mecanismo de RAG

(Depende da tecnologia que você escolher: Qdrant, Chroma, etc.)

Objetivo
Carregar as fichas de times/jogadores em um vetor store para consulta.

Tarefas

 Escolher e configurar um vetor store (ex.: Qdrant).

 Implementar indexação dos documentos de times.

 Implementar indexação dos documentos de jogadores.

 Implementar função de search(query) que retorna documentos relevantes.

Critérios de aceite

 Consultas simples (“mostrar estatísticas do Flamengo”) retornam a ficha correta.

 Consultas por jogador trazem as informações agregadas.

Issue 16 – Criação de serviço de explicação de resultados (usando RAG)

Objetivo
Permitir que o usuário faça perguntas sobre probabilidades e o sistema explique com base nos dados.

Tarefas

 Implementar endpoint ou função:

def explain_prediction(match_id_or_context, question_text):
    # usa RAG para buscar fichas relevantes e montar uma resposta textual


 Conectar:

resultados de simulação (probabilidades),

fichas de times/jogadores do RAG.

 Montar respostas explicando:

principais fatores ofensivos,

impacto de jogadores,

padrões de escanteios etc.

Critérios de aceite

 Perguntas como “por que o modelo indica muitos escanteios?” recebem respostas coerentes com os dados.

 Sistema não inventa probabilidades, só explica as já calculadas.

Milestone 6 – Integração & UX Básico
Issue 17 – Endpoint/API para simular confronto entre dois times

Objetivo
Expor uma interface programática para gerar probabilidades a partir dos times e escalações.

Tarefas

 Implementar endpoint (ex.: FastAPI):

POST /simulate com payload:

home_team_id, away_team_id

lineup_home, lineup_away (lista de player_ids)

 Pipeline do endpoint:

buscar stats de times,

calcular λ (camada time),

calcular ratios da escalação (camada jogador),

ajustar λ,

rodar simulação,

retornar probabilidades.

 Validar listas de jogadores (se pertencem ao time, se têm stats etc.).

Critérios de aceite

 Chamada ao endpoint retorna JSON com probabilidades de gols, escanteios, etc.

 Erros são tratados (ex.: time inexistente, jogador inválido).

Issue 18 – UI simples (CLI ou Web) para selecionar times e ver resultados

Objetivo
Prover uma interface básica para uso humano.

Tarefas

 Criar uma página (Streamlit ou outra) ou CLI que:

permita escolher time A e B,

escolha de escalação (11 por time),

mostre:

λ ajustados,

probabilidades principais (over/under, 1X2, escanteios).

 (Opcional) Mostrar explicação via RAG (“por que essas probabilidades?”).

Critérios de aceite

 Usuário consegue selecionar dois times, uma provável escalação e ver as probabilidades.

 A interface está consumindo a API de simulação.

Observações finais

Você pode transformar cada seção “Issue X” aqui em uma issue real no GitHub (copiar/colar título + descrição).

As milestones sugeridas:

Milestone 1 – Dados

Milestone 2 – Modelo Time

Milestone 3 – Modelo Jogadores

Milestone 4 – Simulador

Milestone 5 – RAG

Milestone 6 – Integração & UI

Recomendação prática:
Começar pelas Issues 1 a 5, depois 6–8, depois 9–11, 12–13, e só então 14+ (RAG e UI).