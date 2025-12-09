#!/usr/bin/env python3
"""
Teste da API-Football (api-football.com)
Plano gratuito: 100 requests/dia
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Importar configuração
try:
    from config_api_football import API_KEYS, BASE_URL
except ImportError:
    print("❌ Erro: Configure as API Keys em config_api_football.py")
    exit(1)

# Usar primeira chave para teste
API_KEY = API_KEYS[0] if API_KEYS and API_KEYS[0] != "SUA_API_KEY_1_AQUI" else None

def testar_conexao():
    """Testa conexão com a API"""
    url = f"{BASE_URL}/status"
    headers = {
        'x-apisports-key': API_KEY
    }
    
    print("🔍 TESTANDO API-FOOTBALL")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conexão bem-sucedida!")
            print(f"\n📊 Limites da sua conta:")
            
            account = data.get('response', {}).get('account', {})
            requests_info = data.get('response', {}).get('requests', {})
            
            print(f"   Plano: {account.get('plan', 'N/A')}")
            print(f"   Requests disponíveis: {requests_info.get('current', 'N/A')}/{requests_info.get('limit_day', 'N/A')}")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   Mensagem: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def buscar_brasileirao():
    """Busca ID do Brasileirão 2025"""
    url = f"{BASE_URL}/leagues"
    headers = {'x-apisports-key': API_KEY}
    params = {
        'country': 'Brazil',
        'season': 2025
    }
    
    print("\n🏆 BUSCANDO BRASILEIRÃO 2025")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            leagues = data.get('response', [])
            
            for league in leagues:
                league_data = league.get('league', {})
                if 'Serie A' in league_data.get('name', ''):
                    print(f"✅ Encontrado: {league_data.get('name')}")
                    print(f"   ID: {league_data.get('id')}")
                    print(f"   País: {league.get('country', {}).get('name')}")
                    return league_data.get('id')
            
            print("⚠️  Série A não encontrada")
            print(f"Ligas disponíveis: {[l.get('league', {}).get('name') for l in leagues]}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    return None

def buscar_times_brasileirao(league_id=71):
    """Busca times do Brasileirão (ID padrão: 71)"""
    url = f"{BASE_URL}/teams"
    headers = {'x-apisports-key': API_KEY}
    params = {
        'league': league_id,
        'season': 2025
    }
    
    print(f"\n📋 BUSCANDO TIMES DO BRASILEIRÃO 2025")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            teams = data.get('response', [])
            
            print(f"✅ Encontrados {len(teams)} times:")
            for team in teams[:5]:
                team_data = team.get('team', {})
                print(f"   - {team_data.get('name')} (ID: {team_data.get('id')})")
            
            if len(teams) > 5:
                print(f"   ... e mais {len(teams) - 5} times")
            
            return teams
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    return []

def buscar_jogadores_time(team_id, season=2025):
    """Busca jogadores de um time específico"""
    url = f"{BASE_URL}/players"
    headers = {'x-apisports-key': API_KEY}
    params = {
        'team': team_id,
        'season': season
    }
    
    print(f"\n👥 BUSCANDO JOGADORES (Team ID: {team_id})")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            players = data.get('response', [])
            
            print(f"✅ Encontrados {len(players)} jogadores")
            
            # Mostrar exemplos com estatísticas
            for player_data in players[:3]:
                player = player_data.get('player', {})
                stats = player_data.get('statistics', [{}])[0]
                
                games = stats.get('games', {})
                goals = stats.get('goals', {})
                
                print(f"\n   {player.get('name', 'N/A')}")
                print(f"      Posição: {games.get('position', 'N/A')}")
                print(f"      Jogos: {games.get('appearences', 0)}")
                print(f"      Gols: {goals.get('total', 0)}")
                print(f"      Assistências: {stats.get('goals', {}).get('assists', 0)}")
            
            return players
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    return []

def exemplo_estatisticas_completas():
    """Mostra exemplo de todas as estatísticas disponíveis"""
    print("\n📊 ESTATÍSTICAS DISPONÍVEIS NA API-FOOTBALL")
    print("=" * 80)
    print("""
    JOGADOR:
      • Nome, foto, idade, nacionalidade
      • Altura, peso
      • Número da camisa
      
    ESTATÍSTICAS DE JOGO:
      • Partidas jogadas (titular/reserva)
      • Minutos jogados
      • Rating médio
      
    ATAQUE:
      • Gols marcados
      • Assistências
      • Chutes (total, no gol)
      • Passes decisivos
      
    DEFESA:
      • Tackles
      • Interceptações
      • Bloqueios
      • Duelos ganhos/perdidos
      
    DISCIPLINA:
      • Cartões amarelos
      • Cartões vermelhos
      
    GOLEIRO:
      • Defesas
      • Gols sofridos
      • Clean sheets (jogos sem sofrer gol)
      
    TIME:
      • Jogos, vitórias, empates, derrotas
      • Gols marcados/sofridos
      • Clean sheets
      • Maiores vitórias/derrotas
      • Forma recente
    """)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔑 TESTE DA API-FOOTBALL")
    print("=" * 80)
    
    if not API_KEY or API_KEY == "SUA_API_KEY_1_AQUI":
        print("\n⚠️  CONFIGURE AS API KEYS PRIMEIRO!")
        print("=" * 80)
        print("📋 PASSOS:")
        print("   1. Crie 5 contas em: https://www.api-football.com/")
        print("   2. Pegue as API Keys em: https://dashboard.api-football.com/")
        print("   3. Cole em: src/config_api_football.py")
        print()
        print("📖 Veja o guia completo: GUIA_SETUP_API_FOOTBALL.md")
        print("=" * 80)
        exit(1)
    else:
        # Executar testes
        if testar_conexao():
            league_id = buscar_brasileirao()
            if league_id:
                times = buscar_times_brasileirao(league_id)
                if times:
                    # Testar com primeiro time (ex: Flamengo)
                    primeiro_time = times[0].get('team', {})
                    team_id = primeiro_time.get('id')
                    print(f"\n🔍 Testando com: {primeiro_time.get('name')}")
                    buscar_jogadores_time(team_id)
        
        exemplo_estatisticas_completas()
        
        print("\n" + "=" * 80)
        print("💡 PRÓXIMOS PASSOS:")
        print("   1. Se funcionou, podemos migrar para API-Football")
        print("   2. Tem 100 requests/dia grátis (suficiente para atualizar 1 time/dia)")
        print("   3. Estatísticas mais completas que o SofaScore")
        print("=" * 80)
