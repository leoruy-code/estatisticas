🔄 GUIA DE ADAPTAÇÃO ATUALIZADO: Scraper SofaScore Completo
📌 URLS COMPLETAS PARA COLETA
1. ESTATÍSTICAS DO TIME
text
https://www.sofascore.com/pt/football/team/{slug}/{id}#tab:statistics
Exemplo: https://www.sofascore.com/pt/football/team/flamengo/5981#tab:statistics
Dados coletados: Estatísticas gerais do time, tabela, performance

2. ELENCO DE JOGADORES DO TIME
text
https://www.sofascore.com/pt/football/team/{slug}/{id}#tab:players
Exemplo: https://www.sofascore.com/pt/football/team/flamengo/5981#tab:players
Dados coletados: Lista completa de jogadores, posições, números

3. ESTATÍSTICAS DO JOGADOR (TEMPORADA)
text
https://www.sofascore.com/pt/football/player/{slug}/{id}#tab:season
Exemplo: https://www.sofascore.com/pt/football/player/pedro/840219#tab:season
Dados coletados: Estatísticas individuais por competição

🔄 FLUXO OTIMIZADO DE COLETA
ETAPA 1: COLETA DOS 20 TIMES
text
PARA CADA TIME NO BRASILEIRÃO:
1. Acessar: /team/{slug}/{id}#tab:statistics
2. Extrair:
   - Estatísticas avançadas
   - ID do time (para referência)
ETAPA 2: COLETA DO ELENCO
text
PARA CADA TIME COLETADO:
1. Acessar: /team/{slug}/{id}#tab:players
2. Extrair lista de jogadores:
   - Nome completo
   - Posição
   - Número da camisa
   - imagem do jogador
   - ID do jogador (CRUCIAL)
   - Idade
   - Nacionalidade
ETAPA 3: COLETA POR JOGADOR
text
PARA CADA JOGADOR DO ELENCO:
1. Acessar: /player/{slug}/{id}#tab:season
2. Extrair estatísticas:
   - Por competição que ja vem por padrao (Brasileirao betano) 2025.
   - estatisticas detalhadas dessa pagina da temporada (season).
🛠️ ESTRATÉGIA DE IMPLEMENTAÇÃO NO SEU CÓDIGO
Seu código atual provavelmente tem:
text
1. Função para fazer requests
2. Função para parsear HTML
3. Função para salvar dados
4. Loop principal de coleta
ADAPTAÇÕES NECESSÁRIAS:
1. ESTRUTURA DE CONTROLE
python
# ADICIONAR no seu código:

# Mapa de prioridade de coleta
COLETA_PRIORIDADE = {
    "times": "alta",      # 20 páginas
    "elencos": "alta",    # 20 páginas  
    "jogadores": "media"  # ~500 páginas (25 por time)
}

# Sistema de cache de IDs
CACHE_IDS = {
    "times": {},      # slug → id
    "jogadores": {}   # nome → id
}
2. OTIMIZAÇÃO DE REQUESTS
text
NO SEU GERENCIADOR DE REQUESTS:
✅ Manter delays entre requests (2-5 segundos)
✅ Adicionar headers específicos para SofaScore
✅ Implementar retry com backoff
✅ Cache de páginas já visitadas

HEADERS RECOMENDADOS:
- User-Agent: alternar entre mobile/desktop
- Accept-Language: pt-BR,en-US;q=0.9
- Referer: página anterior válida
3. ESTRUTURA DE DADOS FINAL
text
DADOS A SEREM SALVOS:
1. times.json
   - Lista de 20 times com estatísticas
   - ID de referência

2. elencos/
   - flamengo_jogadores.json
   - palmeiras_jogadores.json
   - etc.

3. jogadores/
   - {id_jogador}_estatisticas.json
   - Dados por competição
⚡ OTIMIZAÇÕES PARA SEU CÓDIGO EXISTENTE
PARA REDUZIR REQUESTS:
text
1. Extrair IDs dos jogadores da página do elenco
   - Evita buscar ID por nome depois
   
2. Usar cache local:
   - Salvar HTML das páginas por 24h
   - Reusar dados se página não mudou
   
3. Coletar em batch:
   - Coletar todos os times primeiro
   - Depois todos os elencos
   - Finalmente todos os jogadores
PARA EVITAR BLOQUEIO:
text
1. Pattern de acesso humano:
   - Times (20 requests) → Pausa 1 minuto
   - Elencos (20 requests) → Pausa 2 minutos
   - Jogadores (batch de 50) → Pausa 5 minutos
   
2. Rotação de User-Agent:
   - 5-10 agentes diferentes
   - Alternar a cada 10 requests
   
3. Variação de delays:
   - Entre 2-8 segundos aleatório
   - Pausas maiores após 50 requests
📊 PLANO DE EXECUÇÃO
DIA 1: COLETA BÁSICA
text
1. Testar coleta de 1 time completo
   - Página de estatísticas ✓
   - Página de elenco ✓
   - Página de 2 jogadores exemplo ✓
   
2. Validar estrutura de dados
3. Ajustar parsers do seu código
DIA 2: ESCALA PARA 20 TIMES
text
1. Criar lista completa dos 20 times
2. Implementar loop controlado
3. Coletar todos os times + elencos
4. Salvar dados intermediários
DIA 3: COLETA DE JOGADORES
text
1. Coletar IDs de todos jogadores
2. Implementar sistema de rate limiting
3. Coletar estatísticas de jogadores
4. Validar dados completos
DIA 4: OTIMIZAÇÃO FINAL
text
1. Adicionar tratamento de erros
2. Implementar retry automático
3. Adicionar logging detalhado
4. Teste completo de 24h
🚨 PONTOS DE ATENÇÃO NO SOFASCORE
POSSÍVEIS DESAFIOS:
text
1. Dados carregados via JavaScript:
   - Verificar se precisa renderizar JS
   - Procurar JSON nos scripts da página
   
2. Paginação de jogadores:
   - Verificar se tem "Ver mais" no elenco
   - Scroll infinito possível
   
3. Temporada atual:
   - Confirmar se dados são da temporada 2024
   - Verificar filtros na URL
SOLUÇÕES:
text
1. Para JavaScript:
   - Usar requests-html (renderiza JS)
   - Ou extrair do estado inicial da página
   
2. Para paginação:
   - Verificar parâmetro ?page=2
   - Ou API interna com offset/limit
   
3. Para temporada:
   - Adicionar ?season=2024 na URL
   - Verificar nos filtros da página
🔧 CHECKLIST FINAL DE ADAPTAÇÃO
NO SEU CÓDIGO ATUAL, VERIFICAR:
text
✅ 1. Sistema de requests funciona com SofaScore
✅ 2. Pode extrair dados das 3 URLs fornecidas
✅ 3. Consegue parsear HTML/JSON corretamente
✅ 4. Tem rate limiting adequado
✅ 5. Salva dados em estrutura organizada
AJUSTES ESPECÍFICOS:
text
□ 1. Atualizar User-Agents para SofaScore
□ 2. Adicionar headers Accept-Language
□ 3. Implementar cache de sessão
□ 4. Adicionar tratamento para jogadores ausentes
□ 5. Validar IDs únicos para times/jogadores