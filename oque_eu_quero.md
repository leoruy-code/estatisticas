# Sistema de Previsão Estatística com RAG (sem LLM preditivo)

Este documento define **como implementar o sistema de previsão** com base em:

- estatísticas **locais** (times + jogadores),
- **modelagem estatística** (Poisson / NegBin),
- uso de **RAG apenas para consulta/explicação**, **não para previsão**.

Nada de LLM tomando decisão de probabilidade aqui – o coração do sistema é **matemática + dados**.

---

## 1. Objetivo do Sistema

1. Popular e manter atualizadas as estatísticas de:
   - **todos os jogadores** de todos os times;
   - **todos os times** (médias dos últimos confrontos, escanteios, cartões, faltas etc.).
2. Ter duas camadas de análise:
   - **Camada Time**: modelo estatístico por time (força ofensiva/defensiva, médias agregadas).
   - **Camada Jogador**: impacto dos jogadores escalados nas estatísticas esperadas do jogo.
3. Selecionar **dois times** e simular um confronto:
   - calcular λ (expectativas) para gols, escanteios, cartões etc.;
   - rodar simulações (Monte Carlo) para obter probabilidades.
4. Usar **RAG**:
   - para consultar estatísticas, explicar previsões, navegar pelos dados;
   - **não** para gerar as probabilidades em si.

---

## 2. Arquitetura Geral

### 2.1. Camadas principais

1. **Camada de Dados (local)**
   - Banco de dados + ETL.
   - Armazena partidas, stats de times, stats de jogadores.

2. **Camada de Modelagem Estatística**
   - Cálculo de forças de times (attack/defense).
   - Cálculo de λ para cada métrica (gols, escanteios, cartões, faltas).
   - Ajustes com base na escalação (impacto dos jogadores).
   - Simulador Monte Carlo para gerar distribuição de resultados e probabilidades.

3. **Camada RAG (consulta / explicação)**
   - Indexa:
     - fichas de times,
     - fichas de jogadores,
     - relatórios de partidas,
     - documentos de modelo.
   - Responde perguntas em linguagem natural, usando apenas os dados locais.

---

## 3. Modelagem dos Dados

### 3.1. Tabela de Times (`teams` e `team_stats`)

**Tabela `teams`** (meta):

- `id`
- `nome`
- `liga`
- `sofascore_id` (ou outro ID externo)
- `ativo` (boolean)

**Tabela `team_stats`** (agregado, por temporada ou janela):

- `team_id`
- `jogos_total`
- `jogos_casa`
- `jogos_fora`
- `gols_marcados_media`
- `gols_sofridos_media`
- `escanteios_for_media`
- `escanteios_against_media`
- `chutes_for_media`
- `chutes_against_media`
- `cartoes_for_media`
- `cartoes_against_media`
- `faltas_for_media`
- `faltas_against_media`
- `forma_multiplicador` (últimos 5 jogos vs média da temporada)
- `updated_at`

Observação:  
Você pode ter mais de uma linha por time, por exemplo por janela:

- temporada toda,
- últimos 10 jogos,
- últimos 5 jogos etc.

---

### 3.2. Tabela de Partidas (`matches` e `team_games`)

**Tabela `matches`**:

- `id`
- `data`
- `home_team_id`
- `away_team_id`
- `home_goals`
- `away_goals`
- `home_corners`
- `away_corners`
- `home_shots`
- `away_shots`
- `home_fouls`
- `away_fouls`
- `home_cards`
- `away_cards`
- `status` (finished, ongoing etc.)
- `liga`
- `fonte_event_id` (id do evento na origem)

**Tabela `team_games`** (opcional, derivada de `matches`):

Uma linha por time por jogo, facilitando queries:

- `match_id`
- `team_id`
- `opponent_id`
- `mandante` (bool)
- `gols_pro`
- `gols_contra`
- `escanteios_pro`
- `escanteios_contra`
- `chutes_pro`
- `chutes_contra`
- `faltas_pro`
- `faltas_contra`
- `cartoes_pro`
- `cartoes_contra`

---

### 3.3. Tabela de Jogadores (`players` e `player_stats`)

**Tabela `players`**:

- `id`
- `nome`
- `time_atual_id`
- `posicao` (CF, LW, RW, MC, VOL, ZAG, LD, LE etc.)
- `nascimento` (opcional)
- `ativo` (bool)

**Tabela `player_stats`** (por jogador, agregada):

- `player_id`
- `minutos_total`
- `jogos_total`
- `minutos_por_jogo`
- `gols_total`
- `gols_por_90`
- `finalizacoes_total`
- `finalizacoes_por_90`
- `assistencias_total`
- `xg_total` (se disponível)
- `xg_por_90`
- `passes_chave_por_90`
- `escanteios_cobrados_por_90`
- `cruzamentos_por_90`
- `faltas_cometidas_por_90`
- `faltas_sofridas_por_90`
- `cartoes_amarelos_total`
- `cartoes_vermelhos_total`
- `periodo` (ex.: temporada, últimos 10 jogos etc.)
- `updated_at`

---

## 4. Modelo Estatístico – Camada Time

### 4.1. Cálculo da força de ataque/defesa

Primeiro, calcular a média da liga:

- `league_avg_goals_for` = média de gols marcados por time/jogo.
- `league_avg_goals_against` = deve ser igual, mas você também pode armazenar.

Para cada time:

```python
attack_strength_goals = team.gols_marcados_media / league_avg_goals_for
defense_weakness_goals = team.gols_sofridos_media / league_avg_goals_against
```

Você pode fazer isso para outras métricas também (escanteios, chutes, cartas etc.):

```python
attack_strength_corners   = team.escanteios_for_media / league_avg_corners_for
defense_weakness_corners  = team.escanteios_against_media / league_avg_corners_against
```

---

### 4.2. Expectativa de gols (λ_gols)

Definir:

- `μ_goals` = média de gols da liga por time/jogo (ou por jogo, ajusta-se depois).

Para confronto entre **Time A (casa)** e **Time B (fora)**:

```python
lambda_goals_home = μ_goals * A.attack_strength_goals * B.defense_weakness_goals * home_advantage * form_A
lambda_goals_away = μ_goals * B.attack_strength_goals * A.defense_weakness_goals * form_B
```

Onde:

- `home_advantage` ≈ 1.06 – 1.10 (ajustado depois via backtest),
- `form_A` e `form_B` vêm de `forma_multiplicador` (últimos 5 vs média longa).

---

### 4.3. Expectativa de escanteios, cartões, faltas (λ_outros)

Você pode escolher:

- modelo multiplicativo (como gols), ou
- modelo mais simples baseado em médias casa/fora.

Exemplo simples para **escanteios**:

```python
lambda_corners_home = A.escanteios_for_casa_media * form_A
lambda_corners_away = B.escanteios_for_fora_media * form_B
lambda_corners_total = lambda_corners_home + lambda_corners_away
```

Para cartões, você pode usar:

```python
lambda_cards_home = A.cartoes_for_media * form_A * cards_ref_multiplier
lambda_cards_away = B.cartoes_for_media * form_B * cards_ref_multiplier
```

Onde `cards_ref_multiplier` poderia depender do árbitro (se decidir incluir isso).

---

## 5. Modelo Estatístico – Camada Jogador (impacto na partida)

Ideia: a escalação (quem joga) muda a força do time.

### 5.1. Índices por jogador

Para cada jogador, calcule alguns índices:

- **Índice ofensivo**:
  - `off_index = w1 * gols_por_90 + w2 * finalizacoes_por_90 + w3 * xg_por_90 + w4 * passes_chave_por_90`
- **Índice cruzamento / bola parada**:
  - `cross_index = w5 * escanteios_cobrados_por_90 + w6 * cruzamentos_por_90`
- **Índice disciplina / faltas**:
  - `foul_index = w7 * faltas_cometidas_por_90 + w8 * cartoes_por_90`

Os pesos `w1...w8` podem ser ajustados empiricamente (ex.: todos 1 no início).

---

### 5.2. Índices agregados da escalação

Dada uma escalação de 11 jogadores para o Time A:

```python
off_index_lineup_A   = sum(off_index_jogador_i for i in titulares_A)
cross_index_lineup_A = sum(cross_index_jogador_i for i in titulares_A)
foul_index_lineup_A  = sum(foul_index_jogador_i for i in titulares_A)
```

Também calcule índices “médios” do elenco:

```python
off_index_team_avg   = media(off_index_jogadores_do_time)
cross_index_team_avg = media(cross_index_jogadores_do_time)
foul_index_team_avg  = media(foul_index_jogadores_do_time)
```

Então:

```python
off_ratio_A   = off_index_lineup_A   / off_index_team_avg
cross_ratio_A = cross_index_lineup_A / cross_index_team_avg
foul_ratio_A  = foul_index_lineup_A  / foul_index_team_avg
```

Faça o mesmo para o Time B (`off_ratio_B`, `cross_ratio_B`, `foul_ratio_B`).

---

### 5.3. Ajuste dos λ do time com base nos jogadores

Agora, ajuste as expectativas calculadas na camada Time.

Exemplo para **gols**:

```python
lambda_goals_home_aj = lambda_goals_home * off_ratio_A
lambda_goals_away_aj = lambda_goals_away * off_ratio_B
```

Para **escanteios**:

```python
lambda_corners_home_aj = lambda_corners_home * cross_ratio_A
lambda_corners_away_aj = lambda_corners_away * cross_ratio_B
```

Para **faltas/cartões**:

```python
lambda_fouls_home_aj = lambda_fouls_home * foul_ratio_A
lambda_fouls_away_aj = lambda_fouls_away * foul_ratio_B
```

Lembre de:

- Colocar limites (clipping) para os ratios, tipo entre 0.7 e 1.3,  
  para não explodir quando a amostra for pequena.

---

## 6. Distribuições e Simulação (Monte Carlo)

### 6.1. Escolha de distribuição

Para cada evento (gols, escanteios, faltas, cartões):

1. Calcule, com dados históricos:
   - média `μ`,
   - variância `σ²`.
2. Critério simples:
   - Se `σ² / μ <= 1.2` → use **Poisson**.
   - Se `σ² / μ > 1.2` → use **Negative Binomial**.

**Poisson:**

\[
P(k; \lambda) = \frac{e^{-\lambda} \lambda^k}{k!}
\]

Probabilidade de over X:

```python
def prob_over_poisson(lmbda, x):
    return 1 - sum(poisson_pmf(k, lmbda) for k in range(0, x+1))
```

**Negative Binomial (quando há overdispersão):**

Usando média e variância:

- mean = μ,
- var  = σ²,

Converter para parâmetros de biblioteca (n, p) (você fará isso no código usando scipy/stats, por exemplo).

---

### 6.2. Simulador Monte Carlo

Fluxo:

1. Receber:
   - times A e B,
   - escalações (lista de jogadores A e B).
2. Calcular:
   - λ_gols_home_aj, λ_gols_away_aj,
   - λ_corners_home_aj, λ_corners_away_aj,
   - λ_fouls_home_aj, λ_fouls_away_aj,
   - etc.
3. Definir número de simulações:  
   ex.: `N = 50_000`.

4. Loop de simulação:

```python
for i in range(N):
    gols_A = sample_goals(lambda_goals_home_aj)   # Poisson ou NegBin
    gols_B = sample_goals(lambda_goals_away_aj)
    esc_A  = sample_corners(lambda_corners_home_aj)
    esc_B  = sample_corners(lambda_corners_away_aj)
    # ... etc ...

    registrar_resultado(...)
```

5. Ao final:
   - `P(Over 2.5 gols)` = nº simulações com (gols_A + gols_B > 2.5) / N  
   - `P(Over 10.5 escanteios)` = nº simulações com (esc_A + esc_B > 10.5) / N  
   - `P(A vence)` = nº simulações com `gols_A > gols_B` / N  
   - etc.

Você gera um **conjunto de probabilidades puramente estatísticas**, sem usar LLM.

---

## 7. Uso de RAG (sem LLM preditivo)

Você disse: *“LLM é inútil no momento, vamos usar RAG e a fórmula”*.

A forma saudável de usar RAG aqui é:

### 7.1. O que indexar no RAG

- Dados estruturados transformados em texto:
  - Perfil de cada time (forças, fraquezas, médias).
  - Perfil de cada jogador (índices ofensivos, cruzamentos, disciplina).
  - Relatórios de confrontos passados (texto gerado uma vez a partir de stats).
  - Documentação do modelo (explicando fórmulas, significado de λ etc.).

### 7.2. Para que usar RAG

- Explicar resultados:
  - “Por que a probabilidade de over 10.5 escanteios está alta?”
- Comparar jogadores:
  - “Quais jogadores mais influenciam cruzamentos no time X?”
- Dar contexto:
  - “Qual é o estilo do time X nas últimas 10 partidas (ofensivo, defensivo, cruzamentos etc.)?”

O **RAG não gera probabilidade**, apenas usa o resultado do motor estatístico + dados locais para responder perguntas em linguagem natural.

---

## 8. Resumo da Implementação

1. **Organizar banco de dados**:
   - `teams`, `team_stats`, `players`, `player_stats`, `matches` (e opcionalmente `team_games`).

2. **ETL**:
   - Scrapers trazem dados brutos → consolidar em stats por time e jogador.

3. **Camada Time**:
   - Calcular médias da liga.
   - Calcular forças de ataque/defesa.
   - Calcular λ base de gols, escanteios, faltas, cartões para um confronto.

4. **Camada Jogador**:
   - Calcular índices por jogador.
   - Agregar pelos 11 titulares.
   - Ajustar λ do time conforme perfil da escalação.

5. **Simulador**:
   - Definir distribuição (Poisson/NegBin) por métrica.
   - Simular N partidas (Monte Carlo).
   - Estimar probabilidades de eventos (over/under, resultado, etc.).

6. **RAG**:
   - Indexar fichas e relatórios.
   - Permitir consultas e explicações sem interferir na matemática do modelo.

---

Com isso, você terá um sistema:

- **100% baseado em dados locais e estatística** para previsão,
- **determinístico, auditável e reprodutível**,
- com **RAG apenas como camada de inteligência de consulta/explicação**,
- pronto para, no futuro, se você quiser, receber um LLM só como “analista”, nunca como “oráculo” de probabilidade.
