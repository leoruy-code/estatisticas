# ⚡ INÍCIO RÁPIDO - API-FOOTBALL

## 🎯 Configure em 3 Passos

### 1️⃣ Criar Contas (10 minutos)
```
1. Acesse: https://www.api-football.com/
2. Crie 5 contas gratuitas
3. Confirme os 5 emails
```

**Dica:** Use Gmail com `+` para facilitar:
- seu_email+api1@gmail.com
- seu_email+api2@gmail.com
- seu_email+api3@gmail.com
- seu_email+api4@gmail.com
- seu_email+api5@gmail.com

---

### 2️⃣ Copiar API Keys (2 minutos)

Para cada conta:
1. Login em: https://dashboard.api-football.com/
2. Copiar a API Key mostrada
3. Salvar em um bloco de notas

Você terá 5 chaves parecidas com:
```
abc123def456ghi789jkl012mno345pqr678
xyz789uvw456rst123opq890mno567klm234
qwe456rty789uio123pas456dfg789hjk012
zxc345vbn678mnb901qwe234rty567uio890
asd678fgh901jkl234zxc567vbn890bnm123
```

---

### 3️⃣ Configurar Sistema (1 minuto)

Abra o arquivo:
```
src/config_api_football.py
```

Cole suas 5 chaves:
```python
API_KEYS = [
    "abc123def456ghi789jkl012mno345pqr678",  # Conta 1
    "xyz789uvw456rst123opq890mno567klm234",  # Conta 2
    "qwe456rty789uio123pas456dfg789hjk012",  # Conta 3
    "zxc345vbn678mnb901qwe234rty567uio890",  # Conta 4
    "asd678fgh901jkl234zxc567vbn890bnm123",  # Conta 5
]
```

Salve o arquivo (Cmd+S ou Ctrl+S)

---

## ✅ Testar

```bash
cd "/Users/leo/RAG ESTATISTICAS"
source venv/bin/activate
python src/testar_api_football.py
```

Deve aparecer:
```
✅ Conexão bem-sucedida!
📊 Limites da sua conta:
   Plano: free
   Requests disponíveis: 0/100
```

---

## 🚀 Atualizar Dados

```bash
python src/atualizar_api_football.py
```

Aguarde 5-10 minutos. O sistema vai:
- ✅ Buscar 20 times do Brasileirão
- ✅ Buscar jogadores de cada time
- ✅ Coletar todas as estatísticas
- ✅ Salvar tudo em data/jogadores.json

---

## 🌐 Ver no Site

```bash
python src/sincronizar_times_jogadores.py
streamlit run src/frontend/app.py
```

Acesse: http://localhost:8501

---

## 📚 Guia Completo

Veja: **GUIA_SETUP_API_FOOTBALL.md** para mais detalhes

---

## 🎉 Benefícios

✅ **500 requests/dia** (5 × 100)
✅ **Dados oficiais** da API-Football
✅ **Sem bloqueios** (rate limit generoso)
✅ **Estatísticas completas** de todos jogadores
✅ **GRÁTIS para sempre**

---

## ❓ Problemas?

1. **"Invalid API Key"** → Verifique se copiou corretamente
2. **"Rate limit"** → Normal! Sistema rotaciona automaticamente
3. **Outras dúvidas** → Veja GUIA_SETUP_API_FOOTBALL.md
