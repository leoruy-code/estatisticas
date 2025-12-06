# 🚀 GUIA DE CONFIGURAÇÃO - API-FOOTBALL

## Passo 1: Criar 5 Contas Gratuitas

### 1.1 - Primeira Conta
1. Acesse: https://www.api-football.com/
2. Clique em **"Sign Up"** (canto superior direito)
3. Preencha:
   - **Email:** seu_email@gmail.com
   - **Senha:** (crie uma senha forte)
4. Confirme o email
5. Faça login

### 1.2 - Contas 2 a 5
Repita o processo acima com emails diferentes:
- **Dica 1:** Use Gmail com `+`: email+api2@gmail.com, email+api3@gmail.com
- **Dica 2:** Ou use emails diferentes mesmo
- **Total:** 5 contas = 500 requests/dia! 🎯

---

## Passo 2: Pegar as API Keys

Para cada uma das 5 contas:

1. Faça login em: https://www.api-football.com/
2. Acesse o Dashboard: https://dashboard.api-football.com/
3. Na página inicial, você verá:
   ```
   YOUR API KEY
   xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
4. Clique em **"Copy"** ou selecione e copie a chave
5. Guarde em um arquivo temporário (txt)

---

## Passo 3: Configurar o Sistema

### 3.1 - Editar arquivo de configuração

Abra o arquivo: `src/config_api_football.py`

Você verá:
```python
API_KEYS = [
    "SUA_API_KEY_1_AQUI",
    "SUA_API_KEY_2_AQUI",
    "SUA_API_KEY_3_AQUI",
    "SUA_API_KEY_4_AQUI",
    "SUA_API_KEY_5_AQUI",
]
```

Substitua por suas chaves reais:
```python
API_KEYS = [
    "abc123def456ghi789jkl012mno345pqr678",  # Conta 1
    "xyz789uvw456rst123opq890mno567klm234",  # Conta 2
    "qwe456rty789uio123pas456dfg789hjk012",  # Conta 3
    "zxc345vbn678mnb901qwe234rty567uio890",  # Conta 4
    "asd678fgh901jkl234zxc567vbn890bnm123",  # Conta 5
]
```

### 3.2 - Salvar e fechar

---

## Passo 4: Testar Configuração

Execute o teste:
```bash
cd "/Users/leo/RAG ESTATISTICAS"
source venv/bin/activate
python src/testar_api_football.py
```

Você deve ver:
```
✅ Conexão bem-sucedida!
📊 Limites da sua conta:
   Plano: free
   Requests disponíveis: 0/100
```

Se funcionou, você está pronto! 🎉

---

## Passo 5: Atualizar Dados

Execute a atualização completa:
```bash
python src/atualizar_api_football.py
```

Isso vai:
1. ✅ Buscar todos os 20 times do Brasileirão 2025
2. ✅ Buscar jogadores de cada time
3. ✅ Coletar estatísticas completas
4. ✅ Salvar em `data/jogadores.json`
5. ✅ Usar rotação automática entre as 5 chaves

**Tempo estimado:** 5-10 minutos
**Requests usados:** ~40-60 (de 500 disponíveis)

---

## Passo 6: Sincronizar e Ver no Site

Depois da atualização:
```bash
# Sincronizar dados
python src/sincronizar_times_jogadores.py

# Iniciar site
streamlit run src/frontend/app.py
```

Acesse: http://localhost:8501

---

## 🎯 Resumo Executivo

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | Criar 5 contas | 10 min |
| 2 | Copiar 5 API Keys | 2 min |
| 3 | Colar em config_api_football.py | 1 min |
| 4 | Testar conexão | 30 seg |
| 5 | Atualizar dados | 5-10 min |
| 6 | Ver no site | 1 min |
| **TOTAL** | **~20 minutos** | ✅ |

---

## 💡 Dicas

1. **Organização:** Mantenha as senhas das 5 contas em um gerenciador (1Password, LastPass)
2. **Rotação:** O sistema alterna automaticamente entre as 5 chaves
3. **Monitoramento:** Você pode ver uso em cada dashboard: https://dashboard.api-football.com/
4. **Atualizações:** Execute `python src/atualizar_api_football.py` 1x por semana
5. **Limite:** Com 5 contas = 500 requests/dia = atualiza TODOS os times TODO DIA!

---

## ⚠️ Troubleshooting

### Erro: "Invalid API Key"
- ✅ Verifique se copiou a chave completa
- ✅ Sem espaços antes/depois
- ✅ Entre aspas duplas

### Erro: "Rate limit exceeded"
- ✅ Normal! O sistema vai rotacionar para próxima chave
- ✅ Se todas as 5 esgotarem, espere 24h

### Erro: "League not found"
- ✅ Brasileirão 2025 pode não estar disponível ainda
- ✅ Teste com 2024: mude SEASON = 2024 no config

---

## 🎉 Pronto!

Após configurar, você terá:
- ✅ **500 requests/dia** (5 contas × 100)
- ✅ **Dados oficiais** e confiáveis
- ✅ **Sem bloqueios** (API oficial)
- ✅ **Estatísticas completas** de todos os jogadores
- ✅ **Atualização automática** de todos os times

**Custo:** R$ 0,00 (100% GRÁTIS) 💰
