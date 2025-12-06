Segue um **roadmap completo**, em formato de `.md`, pensado especificamente pro teu sistema (repo `estatisticas` + RAG de jogadores) pra deixá-lo **robusto, otimizado e o mais preciso possível**.

Você pode copiar e colar direto em um arquivo tipo:
`docs/ROADMAP_COMPLETO.md`

---

````markdown
# Roadmap Completo – Sistema de Estatísticas e Previsões (Tipo Casa de Apostas)

Objetivo geral:  
Construir um sistema capaz de gerar **probabilidades pré-jogo** (gols, escanteios, chutes, props de jogador etc.) com **nível de precisão, robustez e consistência** comparável a modelos de casas de apostas profissionais, utilizando somente **dados antes da partida**.

---

## Visão Geral de Fases

1. **Dados & ETL (Fundação)**
2. **Modelagem Estatística & ML (λ, Poisson, NegBin, Props)**
3. **Engine de Apostas (Odds, EV, Mercado)**
4. **Backtest, Calibração & Ajuste de Hiperparâmetros**
5. **Produto: API, UI, RAG & Explainability**
6. **Engenharia: Qualidade, Logs, Testes & Deploy**

---

## 1. Dados & ETL (Fundação)

### 1.1. Unificação e Correção de IDs

- [ ] Criar `src/config_times.py` com:
  - `TIMES_BRASILEIRAO` único e corrigido (IDs SofaScore).
- [ ] Remover todos os dicionários duplicados em:
  - `buscar_partidas.py`
  - `buscar_escanteios.py`
- [ ] Garantir que **todos** os scrapers usam:
  ```python
  from src.config_times import TIMES_BRASILEIRAO
````

### 1.2. Filtros de Competição e Status

* [ ] Em todos os scrapers de partidas:

  * Filtrar apenas eventos com:

    * `tournament.uniqueTournament.id == 325` (Brasileirão).
    * `status.type == "finished"` (jogos encerrados).
* [ ] Aplicar o filtro **antes** de limitar pelos “N últimos jogos”.

### 1.3. Tratamento de Valores Faltantes vs Zero

* [ ] Adotar convenção:

  * `None` → dado ausente (API não retornou).
  * `0` → evento realmente não ocorreu.
* [ ] Ajustar:

  * `buscar_escanteios.py` para não excluir jogos com 0 escanteios/chutes.
* [ ] Cálculo de médias:

  * Incluir todos os zeros,
  * Ignorar apenas `None`.

### 1.4. Estrutura de Banco de Dados (Histórico Completo)

* [ ] Adicionar tabela `partidas`:

  ```sql
  CREATE TABLE partidas (
      id                SERIAL PRIMARY KEY,
      time_id           INTEGER NOT NULL,
      adversario_id     INTEGER,
      data              TIMESTAMP NOT NULL,
      mandante          BOOLEAN NOT NULL,
      gols_pro          INTEGER,
      gols_contra       INTEGER,
      escanteios_pro    INTEGER,
      escanteios_contra INTEGER,
      chutes_pro        INTEGER,
      chutes_contra     INTEGER,
      fonte_sofascore_id BIGINT,
      UNIQUE (time_id, fonte_sofascore_id)
  );
  ```

* [ ] Adaptar scrapers para:

  * Preencher/atualizar `times.json` (se ainda for útil).
  * Inserir/atualizar cada linha em `partidas`.

### 1.5. Estatísticas de Jogadores para o RAG

* [ ] Criar/expandir tabela `jogadores` ou `jogadores_stats` com:

  * minutos jogados,
  * gols/90, finalizações/90, xG/90 (se disponível),
  * escanteios cobrados,
  * posição,
  * time atual.
* [ ] ETL específico de jogadores:

  * Atualizar stats por janela (últimos 5, 10, 20 jogos).

---

## 2. Modelagem Estatística & ML

### 2.1. λ de Gols (Modelo Time vs Time)

* [ ] Calcular médias da liga:

  * `league_avg_goals` = gols por jogo na liga.
* [ ] Para cada time:

  ```python
  team.gols_por_partida     = gols_marcados_media
  team.gols_sofridos_media  = gols_sofridos_media
  team.attack_strength      = team.gols_por_partida    / league_avg_goals
  team.defense_weakness     = team.gols_sofridos_media / league_avg_goals
  ```
* [ ] Definir λ base por jogo:

  ```python
  lambda_home = league_avg_goals * home.attack_strength * away.defense_weakness
  lambda_away = league_avg_goals * away.attack_strength * home.defense_weakness
  ```

### 2.2. Ajustes Contextuais (Forma & Mando de Campo)

* [ ] Definir constantes:

  ```python
  HOME_ADVANTAGE = 1.06 ~ 1.10  # calibrar na fase 4
  ```
* [ ] Aplicar forma (já salva como `forma_multiplicador`):

  ```python
  lambda_home *= home.forma_multiplicador * HOME_ADVANTAGE
  lambda_away *= away.forma_multiplicador
  ```

### 2.3. λ de Escanteios (por Time e Total)

* [ ] Calcular `league_avg_corners` a partir do BD:

  * média de escanteios por time/jogo.
* [ ] Para cada jogo:

  ```python
  lambda_home_corners = home.escanteios_casa_media * home.forma_multiplicador
  lambda_away_corners = away.escanteios_fora_media * away.forma_multiplicador
  lambda_total_corners = lambda_home_corners + lambda_away_corners
  ```

### 2.4. Escolha Poisson vs Negative Binomial

* [ ] A partir da tabela `partidas`, construir vetores:

  * `total_goals`, `total_corners` por jogo.
* [ ] Calcular para cada mercado:

  * média (μ) e variância (σ²).
* [ ] Regra:

  * Se `σ² / μ <= 1.2` → usar Poisson.
  * Se `σ² / μ > 1.2` → usar Negative Binomial.
* [ ] Implementar funções:

  * `poisson_pmf`, `prob_over_poisson`.
  * `negbin_prob_over(mean, var, threshold)`.

### 2.5. Props de Jogador (λ_jogador)

* [ ] Definir função genérica:

  ```python
  def lambda_player_event(
      baseline_per90: float,
      expected_minutes: float,
      team_attack_multiplier: float,
      opponent_vulnerability: float
  ) -> float:
      minutes_share = expected_minutes / 90.0
      return baseline_per90 * minutes_share * team_attack_multiplier * opponent_vulnerability
  ```

* [ ] Definir:

  * `baseline_per90` = ex.: finalizações/90 do jogador.
  * `team_attack_multiplier` = gols/chutes do time vs média da liga.
  * `opponent_vulnerability` = estatística sofrida pelo adversário vs média da liga.

* [ ] Usar λ_jogador em Poisson para:

  * finalizações over X,
  * chance de marcar,
  * escanteios cobrados etc.

### 2.6. ML para melhorar λ (opcional mas forte)

* [ ] Criar features completas (time/jogo/adversário/contexto).
* [ ] Treinar modelo tipo LightGBM/XGBoost com:

  * `objective = "poisson"` para counts (gols, escanteios, chutes).
* [ ] Combinar:

  ```python
  lambda_final = w_ml * lambda_ml + w_rule * lambda_rule
  # Exemplo inicial: w_ml = 0.7, w_rule = 0.3
  ```

---

## 3. Engine de Apostas (Odds, EV, Mercado)

### 3.1. Conversão Prob → Odd Justa

* [ ] Para qualquer evento com probabilidade `p_model`:

  ```python
  odd_fair = 1.0 / p_model
  ```

### 3.2. Margem da “Casa” (Overround)

* [ ] Definir margem alvo por mercado:

  * ex.: 3–6% para mercados principais, mais alta para props.
* [ ] Ajustar probabilidades:

  * normalizar para somarem `(1 - margem)`,
  * recalcular odds.

### 3.3. Valor Esperado (Value Bet)

* [ ] Função:

  ```python
  def expected_value(prob_model: float, odd_market: float) -> float:
      # EV por unidade apostada
      return prob_model * (odd_market - 1) - (1 - prob_model)
  ```

* [ ] Na UI:

  * pedir odd da casa,
  * mostrar:

    * prob modelo,
    * odd justa,
    * EV,
    * tag (bom, neutro, ruim).

### 3.4. Regras de Amostra Mínima

* [ ] Não sugerir mercados quando:

  * jogador tem < 5–8 jogos com dados suficientes,
  * time tem poucos jogos na liga.
* [ ] Exibir avisos do tipo:

  * “Amostra pequena – interpretar com cautela”.

### 3.5. Regressão à Média para Props

* [ ] Para jogadores com pouca amostra:

  ```python
  p_final = alpha * p_model + (1 - alpha) * p_liga
  # ex.: alpha = 0.5.
  ```

---

## 4. Backtest, Calibração & Hiperparâmetros

### 4.1. Script de Backtest

* [ ] Criar `src/backtest_poisson.py` com fluxo:

  * Para cada partida histórica:

    1. Reconstruir stats dos times **usando apenas jogos anteriores**.
    2. Calcular λ de gols, escanteios etc.
    3. Gerar `p_model` para mercados:

       * Over/Under 2.5 gols,
       * Over/Under 10.5 escanteios,
       * BTTS, 1X2, etc.
    4. Comparar com o que realmente aconteceu (y=0/1).
    5. Salvar tudo em CSV ou tabela `backtest_results`.

### 4.2. Métricas de Calibração

* [ ] Calcular para cada mercado:

  * **Brier Score**,
  * Log-loss (opcional),
  * `p_bins` vs `freq_observada` (calibration curve).
* [ ] Comparar desempenho entre:

  * Apenas regra,
  * Regra + ML,
  * Poisson vs NegBin.

### 4.3. Ajuste de Hiperparâmetros

* [ ] Grid search simples usando backtest:

  * `HOME_ADVANTAGE`: {1.04, 1.06, 1.08, 1.10}
  * Peso de forma (curta vs longa),
  * Limiar de overdispersion: {1.1, 1.2, 1.3}.
* [ ] Critérios:

  * Minimizar Brier score,
  * Evitar viés sistemático (sempre over ou sempre under).

---

## 5. Produto: API, UI, RAG & Explainability

### 5.1. API de Previsões

* [ ] Implementar (por exemplo, FastAPI):

  * `GET /predictions/match/{match_id}`

    * λ de gols,
    * λ de escanteios,
    * probabilidades chave,
    * odds justas.
  * `GET /predictions/match/{match_id}/player/{player_id}`

    * props de jogador.

### 5.2. Interface (Streamlit / Web)

* [ ] Página de partida:

  * Mostrar:

    * λ_home, λ_away, λ_total_corners,
    * Over/Under com prob e odds,
    * EV quando inputar odd da casa.
* [ ] Página de jogador:

  * Finalizações esperadas,
  * Probabilidade de over X,
  * Contexto (forma, média, minutos).

### 5.3. Integração com RAG de Jogadores

* [ ] Indexar:

  * Estatísticas de jogadores,
  * Logs de previsões,
  * Explicações de modelo.
* [ ] Permitir perguntas do tipo:

  * “Por que o modelo deu 62% de chance de Over 10.5 escanteios?”
  * “Quais são os argumentos para apostar em finalizações do jogador X?”

### 5.4. Explainability Simples

* [ ] Para cada previsão, armazenar:

  * principais features,
  * decomposição de λ (base × forma × mando × adversário).
* [ ] Exibir em linguagem natural:

  * “O time A chuta 20% acima da média da liga, o adversário concede muitos chutes, e o mando de campo aumenta ainda mais o ritmo.”

---

## 6. Engenharia: Qualidade, Logs, Testes & Deploy

### 6.1. Organização de Pastas

* [ ] Estrutura sugerida:

  ```text
  src/
    config_times.py
    scrapers/
      buscar_partidas.py
      buscar_escanteios.py
    models/
      poisson_analyzer.py
      player_props.py
    services/
      odds_service.py
      value_bet.py
      features.py
    backtest/
      backtest_poisson.py
  app/
    streamlit_app.py
  docs/
    ROADMAP_COMPLETO.md
    FASE1_DADOS.md
  ```

### 6.2. Configurações (.env)

* [ ] Criar `.env` para:

  * tokens de API (SofaScore ou outras),
  * credenciais de banco.
* [ ] Garantir `.env` presente em `.gitignore`.

### 6.3. Logs e Monitoramento

* [ ] Substituir `print` por `logging`:

  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)
  ```
* [ ] Logar:

  * Erros de request,
  * Partidas ignoradas,
  * Estatísticas estranhas (outliers).

### 6.4. Testes Unitários

* [ ] Criar `tests/` com testes para:

  * funções de Poisson/NegBin,
  * cálculo de λ (cenários artificiais),
  * escolha Poisson vs NegBin,
  * EV.
* [ ] Adicionar um workflow simples de CI (GitHub Actions ou similar).

### 6.5. Deploy e Ambientes

* [ ] Separar:

  * `dev` (dados de teste, logs verbosos),
  * `prod` (logs reduzidos, seeds fixas).
* [ ] Automatizar:

  * ETL diário,
  * re-treino periódico de modelos ML,
  * geração de previsões pré-jogo.

---

## Ordem Sugerida de Implementação

1. **Fase 1 – Dados & ETL**

   * IDs, filtros de liga/status, zeros, BD de partidas e jogadores.
2. **Fase 2 – Modelagem**

   * λ de gols, escanteios, props, Poisson vs NegBin, forma & mando.
3. **Fase 4 – Backtest & Calibração**

   * Brier score, calibração, ajuste de hiperparâmetros.
4. **Fase 3 – Engine de Apostas (Odds & EV)**

   * Odds justas, margem, EV, filtros de amostra.
5. **Fase 5 – Produto & RAG**

   * API, UI, explicações de modelo, integração com RAG.
6. **Fase 6 – Engenharia**

   * estrutura, logs, testes, CI/CD.

---

Com esse roadmap implementado, o sistema passa a:

* usar dados limpos, consistentes e específicos do Brasileirão,
* estimar expectativas (λ) alinhadas com estatística real da liga,
* escolher melhor entre Poisson e NegBin para cada mercado,
* comparar probabilidades com as odds de mercado via EV,
* e ser validado continuamente com backtests e calibração.

```

Se quiser, no próximo passo posso pegar **uma fase específica** (ex.: Modelagem – Fase 2) e transformar em um **plano detalhado de implementação direta no código** (com sugestões de funções, nomes de arquivos e até trechos prontos).
::contentReference[oaicite:0]{index=0}
```
