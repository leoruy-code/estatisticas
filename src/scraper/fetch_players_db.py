"""
Fetch Players para PostgreSQL
=============================
Busca jogadores atualizados do SofaScore e insere direto no banco.
Rate limiting inteligente: rápido mas seguro.
"""

import json
import time
import random
import psycopg2
from psycopg2.extras import execute_values
import requests
from datetime import datetime
import sys

# ==================== CONFIGURAÇÕES ====================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estatisticas',
    'user': 'estatisticas_user',
    'password': 'estatisticas_pass'
}

# SofaScore API
BASE_URL = "https://www.sofascore.com/api/v1"
TOURNAMENT_ID = 325  # Brasileirão
SEASON_ID = 72034    # 2025

# Rate limiting inteligente
# - Começa rápido (0.5s)
# - Aumenta delay se detectar problemas
# - Requests em batch para ser mais eficiente
MIN_DELAY = 0.5
MAX_DELAY = 1.5
BATCH_SIZE = 5  # Processa N times, depois pausa maior

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Referer': 'https://www.sofascore.com/',
    'Origin': 'https://www.sofascore.com'
}

# ==================== FUNÇÕES ====================

session = requests.Session()
session.headers.update(HEADERS)
last_request = 0
current_delay = MIN_DELAY
consecutive_errors = 0

def smart_delay():
    """Rate limiting adaptativo."""
    global last_request, current_delay
    
    elapsed = time.time() - last_request
    delay = current_delay + random.uniform(0, 0.3)  # Pequeno jitter
    
    if elapsed < delay:
        time.sleep(delay - elapsed)
    
    last_request = time.time()

def fetch(endpoint: str) -> dict:
    """Faz requisição com retry e backoff."""
    global current_delay, consecutive_errors
    
    smart_delay()
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = session.get(url, timeout=15)
        
        if response.status_code == 429:
            # Rate limited - aumentar delay
            current_delay = min(current_delay * 2, 5.0)
            print(f"  ⚠️  Rate limit! Delay aumentado para {current_delay:.1f}s")
            time.sleep(10)
            return fetch(endpoint)
        
        if response.status_code == 403:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                print("  ❌ Bloqueado! Aguardando 30s...")
                time.sleep(30)
                consecutive_errors = 0
            return {}
        
        response.raise_for_status()
        
        # Sucesso - pode reduzir delay gradualmente
        consecutive_errors = 0
        if current_delay > MIN_DELAY:
            current_delay = max(current_delay * 0.9, MIN_DELAY)
        
        return response.json()
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return {}

def get_team_players(team_id: int, team_name: str) -> list:
    """Busca jogadores de um time."""
    data = fetch(f"team/{team_id}/players")
    
    if not data or 'players' not in data:
        return []
    
    players = []
    for p in data.get('players', []):
        player = p.get('player', {})
        
        # Calcular idade
        idade = 0
        if player.get('dateOfBirthTimestamp'):
            birth = datetime.fromtimestamp(player['dateOfBirthTimestamp'])
            idade = (datetime.now() - birth).days // 365
        
        players.append({
            'sofascore_id': player.get('id'),
            'nome': player.get('name', ''),
            'posicao': player.get('position', ''),
            'nacionalidade': player.get('country', {}).get('name', ''),
            'idade': idade,
            'numero': player.get('shirtNumber'),
            'pe': player.get('preferredFoot', ''),
            'altura': player.get('height', 0)
        })
    
    return players

def insert_players(conn, team_db_id: int, players: list):
    """Insere jogadores no banco."""
    cursor = conn.cursor()
    
    for p in players:
        cursor.execute("""
            INSERT INTO players (nome, time_atual_id, posicao, sofascore_id, ativo)
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT DO NOTHING
        """, (
            p['nome'],
            team_db_id,
            p['posicao'],
            p['sofascore_id']
        ))
    
    conn.commit()

def main():
    print("🚀 Buscando jogadores atualizados do Brasileirão 2025\n")
    print(f"⚡ Rate limit: {MIN_DELAY}-{MAX_DELAY}s (adaptativo)")
    print(f"📦 Batch size: {BATCH_SIZE} times por pausa\n")
    
    # Conectar ao banco
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Buscar times do banco com sofascore_id
    cursor.execute("SELECT id, nome, sofascore_id FROM teams ORDER BY id")
    teams = cursor.fetchall()
    
    print(f"📋 {len(teams)} times para processar\n")
    
    total_players = 0
    start_time = time.time()
    
    for i, (team_id, team_name, sofascore_id) in enumerate(teams, 1):
        print(f"[{i:2}/{len(teams)}] {team_name}...", end=" ", flush=True)
        
        players = get_team_players(sofascore_id, team_name)
        
        if players:
            insert_players(conn, team_id, players)
            total_players += len(players)
            print(f"✅ {len(players)} jogadores")
        else:
            print("❌ Sem dados")
        
        # Pausa maior a cada batch
        if i % BATCH_SIZE == 0 and i < len(teams):
            pause = random.uniform(2, 4)
            print(f"\n   ⏸️  Pausa de {pause:.1f}s...\n")
            time.sleep(pause)
    
    elapsed = time.time() - start_time
    
    # Resumo final
    print("\n" + "="*50)
    print("📊 RESUMO")
    print("="*50)
    print(f"✅ {total_players} jogadores inseridos")
    print(f"⏱️  Tempo total: {elapsed:.1f}s")
    print(f"📈 Média: {elapsed/len(teams):.1f}s por time")
    
    # Verificar no banco
    cursor.execute("""
        SELECT t.nome, COUNT(p.id) as jogadores
        FROM teams t
        LEFT JOIN players p ON p.time_atual_id = t.id
        GROUP BY t.id, t.nome
        ORDER BY jogadores DESC
    """)
    
    print("\n📋 Jogadores por time:")
    for nome, count in cursor.fetchall():
        print(f"   {nome:25} {count:3} jogadores")
    
    conn.close()
    print("\n✅ Concluído!")

if __name__ == "__main__":
    main()
