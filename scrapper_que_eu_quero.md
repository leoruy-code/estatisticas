# Especificação de Dados para o Modelo Time 1 x Time 2  
## (Gols, Escanteios e Impacto dos Jogadores)

Este documento descreve **quais estatísticas você precisa coletar e manter por rodada**  
para conseguir rodar o modelo de:

- Probabilidade de vitória / empate / derrota
- Distribuição de gols por time
- Distribuição de escanteios por time e no total
- Ajuste fino com base **na escalação (jogadores)**

---

## 1. Níveis de Dados

Você vai trabalhar com **3 níveis principais**:

1. **Partida (match-level)** → o que aconteceu no jogo.
2. **Time (team-level)** → médias e forças de ataque/defesa/escanteios.
3. **Jogador (player-level)** → contribuição de cada jogador para gols e escanteios.

Além disso, precisa da **ligação time–jogador–partida** (quem jogou em qual jogo, por quanto tempo).

---

## 2. Dados de Cada Partida (Match-Level)

Para **cada jogo** da rodada, armazene:

### 2.1. Identificação básica

- `match_id`
- `rodada` (ex.: 5, 12, 30…)
- `campeonato` (ex.: Brasileirão Série A 2024)
- `data`
- `home_team_id`
- `away_team_id`

### 2.2. Resultado e gols

- `home_goals` → gols marcados pelo mandante
- `away_goals` → gols marcados pelo visitante

Opcional (ajudam muito em modelos mais avançados):

- `home_xg` → expected goals (se tiver)
- `away_xg`

### 2.3. Escanteios

- `home_corners` → escanteios a favor do mandante
- `away_corners` → escanteios a favor do visitante

Se quiser ser mais detalhado (futuro):

- `home_corners_1t`, `home_corners_2t`
- `away_corners_1t`, `away_corners_2t`

### 2.4. Informações de contexto (opcional, mas útil)

- `home_shots` / `away_shots` → finalizações
- `home_shots_on_target` / `away_shots_on_target`
- `home_possession` / `away_possession`
- `stadium`
- `referee_id` (se quiser depois modelar árbitro)

---

## 3. Estatísticas Agregadas por Time (Team-Level)

A partir dos dados das partidas, você calcula **médias por time**, separando:

- **mandante** e **visitante**, pois o mando influencia muito.

### 3.1. Gols por time

Para cada `team_id`:

- `matches_home` → jogos como mandante
- `matches_away` → jogos como visitante

- `goals_for_home_total`
- `goals_against_home_total`
- `goals_for_away_total`
- `goals_against_away_total`

E as **médias**:

- `goals_for_home_avg` = `goals_for_home_total / matches_home`
- `goals_against_home_avg` = `goals_against_home_total / matches_home`
- `goals_for_away_avg` = `goals_for_away_total / matches_away`
- `goals_against_away_avg` = `goals_against_away_total / matches_away`

Essas médias serão a base para:

- **força de ataque** (gols a favor)
- **força de defesa** (gols contra)

### 3.2. Escanteios por time

Mesma lógica:

- `corners_for_home_total`
- `corners_against_home_total`
- `corners_for_away_total`
- `corners_against_away_total`

E médias:

- `corners_for_home_avg`
- `corners_against_home_avg`
- `corners_for_away_avg`
- `corners_against_away_avg`

Essas médias alimentam o modelo de **escanteios esperados**.

### 3.3. Janelas temporais (para suavizar)

Para ter estatísticas mais “afinadas”, vale ter esses números:

- **na temporada inteira**
- **nos últimos N jogos** (ex.: últimos 5, 10)

Exemplo: `goals_for_home_avg_last5`, `corners_for_away_avg_last10`, etc.

---

## 4. Dados por Jogador (Player-Level)

Agora vem a parte chave da sua lógica:  
**o time é resultado dos jogadores, e a escalação muda.**

### 4.1. Cadastro do jogador

- `player_id`
- `nome`
- `posicao` (ex.: GK, ZAG, LAT, VOL, MEI, ATA)
- `current_team_id` (time atual)

### 4.2. Estatísticas básicas por jogador (acumuladas)

Idealmente **por 90 minutos** (ou por jogo), para normalizar:

- `minutes_played_total`
- `matches_played` (jogos com participação)

#### Ofensivas (relacionadas a gols e escanteios)

- `goals_total`
- `shots_total`
- `shots_on_target_total`
- `assists_total` (opcional)
- `xg_total` (se tiver)

- `corners_taken_total` (escanteios cobrados)
- `crosses_total` (cruzamentos)

Você pode derivar taxas:

- `goals_per_90`
- `shots_per_90`
- `xg_per_90`
- `corners_taken_per_90`

#### Defensivas (impactam gols sofridos e escanteios contra)

- `tackles_total`
- `interceptions_total`
- `clearances_total`
- `aerial_duels_won_total`

Taxas:

- `tackles_per_90`
- `interceptions_per_90`
- etc.

### 4.3. Estatísticas por jogador **por partida**

Você precisa também, para **cada match_id + player_id**:

- `team_id`
- `minutes_played` na partida
- `goals`
- `shots`
- `xg` (se tiver)
- `corners_taken`
- `crosses`
- `position_in_match` (se mudou de posição pode ignorar no começo)

Essa relação vai permitir:

- saber **quem realmente jogou** em cada partida,
- calcular médias recentes por jogador,
- e montar a **força da escalação**.

---

## 5. Ligação Time–Jogador–Partida (Escalação)

Tabela de escalação (por jogo):

- `match_id`
- `team_id`
- `player_id`
- `is_starter` (true/false)
- `minutes_played`
- (opcional) `substituted_in_minute` / `substituted_out_minute`

Isso permite:

- Montar o time-base real que atuou em cada partida.
- Quando você simular um novo jogo, você informa a **escalação prevista** (lista de `player_id`), e o modelo consegue usar os ratings dos jogadores.

---

## 6. Estatísticas Derivadas para o Modelo (Ratings)

Com as estatísticas acima, você gera **features mais compactas** para alimentar o modelo.

### 6.1. Ratings de time

A partir das médias que você já calculou:

- `attack_rating_home` → baseado em `goals_for_home_avg`
- `defense_rating_home` → baseado em `goals_against_home_avg`
- `attack_rating_away`
- `defense_rating_away`

Para escanteios:

- `corners_attack_rating_home` → baseado em `corners_for_home_avg`
- `corners_defense_rating_home` → baseado em `corners_against_home_avg`
- (mesmo para visitante)

Você pode normalizar esses ratings em torno da média da liga.

### 6.2. Ratings de jogador

A partir das taxas por 90 minutos:

- `attack_player_rating`
  - função de `goals_per_90`, `shots_per_90`, `xg_per_90`
- `defense_player_rating`
  - função de `tackles_per_90`, `interceptions_per_90`, etc.
- `corners_player_rating`
  - função de `corners_taken_per_90`, `crosses_per_90`

---

## 7. Como usar isso para um jogo específico (lógica final)

Para **Time 1 x Time 2** em uma rodada futura:

1. **Definir o contexto do jogo**
   - quem é mandante (`home_team_id`)
   - quem é visitante (`away_team_id`)

2. **Calcular parâmetros base de time**
   - usar:
     - `attack_rating_home` do mandante,
     - `defense_rating_away` do visitante,
     - e vice-versa.
   - a partir disso, gerar:
     - `lambda_gols_time1`
     - `lambda_gols_time2`
     - `kappa_corners_time1`
     - `kappa_corners_time2`

3. **Se houver escalação prevista**:
   - pegar lista de `player_id` de cada time.
   - calcular:
     - `attack_lineup_rating_time1` = média dos `attack_player_rating` dos 11.
     - `defense_lineup_rating_time2` = média dos `defense_player_rating` etc.
   - ajustar `lambda` e `kappa` com base nessa diferença entre:
     - rating da escalação vs rating médio do time.

4. **Rodar o modelo de probabilidade**
   - usar `lambda_gols` para gerar distribuição de gols (Poisson).
   - usar `kappa_corners` para escanteios.
   - opcional: usar Monte Carlo combinando tudo (gols + escanteios de ambos).

5. **Resultado**
   - Probabilidades:
     - vitória / empate / derrota
   - Distribuição de gols:
     - 0,1,2,3… por time
   - Distribuição de escanteios:
     - por time e total (faixas mais prováveis).

---

## 8. Resumo rápido das estatísticas mínimas necessárias

Se quiser um “checklist” conciso:

**Por partida:**

- IDs: `match_id`, `rodada`, `campeonato`, `data`, `home_team_id`, `away_team_id`
- Gols: `home_goals`, `away_goals`
- Escanteios: `home_corners`, `away_corners`

**Por time (derivado das partidas):**

- Jogos mandante/visitante
- Médias:
  - `goals_for_home_avg`, `goals_against_home_avg`
  - `goals_for_away_avg`, `goals_against_away_avg`
  - `corners_for_home_avg`, `corners_against_home_avg`
  - `corners_for_away_avg`, `corners_against_away_avg`

**Por jogador (acumulado):**

- `player_id`, `current_team_id`, `posicao`
- `minutes_played_total`, `matches_played`
- `goals_total`, `shots_total`, `corners_taken_total`, `xg_total` (se tiver)
- taxas por 90: `goals_per_90`, `shots_per_90`, `corners_taken_per_90`

**Por jogador em cada partida:**

- `match_id`, `team_id`, `player_id`
- `minutes_played`
- `goals`, `shots`, `corners_taken`

Com isso, você tem **tudo o que precisa** para:

- montar o modelo Time 1 vs Time 2,
- ajustar por escalação,
- e construir o sistema de probabilidades que você quer.
