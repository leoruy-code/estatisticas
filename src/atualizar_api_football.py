#!/usr/bin/env python3
"""
Integrador API-Football para Brasileirão 2025
Usa rotação de 5 API Keys para 500 requests/dia
"""

import requests
import json
import time
import os
from datetime import datetime

# Importar configuração
try:
    from config_api_football import API_KEYS, BASE_URL, BRASILEIRAO_LEAGUE_ID, SEASON
except ImportError:
    print("❌ Erro: arquivo config_api_football.py não encontrado!")
    exit(1)

class APIFootballClient:
    """Cliente para API-Football com rotação de chaves"""
    
    def __init__(self):
        self.api_keys = [k for k in API_KEYS if k != "SUA_API_KEY_1_AQUI" and k != ""]
        if not self.api_keys:
            raise ValueError("❌ Configure pelo menos 1 API Key em config_api_football.py")
        
        self.current_key_index = 0
        self.base_url = BASE_URL
        self.league_id = BRASILEIRAO_LEAGUE_ID
        self.season = SEASON
        self.request_count = 0
        
        print(f"✅ API-Football inicializada com {len(self.api_keys)} chaves")
    
    def _get_current_key(self):
        """Retorna a chave atual e rotaciona"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def _make_request(self, endpoint, params=None):
        """Faz requisição com rotação de chaves"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'x-apisports-key': self._get_current_key()}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"⚠️  Rate limit - tentando próxima chave...")
                time.sleep(2)
                return self._make_request(endpoint, params)  # Retry com próxima key
            else:
                print(f"❌ Erro {response.status_code}: {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def get_teams(self):
        """Busca todos os times do Brasileirão 2025"""
        print(f"\n🔍 Buscando times do Brasileirão {self.season}...")
        
        data = self._make_request('teams', {
            'league': self.league_id,
            'season': self.season
        })
        
        if data and data.get('response'):
            teams = data['response']
            print(f"✅ Encontrados {len(teams)} times")
            return teams
        
        return []
    
    def get_players(self, team_id, team_name):
        """Busca jogadores de um time específico"""
        print(f"\n👥 Buscando jogadores: {team_name}...")
        
        data = self._make_request('players', {
            'team': team_id,
            'season': self.season,
            'league': self.league_id
        })
        
        if data and data.get('response'):
            players = data['response']
            print(f"   ✅ {len(players)} jogadores encontrados")
            return players
        
        print(f"   ⚠️  Nenhum jogador encontrado")
        return []
    
    def parse_player_data(self, player_data):
        """Converte dados da API para formato do sistema"""
        player = player_data.get('player', {})
        stats_list = player_data.get('statistics', [])
        
        # Usar estatísticas do Brasileirão
        stats = {}
        for s in stats_list:
            if s.get('league', {}).get('id') == self.league_id:
                stats = s
                break
        
        if not stats and stats_list:
            stats = stats_list[0]  # Fallback para primeira estatística
        
        games = stats.get('games', {})
        goals_data = stats.get('goals', {})
        passes = stats.get('passes', {})
        tackles_data = stats.get('tackles', {})
        duels_data = stats.get('duels', {})
        cards = stats.get('cards', {})
        shots = stats.get('shots', {})
        
        return {
            'nome': player.get('name', 'N/A'),
            'id': player.get('id'),
            'foto_url': player.get('photo'),
            'idade': player.get('age'),
            'nacionalidade': player.get('nationality'),
            'altura': player.get('height'),
            'peso': player.get('weight'),
            'numero': player.get('number'),
            'posicao': games.get('position', 'N/A'),
            
            # Estatísticas de jogo
            'partidas': games.get('appearences', 0) or 0,
            'titular': games.get('lineups', 0) or 0,
            'minutos_jogados': games.get('minutes', 0) or 0,
            'rating': float(games.get('rating', 0) or 0),
            
            # Gols e assistências
            'gols': goals_data.get('total', 0) or 0,
            'assistencias': goals_data.get('assists', 0) or 0,
            
            # Chutes
            'chutes': shots.get('total', 0) or 0,
            'chutes_no_gol': shots.get('on', 0) or 0,
            
            # Passes
            'passes_certos': passes.get('accuracy', 0) or 0,
            'total_passes': passes.get('total', 0) or 0,
            'passes_decisivos': passes.get('key', 0) or 0,
            
            # Defesa
            'desarmes': tackles_data.get('total', 0) or 0,
            'interceptacoes': tackles_data.get('interceptions', 0) or 0,
            'bloqueios': tackles_data.get('blocks', 0) or 0,
            
            # Duelos
            'duelos_ganhos': duels_data.get('won', 0) or 0,
            'duelos_totais': duels_data.get('total', 0) or 0,
            
            # Cartões
            'cartoes_amarelos': cards.get('yellow', 0) or 0,
            'cartoes_vermelhos': cards.get('red', 0) or 0,
        }

def atualizar_brasileirao():
    """Atualiza todos os times do Brasileirão"""
    print("\n" + "=" * 80)
    print("🏆 ATUALIZAÇÃO BRASILEIRÃO 2025 - API-FOOTBALL")
    print("=" * 80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 80)
    
    try:
        client = APIFootballClient()
    except ValueError as e:
        print(f"\n{e}")
        print("\n💡 PASSOS PARA CONFIGURAR:")
        print("   1. Acesse: https://www.api-football.com/")
        print("   2. Crie 5 contas gratuitas (use emails diferentes)")
        print("   3. Em cada conta, vá em: https://dashboard.api-football.com/")
        print("   4. Copie as 5 API Keys")
        print("   5. Cole em: src/config_api_football.py")
        return
    
    # Buscar times
    teams = client.get_teams()
    if not teams:
        print("❌ Erro ao buscar times")
        return
    
    # Carregar jogadores atuais (se existir)
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    jogadores_path = os.path.join(data_dir, 'jogadores.json')
    
    todos_jogadores = []
    times_processados = 0
    jogadores_adicionados = 0
    
    for team_data in teams:
        team = team_data.get('team', {})
        team_id = team.get('id')
        team_name = team.get('name')
        
        # Buscar jogadores do time
        players = client.get_players(team_id, team_name)
        
        for player_data in players:
            jogador = client.parse_player_data(player_data)
            jogador['time'] = team_name
            todos_jogadores.append(jogador)
            jogadores_adicionados += 1
        
        times_processados += 1
        print(f"   ✅ {team_name}: {len(players)} jogadores")
        
        # Delay para não sobrecarregar
        time.sleep(1)
    
    # Salvar dados
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(todos_jogadores, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("🎉 ATUALIZAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print(f"✅ Times processados: {times_processados}")
    print(f"✅ Jogadores adicionados: {jogadores_adicionados}")
    print(f"📊 Total de requests: {client.request_count}")
    print(f"💾 Arquivo salvo: {jogadores_path}")
    print("=" * 80)

if __name__ == "__main__":
    atualizar_brasileirao()
