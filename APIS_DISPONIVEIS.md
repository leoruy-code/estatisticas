# APIs Gratuitas para Estatísticas de Futebol

## 📊 Comparação de APIs Disponíveis

### 1. API-Football (RECOMENDADA) ⭐
**Site:** https://www.api-football.com/

**Plano Gratuito:**
- ✅ 100 requisições/dia
- ✅ Dados em tempo real
- ✅ Brasileirão 2025 disponível
- ✅ Documentação completa

**Estatísticas Disponíveis:**

**JOGADORES:**
- Dados pessoais (nome, foto, idade, nacionalidade, altura, peso)
- Posição e número da camisa
- Partidas jogadas (titular/reserva)
- Minutos jogados
- Rating médio
- Gols marcados
- Assistências
- Chutes (total, no gol)
- Passes decisivos
- Tackles, interceptações, bloqueios
- Duelos (ganhos/perdidos)
- Cartões (amarelos/vermelhos)
- **Goleiros:** defesas, gols sofridos, clean sheets

**TIMES:**
- Jogos, vitórias, empates, derrotas
- Gols marcados/sofridos
- Clean sheets
- Maiores vitórias/derrotas
- Forma recente (últimos 5 jogos)
- Estatísticas casa/fora

**Como Usar:**
1. Criar conta gratuita em: https://www.api-football.com/
2. Pegar API Key em: https://dashboard.api-football.com/
3. Executar: `python src/testar_api_football.py`

**Limitações:**
- 100 requests/dia (dá para atualizar 1-2 times por dia)
- Pode levar alguns dias para atualizar todos os 20 times

---

### 2. SofaScore (ATUAL)
**Site:** https://www.sofascore.com/

**Status:**
- ⚠️ API não oficial
- ⚠️ Bloqueios frequentes (erro 403)
- ✅ Muitos dados quando funciona

**Estatísticas Disponíveis:**
- 40+ campos por jogador
- xG, xA, rating
- Passes, dribles, duelos
- Estatísticas avançadas

**Problemas:**
- Rate limit muito agressivo
- Bloqueios por IP
- Não é oficial/documentada
- Pode parar de funcionar a qualquer momento

---

### 3. Football-Data.org
**Site:** https://www.football-data.org/

**Plano Gratuito:**
- ✅ 10 requisições/minuto
- ⚠️ Brasileirão não disponível no plano gratuito
- ✅ Ligas europeias principais

**Status:** ❌ Não serve para nosso caso (sem Brasileirão)

---

### 4. TheSportsDB
**Site:** https://www.thesportsdb.com/

**Plano Gratuito:**
- ✅ Totalmente gratuito
- ⚠️ Estatísticas básicas
- ⚠️ Dados podem estar desatualizados

**Estatísticas:**
- Apenas básicas (gols, assistências)
- Não tem dados avançados

**Status:** ⚠️ Backup, mas limitado

---

## 🎯 RECOMENDAÇÃO

### Solução Ideal: **API-Football**

**Vantagens:**
1. ✅ Oficial e confiável
2. ✅ Brasileirão 2025 completo
3. ✅ Estatísticas detalhadas
4. ✅ 100 requests/dia grátis
5. ✅ Sem bloqueios por rate limit
6. ✅ Documentação completa

**Estratégia de Uso:**
- **Dia 1-5:** Atualizar 4 times/dia (20 requests)
- **Dia 6-20:** Atualizar 1 time/dia (manutenção)
- **Total:** 5 dias para atualizar todos os 20 times

**Custo:** GRÁTIS (plano free)

---

## 💰 Opção Paga (Se Precisar)

Se quiser atualizar todos os times diariamente:

**API-Football Pro:**
- 💵 ~$10-15/mês
- 📈 1.000 requests/dia
- ⚡ Suficiente para atualizar todos os times diariamente

---

## 🚀 Próximos Passos

1. **Criar conta** em https://www.api-football.com/
2. **Pegar API Key** no dashboard
3. **Testar** com: `python src/testar_api_football.py`
4. **Migrar** do SofaScore para API-Football
5. **Automatizar** atualizações diárias

---

## 📝 Comparação Final

| Recurso | SofaScore | API-Football | Football-Data |
|---------|-----------|--------------|---------------|
| Plano Gratuito | ⚠️ Não oficial | ✅ 100/dia | ✅ 10/min |
| Brasileirão 2025 | ✅ | ✅ | ❌ |
| Estabilidade | ❌ Bloqueios | ✅ Estável | ✅ Estável |
| Estatísticas | ✅✅ Muitas | ✅ Completas | ⚠️ Básicas |
| Documentação | ❌ Nenhuma | ✅ Completa | ✅ Completa |
| **RECOMENDAÇÃO** | ❌ | ✅ **USAR** | ❌ |

---

## 🔧 Migração para API-Football

Vantagens imediatas:
1. ✅ Sem mais erro 403
2. ✅ Dados confiáveis e atualizados
3. ✅ Pode automatizar atualizações
4. ✅ Suporte oficial se tiver problemas

**Quer que eu implemente a migração para API-Football?**
