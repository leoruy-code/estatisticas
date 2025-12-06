# 🛡️ Web Scraper Seguro - Guia de Uso

## 📋 Características Implementadas

### 1. **Rate Limiting**
- Limite de **15 requests por minuto** (conservador)
- Delay aleatório entre **2-5 segundos** entre cada request
- Aguarda automaticamente se atingir o limite

### 2. **Anti-Bloqueio**
```python
✅ Rotação de User-Agents (4 diferentes)
✅ Headers realistas (Accept, Language, DNT)
✅ Session persistente com cookies
✅ Delays aleatórios
✅ Retry com backoff exponencial
```

### 3. **Cache Local**
- Cache de **24 horas** para respostas
- Evita requests duplicados
- Armazenado em `data/cache/`

### 4. **Tratamento de Erros**
- **3 tentativas** com retry automático
- Backoff exponencial: 1s → 2s → 4s
- Detecta e aguarda quando recebe `429 Too Many Requests`

## 🚀 Como Usar

### Exemplo 1: Buscar fotos de um time
```bash
cd "/Users/leo/RAG ESTATISTICAS"
source venv/bin/activate
python src/atualizar_com_scraper.py Flamengo
```

### Exemplo 2: Buscar fotos de múltiplos times
```bash
python src/atualizar_com_scraper.py Flamengo Palmeiras Corinthians
```

### Exemplo 3: Atualizar TODOS os times
```bash
python src/atualizar_com_scraper.py
```

## ⚙️ Configurações Ajustáveis

Em `src/scraper_seguro.py`:

```python
# Delays entre requests
MIN_DELAY = 2  # Aumentar para 3-4 se houver bloqueios
MAX_DELAY = 5  # Aumentar para 7-10 se houver bloqueios

# Limite de requests
REQUESTS_PER_MINUTE = 15  # Reduzir para 10 se necessário

# Timeout
TIMEOUT = 30  # Aumentar se conexão for lenta

# Retries
MAX_RETRIES = 3  # Aumentar para 5 se site for instável
```

## 📊 Estimativa de Tempo

Para **20 times** (Brasileirão completo):

| Configuração | Tempo Estimado |
|--------------|----------------|
| 15 req/min | ~20-25 minutos |
| 10 req/min | ~30-35 minutos |
| 5 req/min | ~60-70 minutos |

**Recomendação**: Executar em lotes de 5 times por vez.

## 🎯 Estratégias de Uso

### 1. **Uso Conservador** (Recomendado)
```bash
# Fazer 1 time por vez, verificar se funcionou
python src/atualizar_com_scraper.py Flamengo
python src/atualizar_com_scraper.py Palmeiras
python src/atualizar_com_scraper.py Botafogo
```

### 2. **Uso em Lotes**
```bash
# 5 times por vez (25-30 min cada lote)
python src/atualizar_com_scraper.py Flamengo Palmeiras Botafogo "São Paulo" Corinthians
# Aguardar 30-60 minutos antes do próximo lote
python src/atualizar_com_scraper.py "Atlético-MG" Grêmio Fluminense Cruzeiro Vasco
```

### 3. **Uso Automatizado** (Cuidado!)
```bash
# Todos os 20 times de uma vez (~20-25 min total)
# Usar apenas se cache estiver vazio e precisar urgente
python src/atualizar_com_scraper.py
```

## 🚨 Sinais de Bloqueio

Se você ver:
- ❌ Muitos erros `429 Too Many Requests`
- ❌ Timeouts frequentes
- ❌ Captchas ou redirecionamentos

**Solução**:
1. Parar o script (Ctrl+C)
2. Aguardar 30-60 minutos
3. Aumentar delays: `MIN_DELAY = 4`, `MAX_DELAY = 8`
4. Reduzir taxa: `REQUESTS_PER_MINUTE = 8`
5. Tentar novamente

## 📁 Estrutura do Cache

```
data/cache/
├── a1b2c3d4e5f6.json  # Hash MD5 da URL
├── f6e5d4c3b2a1.json
└── ...
```

Cada arquivo contém:
- URL original
- Timestamp
- Conteúdo da resposta

**Limpar cache**: `rm -rf data/cache/*`

## 🔍 Monitoramento

O script mostra em tempo real:
```
✅ Request #1: https://api.sofascore.com/api/v1/team/5981/players...
📦 Cache hit: https://api.sofascore.com/api/v1/team/5957/players...
⏳ Rate limit: aguardando 3.2s...
⚠️  Rate limit (429), aguardando 20s...
✅ Flamengo: foto adicionada
```

## 💡 Dicas

1. **Executar em horários fora de pico** (madrugada, fins de semana)
2. **Usar cache ao máximo** - re-executar no mesmo dia usa cache
3. **Começar com 1 time** para testar configurações
4. **Verificar robots.txt**: `curl https://www.sofascore.com/robots.txt`
5. **Alternar fontes** se um site bloquear (transfermarkt, flashscore)

## 🎓 Melhores Práticas

### ✅ FAZER:
- Respeitar rate limits
- Usar cache agressivamente
- Adicionar delays
- Rodar em background
- Monitorar logs
- Testar com 1 item primeiro

### ❌ NÃO FAZER:
- Fazer milhares de requests seguidos
- Ignorar erros 429
- Usar delays < 1 segundo
- Rodar múltiplas instâncias simultaneamente
- Scraping 24/7
- Ignorar robots.txt

## 🛠️ Troubleshooting

### Problema: Nenhuma foto encontrada
```bash
# Verificar se o mapeamento está correto
python -c "from src.atualizar_com_scraper import SOFASCORE_TEAMS; print(SOFASCORE_TEAMS['Flamengo'])"

# Testar URL manualmente
curl "https://api.sofascore.com/api/v1/team/5981/players"
```

### Problema: Muitos erros 429
```python
# Em scraper_seguro.py, aumentar delays
MIN_DELAY = 5
MAX_DELAY = 10
REQUESTS_PER_MINUTE = 8
```

### Problema: Cache desatualizado
```bash
# Limpar cache para forçar novos requests
rm -rf data/cache/*
```

## 📈 Próximos Passos

1. ✅ Buscar fotos de jogadores
2. ⏳ Buscar estatísticas (gols, assistências)
3. ⏳ Buscar ratings do SofaScore
4. ⏳ Buscar histórico de partidas
