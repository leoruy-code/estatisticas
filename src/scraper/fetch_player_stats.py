"""
Fetch Player Stats - Busca estatísticas completas de todos os jogadores
========================================================================
Salva todas as estatísticas disponíveis no SofaScore para cada jogador.
"""

import json
import time
import random
import psycopg2
from psycopg2.extras import Json
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

BASE_URL = "https://www.sofascore.com/api/v1"
TOURNAMENT_ID = 325  # Brasileirão
SEASON_ID = 72034    # 2025

# Rate limiting adaptativo
MIN_DELAY = 0.3
MAX_DELAY = 0.8
BATCH_SIZE = 20  # Pausa maior a cada N jogadores

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Referer': 'https://www.sofascore.com/'
}

# ==================== RATE LIMITING ====================

session = requests.Session()
session.headers.update(HEADERS)
last_request = 0
current_delay = MIN_DELAY
errors_count = 0

def smart_delay():
    global last_request, current_delay
    elapsed = time.time() - last_request
    delay = current_delay + random.uniform(0, 0.2)
    if elapsed < delay:
        time.sleep(delay - elapsed)
    last_request = time.time()

def fetch(endpoint: str) -> dict:
    global current_delay, errors_count
    smart_delay()
    
    try:
        response = session.get(f"{BASE_URL}/{endpoint}", timeout=15)
        
        if response.status_code == 429:
            current_delay = min(current_delay * 2, 5.0)
            print(f"\n  ⚠️ Rate limit! Delay: {current_delay:.1f}s")
            time.sleep(10)
            return fetch(endpoint)
        
        if response.status_code == 404:
            return {}  # Jogador sem stats nessa temporada
        
        if response.status_code == 403:
            errors_count += 1
            if errors_count >= 5:
                print("\n  ❌ Bloqueado! Aguardando 30s...")
                time.sleep(30)
                errors_count = 0
            return {}
        
        response.raise_for_status()
        errors_count = 0
        
        if current_delay > MIN_DELAY:
            current_delay = max(current_delay * 0.95, MIN_DELAY)
        
        return response.json()
        
    except Exception as e:
        return {}

# ==================== MAPEAMENTO DE STATS ====================

def map_stats(raw: dict) -> dict:
    """Mapeia estatísticas do SofaScore para colunas do banco."""
    return {
        'jogos_total': raw.get('appearances', 0),
        'minutos_total': raw.get('minutesPlayed', 0),
        'titularidades': raw.get('matchesStarted', 0),
        'gols_total': raw.get('goals', 0),
        'assistencias_total': raw.get('assists', 0),
        'xg': raw.get('expectedGoals', 0) or raw.get('goals', 0) * 0.1,  # fallback
        'xa': raw.get('expectedAssists', 0),
        'chutes_total': raw.get('totalShots', 0),
        'chutes_no_gol': raw.get('shotsOnTarget', 0),
        'passes_total': raw.get('totalPasses', 0),
        'passes_certos': raw.get('accuratePasses', 0),
        'passes_decisivos': raw.get('keyPasses', 0),
        'passes_longos_certos': raw.get('accurateLongBalls', 0),
        'cruzamentos_total': raw.get('totalCross', 0),
        'cruzamentos_certos': raw.get('accurateCrosses', 0),
        'desarmes_total': raw.get('tackles', 0),
        'interceptacoes_total': raw.get('interceptions', 0),
        'duelos_ganhos': raw.get('totalDuelsWon', 0),
        'duelos_totais': int(raw.get('totalDuelsWon', 0) / (raw.get('totalDuelsWonPercentage', 50) / 100)) if raw.get('totalDuelsWonPercentage') else 0,
        'duelos_aereos_ganhos': raw.get('aerialDuelsWon', 0),
        'dribles_certos': raw.get('successfulDribbles', 0),
        'faltas_cometidas': raw.get('fouls', 0),
        'faltas_sofridas': raw.get('wasFouled', 0),
        'cartoes_amarelos': raw.get('yellowCards', 0),
        'cartoes_vermelhos': raw.get('redCards', 0) + raw.get('directRedCards', 0),
        'impedimentos': raw.get('offsides', 0),
        'grandes_chances_criadas': raw.get('bigChancesCreated', 0),
        'grandes_chances_perdidas': raw.get('bigChancesMissed', 0),
        # Goleiro
        'defesas': raw.get('saves', 0),
        'gols_sofridos': raw.get('goalsConceded', 0),
        'clean_sheets': raw.get('cleanSheet', 0),
        'penaltis_defendidos': raw.get('penaltySave', 0),
        'gols_evitados': raw.get('goalsPrevented', 0),
        'erros_para_gol': raw.get('errorLeadToGoal', 0),
        # Extras
        'rating': raw.get('rating', 0),
        'bolas_recuperadas': raw.get('ballRecovery', 0),
        'toques': raw.get('touches', 0),
        'sofascore_stats_id': raw.get('id', 0),
    }

def insert_stats(conn, player_id: int, stats: dict, raw_stats: dict):
    """Insere ou atualiza estatísticas do jogador."""
    cursor = conn.cursor()
    
    # Calcular médias por 90
    minutos = stats.get('minutos_total', 0)
    if minutos > 0:
        fator = 90 / minutos
        stats['minutos_por_jogo'] = minutos / max(stats.get('jogos_total', 1), 1)
        stats['gols_por_90'] = stats.get('gols_total', 0) * fator
        stats['finalizacoes_por_90'] = stats.get('chutes_total', 0) * fator
        stats['passes_chave_por_90'] = stats.get('passes_decisivos', 0) * fator
        stats['cruzamentos_por_90'] = stats.get('cruzamentos_total', 0) * fator
        stats['faltas_cometidas_por_90'] = stats.get('faltas_cometidas', 0) * fator
        stats['cartoes_amarelos_por_90'] = stats.get('cartoes_amarelos', 0) * fator
    
    # Construir query dinâmica
    columns = list(stats.keys()) + ['raw_stats', 'periodo', 'updated_at']
    values = list(stats.values()) + [Json(raw_stats), 'Brasileirão 2025', datetime.now()]
    
    placeholders = ', '.join(['%s'] * len(values))
    col_names = ', '.join(columns)
    
    # Upsert
    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'player_id'])
    
    cursor.execute(f"""
        INSERT INTO player_stats (player_id, {col_names})
        VALUES (%s, {placeholders})
        ON CONFLICT (player_id) DO UPDATE SET {update_clause}
    """, [player_id] + values)
    
    conn.commit()

# ==================== MAIN ====================

def main():
    print("🚀 Buscando estatísticas de todos os jogadores\n")
    print(f"⚡ Rate limit: {MIN_DELAY}-{MAX_DELAY}s (adaptativo)")
    print(f"📦 Batch: pausa a cada {BATCH_SIZE} jogadores\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Buscar todos os jogadores com sofascore_id
    cursor.execute("""
        SELECT p.id, p.nome, p.sofascore_id, t.nome as time
        FROM players p
        JOIN teams t ON p.time_atual_id = t.id
        WHERE p.sofascore_id IS NOT NULL
        ORDER BY t.id, p.nome
    """)
    players = cursor.fetchall()
    
    print(f"📋 {len(players)} jogadores para processar\n")
    
    stats_found = 0
    stats_empty = 0
    start_time = time.time()
    current_team = None
    
    for i, (player_id, nome, sofascore_id, time_nome) in enumerate(players, 1):
        # Header do time
        if time_nome != current_team:
            current_team = time_nome
            print(f"\n🏟️  {time_nome}")
            print("-" * 40)
        
        # Buscar stats
        endpoint = f"player/{sofascore_id}/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/statistics/overall"
        data = fetch(endpoint)
        
        raw_stats = data.get('statistics', {})
        
        if raw_stats and raw_stats.get('appearances', 0) > 0:
            mapped = map_stats(raw_stats)
            insert_stats(conn, player_id, mapped, raw_stats)
            stats_found += 1
            
            jogos = mapped.get('jogos_total', 0)
            gols = mapped.get('gols_total', 0)
            rating = mapped.get('rating', 0)
            print(f"  ✅ {nome[:25]:25} | {jogos:2}j {gols:2}g | ⭐{rating:.1f}")
        else:
            stats_empty += 1
            print(f"  ⚪ {nome[:25]:25} | sem stats")
        
        # Pausa a cada batch
        if i % BATCH_SIZE == 0 and i < len(players):
            pause = random.uniform(1.5, 3.0)
            print(f"\n  ⏸️  Pausa {pause:.1f}s... ({i}/{len(players)})\n")
            time.sleep(pause)
    
    elapsed = time.time() - start_time
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO FINAL")
    print("=" * 50)
    print(f"✅ Com estatísticas: {stats_found}")
    print(f"⚪ Sem estatísticas: {stats_empty}")
    print(f"⏱️  Tempo total: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"📈 Média: {elapsed/len(players):.2f}s por jogador")
    
    # Verificar no banco
    cursor.execute("SELECT COUNT(*) FROM player_stats WHERE jogos_total > 0")
    total_db = cursor.fetchone()[0]
    print(f"\n📁 Total no banco: {total_db} jogadores com stats")
    
    conn.close()
    print("\n✅ Concluído!")

if __name__ == "__main__":
    main()
