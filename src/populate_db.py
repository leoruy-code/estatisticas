"""
Script para popular o PostgreSQL com dados do Brasileirão 2025
Migra dados do JSON para o banco de dados
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estatisticas',
    'user': 'estatisticas_user',
    'password': 'estatisticas_pass'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

def popular_times(conn, times_data):
    """Popula tabela teams e team_stats."""
    cursor = conn.cursor()
    
    # Limpar tabelas
    cursor.execute("TRUNCATE teams CASCADE;")
    
    print("📊 Inserindo times...")
    
    for i, time in enumerate(times_data, 1):
        # Inserir time
        cursor.execute("""
            INSERT INTO teams (id, nome, liga, sofascore_id, ativo)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nome = EXCLUDED.nome,
                sofascore_id = EXCLUDED.sofascore_id
        """, (
            i,
            time['nome'],
            'Brasileirão Série A',
            time.get('id'),
            True
        ))
        
        # Inserir estatísticas do time
        metricas = time.get('metricas', {})
        cursor.execute("""
            INSERT INTO team_stats (team_id, jogos_total, gols_marcados_media, gols_sofridos_media,
                                   escanteios_for_media, chutes_for_media, cartoes_for_media,
                                   faltas_for_media, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                gols_marcados_media = EXCLUDED.gols_marcados_media,
                gols_sofridos_media = EXCLUDED.gols_sofridos_media,
                escanteios_for_media = EXCLUDED.escanteios_for_media,
                chutes_for_media = EXCLUDED.chutes_for_media,
                cartoes_for_media = EXCLUDED.cartoes_for_media,
                faltas_for_media = EXCLUDED.faltas_for_media,
                updated_at = NOW()
        """, (
            i,
            38,  # jogos da temporada
            metricas.get('gols_media', 1.2),
            metricas.get('gols_sofridos_media', 1.2),
            metricas.get('escanteios_media', 5.0),
            metricas.get('chutes_media', 12.0),
            metricas.get('cartoes_media', 2.5),
            metricas.get('faltas_media', 12.0)
        ))
        
        print(f"  ✅ {time['nome']}")
    
    conn.commit()
    print(f"\n✅ {len(times_data)} times inseridos!")

def popular_jogadores(conn, jogadores_data, times_data):
    """Popula tabela players e player_stats."""
    cursor = conn.cursor()
    
    # Criar mapeamento time_nome -> team_id
    cursor.execute("SELECT id, nome FROM teams")
    times_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    print("\n👥 Inserindo jogadores...")
    
    # Limpar jogadores antigos
    cursor.execute("TRUNCATE players CASCADE;")
    
    inseridos = 0
    for jogador in jogadores_data:
        time_nome = jogador.get('time', '')
        team_id = times_map.get(time_nome)
        
        if not team_id:
            # Tentar match parcial
            for nome, tid in times_map.items():
                if time_nome in nome or nome in time_nome:
                    team_id = tid
                    break
        
        if not team_id:
            continue
        
        # Inserir jogador
        cursor.execute("""
            INSERT INTO players (id, nome, time_atual_id, posicao, ativo)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nome = EXCLUDED.nome,
                time_atual_id = EXCLUDED.time_atual_id,
                posicao = EXCLUDED.posicao
        """, (
            jogador.get('id', inseridos + 1),
            jogador.get('nome', ''),
            team_id,
            jogador.get('posicao', ''),
            True
        ))
        
        # Inserir estatísticas
        cursor.execute("""
            INSERT INTO player_stats (player_id, minutos_total, jogos_total, gols_total, 
                                      assistencias_total, chutes_total, chutes_gol_total,
                                      faltas_cometidas_total, cartoes_amarelos_total,
                                      cartoes_vermelhos_total, passes_chave_total,
                                      cruzamentos_total, xg_total, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (player_id) DO UPDATE SET
                minutos_total = EXCLUDED.minutos_total,
                jogos_total = EXCLUDED.jogos_total,
                gols_total = EXCLUDED.gols_total,
                assistencias_total = EXCLUDED.assistencias_total,
                chutes_total = EXCLUDED.chutes_total,
                updated_at = NOW()
        """, (
            jogador.get('id', inseridos + 1),
            jogador.get('minutos', 0),
            jogador.get('partidas', 0),
            jogador.get('gols', 0),
            jogador.get('assistencias', 0),
            jogador.get('chutes', 0),
            jogador.get('chutes_no_gol', 0),
            jogador.get('faltas_cometidas', 0),
            jogador.get('cartoes_amarelos', 0),
            jogador.get('cartoes_vermelhos', 0),
            jogador.get('passes_chave', 0),
            jogador.get('cruzamentos', 0),
            jogador.get('xg', 0.0)
        ))
        
        inseridos += 1
    
    conn.commit()
    print(f"✅ {inseridos} jogadores inseridos!")

def verificar_dados(conn):
    """Mostra resumo dos dados."""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("📊 RESUMO DO BANCO DE DADOS")
    print("="*50)
    
    cursor.execute("SELECT COUNT(*) FROM teams")
    print(f"Times: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM team_stats")
    print(f"Estatísticas de times: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM players")
    print(f"Jogadores: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM player_stats")
    print(f"Estatísticas de jogadores: {cursor.fetchone()[0]}")
    
    print("\n📋 Times cadastrados:")
    cursor.execute("""
        SELECT t.id, t.nome, ts.gols_marcados_media, 
               (SELECT COUNT(*) FROM players p WHERE p.time_atual_id = t.id) as jogadores
        FROM teams t
        LEFT JOIN team_stats ts ON t.id = ts.team_id
        ORDER BY t.id
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:2}. {row[1]:20} | Gols: {row[2] or 0:.1f} | Jogadores: {row[3]}")

def main():
    print("🚀 Populando PostgreSQL com dados do Brasileirão 2025\n")
    
    # Caminhos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    times_path = os.path.join(base_dir, 'data', 'times.json')
    jogadores_path = os.path.join(base_dir, 'data', 'jogadores.json')
    
    # Carregar dados
    times_data = carregar_json(times_path)
    jogadores_data = carregar_json(jogadores_path)
    
    print(f"📁 Dados carregados:")
    print(f"   Times: {len(times_data)}")
    print(f"   Jogadores: {len(jogadores_data)}")
    
    # Conectar e popular
    conn = get_connection()
    
    try:
        popular_times(conn, times_data)
        popular_jogadores(conn, jogadores_data, times_data)
        verificar_dados(conn)
    finally:
        conn.close()
    
    print("\n✅ Migração concluída!")

if __name__ == "__main__":
    main()
