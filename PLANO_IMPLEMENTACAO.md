# 🎯 Plano de Implementação - Sistema Profissional de Apostas

## ✅ Implementado
- [x] Sistema Poisson básico
- [x] 722 jogadores com stats
- [x] 20 times com dados de partidas
- [x] Escanteios, gols, forma
- [x] Frontend Streamlit
- [x] Repositório no GitHub
- [x] Unificação de IDs (config_times.py)
- [x] Filtros de competição (Brasileirão only)
- [x] Negative Binomial para escanteios
- [x] Value Bet Calculator (EV)
- [x] Probabilidades 1X2

## 🔨 Em Implementação (Fase 1 - Fundação de Dados)

### 1.1 Unificação de IDs [✅ CONCLUÍDO]
- [x] Criar `src/config_times.py` com IDs corretos
- [x] Atualizar buscar_partidas.py para usar config centralizada
- [x] Atualizar buscar_escanteios.py para usar config centralizada
- [x] Remover dicionários duplicados

### 1.2 Filtros de Competição [✅ CONCLUÍDO]
- [x] Filtrar apenas `tournament.uniqueTournament.id == 325` (Brasileirão)
- [x] Filtrar apenas `status.type == "finished"`
- [x] Aplicar filtros ANTES de limitar "N últimos jogos"

### 1.3 Tratamento de Valores [✅ CONCLUÍDO]
- [x] None = dado ausente (não retornado pela API) → ignorar partida
- [x] 0 = evento realmente não ocorreu → incluir em médias

## 📊 Fase 2 - Modelagem (Parcialmente Concluída)

### Fase 2A - Modelo Negative Binomial [✅ CONCLUÍDO]
```python
# Implementado em poisson_analyzer.py
if variance / mean > 1.2:
    use_negbin()
else:
    use_poisson()
```
- [x] Implementar `negbin_prob_over(mean, var, threshold)`
- [x] Aplicar em escanteios (overdispersion típica)

### Fase 2B - Calibração de Probabilidades [PENDENTE]
- [ ] Implementar Platt Scaling
- [ ] Implementar Isotonic Regression
- [ ] Criar curvas de calibração
- [ ] Aplicar ao frontend

## 💰 Fase 3 - Engine de Value Bets [✅ CONCLUÍDO]
```python
EV = prob_model * (odd_market - 1) - (1 - prob_model)
```
- [x] Função `calcular_expected_value(prob, odd)`
- [x] Função `is_value_bet(prob, odd, min_ev)`
- [x] Input de odds no frontend
- [x] Destacar value bets com EV positivo
- [x] Resumo de value bets encontradas

### Fase 4 - Backtest & Validação
- [ ] Script `src/backtest/backtest_poisson.py`
- [ ] Brier Score por mercado
- [ ] Calibration curves
- [ ] Grid search de hiperparâmetros

## 🎯 Ordem de Implementação

**Sprint 1 (Fundação):**
1. Finalizar config centralizada
2. Adicionar filtros de competição
3. Corrigir tratamento de zeros

**Sprint 2 (Modelo Robusto):**
4. Implementar Negative Binomial
5. Adicionar detecção de overdispersion
6. Calibrar probabilidades

**Sprint 3 (Value Bets):**
7. Engine de EV
8. Input de odds no frontend
9. Destacar apostas de valor

**Sprint 4 (Validação):**
10. Backtest completo
11. Métricas de calibração
12. Ajuste fino de parâmetros

## 📝 Notas Técnicas

### Negative Binomial
```python
from scipy import stats

def negbin_prob_over(mean: float, var: float, threshold: float) -> float:
    if var <= mean:
        return prob_over_poisson(mean, threshold)
    
    p = mean / var
    r = (mean ** 2) / (var - mean)
    k = int(threshold)
    return 1 - stats.nbinom.cdf(k, r, p)
```

### Calibração (Platt Scaling)
```python
from sklearn.linear_model import LogisticRegression

# Treinar em probabilidades do backtest
calibrator = LogisticRegression()
calibrator.fit(probs_model.reshape(-1, 1), outcomes)

# Aplicar
prob_calibrada = calibrator.predict_proba(prob_model)[:, 1]
```

### Expected Value
```python
# Se EV > 0 → Aposta tem valor
# Se EV > 0.05 → Value bet forte
# Se EV < 0 → Casa tem margem demais
```

## 🚀 Meta Final

Sistema que:
- ✅ Usa distribuição correta (Poisson vs NegBin)
- ✅ Probabilidades calibradas (não enviesadas)
- ✅ Detecta value bets automaticamente
- ✅ Validado por backtest rigoroso
- ✅ Brier Score < 0.20 em gols
- ✅ Brier Score < 0.25 em escanteios
