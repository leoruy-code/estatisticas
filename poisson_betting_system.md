
# Guia Prático — Estimar números aproximados (λ) e gerar probabilidades próximas das casas de apostas
**Autor:** Para seu RAG  
**Objetivo:** receita prática e reproduzível para obter *números aproximados* (λ) e **probabilidades pré-jogo** tão próximas quanto possível das usadas por casas de apostas, sem dados em tempo real.

---

## 1. Premissas
- Apenas *dados pré-jogo*: históricos, forma, escalação confirmada, clima previsto e árbitro.  
- Objetos alvo: gols (over/under), escanteios (over/under), props de jogador (gols, finalizações, escanteios participados).  
- Precisão buscada: aproximar a expectativa média (λ) e probabilidade justa; depois aplicar margem da casa.

---

## 2. Pipeline resumido (passos para chegar nos números)
1. **Coleta**: carregar históricos de partidas (por time e por jogador), escalações, árbitros e clima.  
2. **Limpeza**: remover outliers, partidas sem dados e normalizar por 90 minutos.  
3. **Features**: calcular rolling windows (5/10/30 jogos), home/away, attack/defense strength, xG/xGA, corners per90, shots per90, involvement per90.  
4. **Estimativa inicial de λ**: combinar regras analíticas simples com saída de regressão (LightGBM, objective=poisson).  
5. **Ajustes contextuais**: multiplicadores por casa/fora, árbitro, clima e escalação.  
6. **Distribuição**: aplicar Poisson ou Negative Binomial para gerar P(k) e somas (over/under).  
7. **Calibração**: Platt/Isotonic em conjunto de validação; verificar Brier score.  
8. **Conversão em odds**: odd_fair = 1 / prob ; aplicar margem (vig) proporcional.  
9. **Backtest**: simular apostas com odds históricas para ajustar parâmetros.

---

## 3. Como calcular λ (receita prática)

### 3.1 Método por regras (rápido — bom baseline)
- Para **escanteios (total)**:
  ```
  lambda_corners = avg_corners_for_home_team + avg_corners_for_away_team
  ```
  Onde `avg` são médias por 90 dos últimos N jogos (use 10 e 30 windows e combine: weight maior para janela curta para capturar forma).

- Para **gols (por time)** (modelo multiplicativo simples):
  ```
  lambda_home = league_avg_goals * attack_strength_home * defense_weakness_away
  lambda_away = league_avg_goals * attack_strength_away * defense_weakness_home
  ```
  Onde:
  ```
  attack_strength_team = team_avg_goals_for / league_avg_goals_for
  defense_weakness_team = team_avg_goals_against / league_avg_goals_against
  ```

- Para **props por jogador** (ex.: finalizações por jogo):
  ```
  lambda_player = baseline_player_per90 * minutes_share_expected * team_attack_multiplier * opponent_vulnerability
  ```

### 3.2 Método ML (recomendado para maior precisão)
- Treine um regressor de contagem (LightGBM com `objective="poisson"`) cujo target é o count (ex.: `corners_total`, `home_goals`, `player_shots`).
- Input: features agregadas (time/jogador/adversário/contexto).
- Saída: `lambda_pred` (valor esperado).

Exemplo:
```python
import lightgbm as lgb
train_data = lgb.Dataset(X_train, label=y_train)
params = {"objective":"poisson", "metric":"rmse", "learning_rate":0.05}
bst = lgb.train(params, train_data, num_boost_round=800)
lambda_pred = bst.predict(X_test)
```

Combine ML e regras: `lambda_final = w_ml * lambda_ml + w_rule * lambda_rule` (p.ex. 0.7/0.3).

---

## 4. Ajustes e multiplicadores (valores práticos sugeridos)
Use multiplicadores empíricos com valores iniciais e ajuste por backtest.

- Home advantage (para eventos ofensivos): `home_mult = 1.08` (8% mais criação em média)
- Forma recente (últimos 5 jogos): calcular ratio `form_mult = 1 + 0.2*(zscore_of_recent_vs_season)` (clip entre 0.8 e 1.2)
- Árbitro (para cartões/escanteios): se árbitro médio dá +10% escanteios, `ref_mult = 1.10`
- Escalação (titular ausente): `starter_absence_mult = 0.75` para reduzir expectativa do jogador em falta
- Clima (chuva/vento): `bad_weather_mult = 0.95` (pouco impacto em gols, mais em crosses/escanteios dependendo do contexto)
- Opponent vulnerability: `opp_mult = opponent_stat / league_avg_stat` (por exemplo, opponent_corners_allowed / league_avg_corners_allowed)

Aplicar limites (min/max) para evitar multiplicadores extremos.

---

## 5. Converter λ para probabilidades (Poisson / NegBin)

### Poisson — probabilidade exata:
\[
P(k) = \frac{e^{-\lambda}\lambda^{k}}{k!}
\]

Probabilidade Over X:
```python
def prob_over_poisson(lamb, x):
    # P(k >= x+1)
    return 1 - sum(poisson_pmf(i, lamb) for i in range(0, x+1))
```

### Negative Binomial — se observar overdispersion
- Estime um parâmetro `disp` (dispersion) a partir do histórico (var/mean ratio).
- Use `scipy.stats.nbinom` ou glm.nb em statsmodels.

Recomendação prática:
- Se `variance / mean > 1.2`, usar Negative Binomial.

---

## 6. Exemplo completo (escanteios total — calcular prob Over 10.5)

1. Coletar:
   - `avg_corners_home_last10 = 5.4`
   - `avg_corners_away_last10 = 5.1`
2. Regras:
   ```
   lambda_rule = 5.4 + 5.1 = 10.5
   ```
3. ML:
   - `lambda_ml = 10.8` (saída do modelo)
4. Combine:
   ```
   lambda_final = 0.7*10.8 + 0.3*10.5 = 10.71
   ```
5. Ajustes (home mult 1.08, referee mult 1.0, weather 0.98):
   ```
   lambda_adj = 10.71 * 1.08 * 1.0 * 0.98 = 11.36
   ```
6. Prob Over 10.5 (i.e., P(k >= 11)) usando Poisson com λ=11.36:
   - calcule P(k<=10) e subtraia de 1
7. Odd justa:
   ```
   prob_over = 1 - cdf_poisson(10, 11.36)
   odd_fair = 1 / prob_over
   ```
8. Aplicar vig (ex.: margem 5%): normalizar probabilidades e recomputar odds.

---

## 7. Calibração e validação (como garantir aproximação)
- Separe dados: treino / validação / teste por temporadas para evitar vazamento temporal.  
- Calibre probabilidades: Platt scaling (sigmoid) ou isotonic regression sobre probabilidades previstas vs resultado real.  
- Métricas: Brier score, logloss, ganho P/L simulado (com estratégia de apostas simples).  
- Monitor: medir `mean(predicted_prob) vs observed_frequency` por buckets (0-0.1, 0.1-0.2, ...).

---

## 8. Código utilitário essencial

### Funções Poisson
```python
import math
from math import exp, factorial

def poisson_pmf(k, lamb):
    return math.exp(-lamb) * (lamb**k) / math.factorial(k)

def prob_over_poisson(lamb, x):
    # prob of >= x+1
    cdf = sum(poisson_pmf(i, lamb) for i in range(0, x+1))
    return 1 - cdf
```

### Calcular variance/mean e escolher distribuição
```python
def choose_distribution(mean, variance):
    if variance / mean > 1.2:
        return "negbin"
    return "poisson"
```

---

## 9. Recomendações práticas para chegar mais perto das casas
1. **Combine várias janelas** (mais peso para janela curta) em vez de usar apenas a média total da temporada.  
2. **Use modelos de ML (poisson objective)** para capturar interações complexas.  
3. **Backtest e ajuste de pesos (w_ml, w_rule)** visando minimizar Brier/logloss e maximizar P/L simulado.  
4. **Inclua features de matchup** (por exemplo, quantos cruzamentos o adversário sofre por jogo se você está calculando escanteios criados por cruzamentos).  
5. **Use Negative Binomial quando houver overdispersion**. Casas grandes modelam dispersão por liga.  
6. **Calibre as probabilidades** para evitar vieses sistemáticos.  

---

## 10. Checklist rápido para gerar λ confiável
- [ ] Dados limpos e normalizados (por 90)  
- [ ] Rolling windows 5/10/30 implementadas  
- [ ] Model ML treinado com objective poisson  
- [ ] Regras heurísticas implementadas (baseline)  
- [ ] Multiplicadores contextuais e limites aplicados  
- [ ] Escolha de distribuição (Poisson/NegBin) por mercado  
- [ ] Calibração de probabilidades com dataset holdout  
- [ ] Backtest em seasons out-of-sample

---

## 11. Anexos técnicos (exemplos de parâmetros iniciais)
- Weights combine ML + rule: `w_ml=0.7, w_rule=0.3`  
- Home advantage: `1.06 - 1.10` (ajustar por liga)  
- Dispersion threshold: `variance/mean > 1.2` → usar NegBin  
- Margem inicial (vig): `3% - 6%` para mercados populares; maiores para props.

---

## 12. Próximos passos sugeridos
1. Me envie um sample CSV (ex.: `matches.csv` + `player_stats.csv`) que você usa no RAG. Eu adapto os scripts para suas colunas.  
2. Posso gerar código completo (ETL + treino + previsão + small API) e um notebook com backtests.  
3. Se quiser, crio uma pipeline pronta com dados sintéticos para você rodar localmente.

---
