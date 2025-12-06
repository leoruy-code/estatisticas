"""
Scraper otimizado usando endpoints internos do SofaScore
Baseado nas dicas do guia scrapper.md
"""

import json
import time
import random
import requests
from typing import Dict, List, Optional, Any

# Configurações
BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 2
MAX_DELAY = 4
TIMEOUT = 30

# IDs importantes
BRASILEIRAO_ID = 325  # unique-tournament ID
SEASON_2024 = 61644   # Season ID para 2024
SEASON_2025 = 63167   # Season ID para 2025 (precisa confirmar)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class SofaScoreScraper:
    """Scraper otimizado do SofaScore usando endpoints JSON diretos"""
    
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
    
    def _headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
        }
    
    def _delay(self):
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    def _get(self, endpoint: str) -> Optional[Dict]:
        """Request genérico com retry"""
        self._delay()
        url = f"{BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, headers=self._headers(), timeout=TIMEOUT)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Status {response.status_code}: {endpoint}")
                return None
        except Exception as e:
            print(f"❌ Erro em {endpoint}: {e}")
            return None
    
    def descobrir_season_id(self, year: int = 2025) -> Optional[int]:
        """
        Descobre o Season ID para um ano específico
        Endpoint: /unique-tournament/325/seasons
        """
        print(f"🔍 Descobrindo Season ID para {year}...")
        
        data = self._get(f"unique-tournament/{BRASILEIRAO_ID}/seasons")
        
        if data and 'seasons' in data:
            for season in data['seasons']:
                if season.get('year') == str(year):
                    season_id = season.get('id')
                    print(f"✅ Season {year} ID: {season_id}")
                    return season_id
        
        print(f"❌ Season {year} não encontrada")
        return None
    
    def listar_partidas_temporada(self, season_id: int) -> List[Dict]:
        """
        Lista todas as partidas de uma temporada
        Endpoint: /unique-tournament/325/season/{SEASON_ID}/events/last/0
        """
        print(f"\n📅 Buscando partidas da temporada {season_id}...")
        
        # Usar /events/last/0 para pegar todas
        data = self._get(f"unique-tournament/{BRASILEIRAO_ID}/season/{season_id}/events/last/0")
        
        if data and 'events' in data:
            events = data['events']
            print(f"✅ {len(events)} partidas encontradas")
            return events
        
        print("❌ Nenhuma partida encontrada")
        return []
    
    def buscar_estatisticas_jogo(self, match_id: int) -> Optional[Dict]:
        """
        Busca estatísticas completas de uma partida
        Endpoint: /event/{MATCH_ID}/statistics
        """
        return self._get(f"event/{match_id}/statistics")
    
    def buscar_lineups(self, match_id: int) -> Optional[Dict]:
        """
        Busca escalações de uma partida
        Endpoint: /event/{MATCH_ID}/lineups
        """
        return self._get(f"event/{match_id}/lineups")
    
    def buscar_detalhes_jogo(self, match_id: int) -> Optional[Dict]:
        """
        Busca detalhes completos de uma partida
        Endpoint: /event/{MATCH_ID}
        """
        return self._get(f"event/{match_id}")
    
    def buscar_stats_jogador_temporada(self, player_id: int, season_id: int) -> Optional[Dict]:
        """
        Busca estatísticas de um jogador na temporada
        Endpoint: /player/{PLAYER_ID}/statistics/season/{SEASON_ID}
        """
        return self._get(f"player/{player_id}/statistics/season/{season_id}")
    
    def extrair_jogadores_de_partidas(self, season_id: int, max_partidas: int = 10) -> Dict[int, Dict]:
        """
        Extrai todos os jogadores únicos a partir das partidas
        Retorna dict: {player_id: {nome, time, posicao, etc}}
        """
        print(f"\n👥 Extraindo jogadores das partidas...")
        
        partidas = self.listar_partidas_temporada(season_id)
        jogadores = {}
        
        for idx, partida in enumerate(partidas[:max_partidas], 1):
            match_id = partida.get('id')
            home_team = partida.get('homeTeam', {}).get('name')
            away_team = partida.get('awayTeam', {}).get('name')
            
            print(f"\n[{idx}/{min(max_partidas, len(partidas))}] {home_team} vs {away_team}")
            
            # Buscar lineups
            lineups = self.buscar_lineups(match_id)
            
            if lineups:
                # Home team
                if 'home' in lineups:
                    for player_data in lineups['home'].get('players', []):
                        player = player_data.get('player', {})
                        player_id = player.get('id')
                        
                        if player_id and player_id not in jogadores:
                            jogadores[player_id] = {
                                'id': player_id,
                                'nome': player.get('name'),
                                'time': home_team,
                                'posicao': player.get('position'),
                                'numero_camisa': player.get('jerseyNumber'),
                                'foto_url': f"https://img.sofascore.com/api/v1/player/{player_id}/image"
                            }
                            print(f"   ✅ {player.get('name')} ({home_team})")
                
                # Away team
                if 'away' in lineups:
                    for player_data in lineups['away'].get('players', []):
                        player = player_data.get('player', {})
                        player_id = player.get('id')
                        
                        if player_id and player_id not in jogadores:
                            jogadores[player_id] = {
                                'id': player_id,
                                'nome': player.get('name'),
                                'time': away_team,
                                'posicao': player.get('position'),
                                'numero_camisa': player.get('jerseyNumber'),
                                'foto_url': f"https://img.sofascore.com/api/v1/player/{player_id}/image"
                            }
                            print(f"   ✅ {player.get('name')} ({away_team})")
        
        print(f"\n✅ Total de jogadores únicos: {len(jogadores)}")
        return jogadores
    
    def buscar_elenco_time(self, team_id: int, season_id: int) -> List[Dict]:
        """
        Busca elenco completo de um time
        Endpoint: /team/{TEAM_ID}/players
        """
        print(f"   🔍 Buscando elenco...")
        data = self._get(f"team/{team_id}/players")
        
        if data and 'players' in data:
            jogadores = []
            for player_data in data['players']:
                player = player_data.get('player', {})
                jogadores.append({
                    'id': player.get('id'),
                    'nome': player.get('name'),
                    'posicao': player.get('position'),
                    'numero_camisa': player.get('jerseyNumber'),
                    'nacionalidade': player.get('country', {}).get('alpha3Code'),
                    'altura': player.get('height'),
                    'idade': self._calcular_idade(player.get('dateOfBirthTimestamp')),
                    'foto_url': f"https://img.sofascore.com/api/v1/player/{player.get('id')}/image"
                })
            print(f"   ✅ {len(jogadores)} jogadores encontrados")
            return jogadores
        return []
    
    def _calcular_idade(self, timestamp: Optional[int]) -> Optional[int]:
        """Calcula idade a partir de timestamp"""
        if timestamp:
            from datetime import datetime
            birth = datetime.fromtimestamp(timestamp)
            hoje = datetime.now()
            return hoje.year - birth.year - ((hoje.month, hoje.day) < (birth.month, birth.day))
        return None
    
    def buscar_ultimas_partidas_time(self, team_id: int, limit: int = 10) -> List[Dict]:
        """
        Busca últimas partidas de um time
        Endpoint: /team/{TEAM_ID}/events/last/0
        """
        print(f"   📅 Buscando últimas {limit} partidas...")
        data = self._get(f"team/{team_id}/events/last/0")
        
        if data and 'events' in data:
            partidas = []
            for event in data['events'][:limit]:
                home = event.get('homeTeam', {})
                away = event.get('awayTeam', {})
                score = event.get('homeScore', {})
                
                resultado = None
                if home.get('id') == team_id:
                    if score.get('current') > event.get('awayScore', {}).get('current', 0):
                        resultado = 'V'
                    elif score.get('current') < event.get('awayScore', {}).get('current', 0):
                        resultado = 'D'
                    else:
                        resultado = 'E'
                else:
                    if event.get('awayScore', {}).get('current') > score.get('current', 0):
                        resultado = 'V'
                    elif event.get('awayScore', {}).get('current') < score.get('current', 0):
                        resultado = 'D'
                    else:
                        resultado = 'E'
                
                partidas.append({
                    'data': event.get('startTimestamp'),
                    'casa': home.get('name'),
                    'fora': away.get('name'),
                    'placar': f"{score.get('current', 0)}-{event.get('awayScore', {}).get('current', 0)}",
                    'resultado': resultado
                })
            
            vitorias = sum(1 for p in partidas if p['resultado'] == 'V')
            empates = sum(1 for p in partidas if p['resultado'] == 'E')
            derrotas = sum(1 for p in partidas if p['resultado'] == 'D')
            
            print(f"   ✅ Últimas {len(partidas)}: {vitorias}V {empates}E {derrotas}D")
            return partidas
        return []
    
    def atualizar_time_completo(self, nome_time: str, team_id: int, season_id: int):
        """
        Atualiza elenco + stats de jogadores + histórico de partidas de UM time
        """
        print(f"\n{'='*70}")
        print(f"🔥 {nome_time.upper()}")
        print(f"{'='*70}")
        
        # 1. Buscar elenco
        elenco = self.buscar_elenco_time(team_id, season_id)
        
        # 2. Buscar últimas partidas
        partidas = self.buscar_ultimas_partidas_time(team_id)
        
        # 3. Para cada jogador, buscar stats individuais
        print(f"\n   📊 Buscando estatísticas dos jogadores...")
        jogadores_completos = []
        
        for idx, jogador in enumerate(elenco, 1):
            player_id = jogador['id']
            print(f"   [{idx}/{len(elenco)}] {jogador['nome']}", end=' ')
            
            stats = self.buscar_stats_jogador_temporada(player_id, season_id)
            
            if stats and 'statistics' in stats:
                s = stats['statistics']
                jogador.update({
                    'time': nome_time,
                    'time_id': team_id,
                    'partidas': s.get('appearances', 0),
                    'gols': s.get('goals', 0),
                    'assistencias': s.get('assists', 0),
                    'rating': float(s.get('rating', 0)),
                    'cartoes_amarelos': s.get('yellowCards', 0),
                    'cartoes_vermelhos': s.get('redCards', 0),
                    'sofascore_id': player_id,
                    'season': 2025 if season_id > 62000 else 2024
                })
                print(f"→ {s.get('appearances', 0)}j {s.get('goals', 0)}g")
            else:
                jogador.update({
                    'time': nome_time,
                    'time_id': team_id,
                    'partidas': 0,
                    'gols': 0,
                    'assistencias': 0,
                    'rating': 0,
                    'sofascore_id': player_id,
                    'season': 2025 if season_id > 62000 else 2024
                })
                print("→ sem stats")
            
            jogadores_completos.append(jogador)
        
        # 4. Retornar tudo
        return {
            'time': nome_time,
            'team_id': team_id,
            'jogadores': jogadores_completos,
            'ultimas_partidas': partidas,
            'season': 2025 if season_id > 62000 else 2024
        }


def main():
    """
    Atualiza Flamengo com elenco completo + stats + histórico
    """
    scraper = SofaScoreScraper()
    
    # IDs do SofaScore
    TIMES_BRASILEIRAO = {
        'Flamengo': 5981,
        'Palmeiras': 5957,
        'Botafogo': 1958,
        'São Paulo': 5947,
        'Corinthians': 5926,
        'Atlético-MG': 1947,
        'Grêmio': 5933,
        'Fluminense': 5930,
        'Cruzeiro': 1963,
        'Vasco': 5998,
        'Internacional': 5925,
        'Bahia': 1943,
        'RB Bragantino': 6002,
        'Athletico-PR': 1950,
        'Fortaleza': 1973,
        'Juventude': 1968,
        'Vitória': 1997,
        'Cuiabá': 24264,
        'Atlético-GO': 1957,
        'Criciúma': 1964
    }
    
    # Descobrir Season ID
    season_id = scraper.descobrir_season_id(2025)
    if not season_id:
        print("⚠️  2025 não disponível, usando 2024...")
        season_id = scraper.descobrir_season_id(2024)
    
    if not season_id:
        print("❌ Nenhuma season disponível!")
        return
    
    # Atualizar apenas Flamengo por enquanto
    time = 'Flamengo'
    team_id = TIMES_BRASILEIRAO[time]
    
    dados = scraper.atualizar_time_completo(time, team_id, season_id)
    
    # Carregar jogadores existentes
    try:
        with open('data/jogadores.json', 'r', encoding='utf-8') as f:
            jogadores_existentes = json.load(f)
    except:
        jogadores_existentes = []
    
    # Remover jogadores antigos do Flamengo
    jogadores_outros = [j for j in jogadores_existentes if j.get('time') != time]
    
    # Adicionar novos jogadores do Flamengo
    jogadores_atualizados = jogadores_outros + dados['jogadores']
    
    # Salvar jogadores
    with open('data/jogadores.json', 'w', encoding='utf-8') as f:
        json.dump(jogadores_atualizados, f, ensure_ascii=False, indent=2)
    
    # Atualizar times.json
    try:
        with open('data/times.json', 'r', encoding='utf-8') as f:
            times = json.load(f)
    except:
        times = []
    
    # Remover Flamengo antigo
    times = [t for t in times if t.get('nome') != time]
    
    # Adicionar Flamengo atualizado
    times.append({
        'id': team_id,
        'nome': time,
        'season': dados['season'],
        'jogadores': [j['nome'] for j in dados['jogadores']],
        'ultimas_partidas': dados['ultimas_partidas']
    })
    
    with open('data/times.json', 'w', encoding='utf-8') as f:
        json.dump(times, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ {time} ATUALIZADO!")
    print(f"   Jogadores: {len(dados['jogadores'])}")
    print(f"   Partidas registradas: {len(dados['ultimas_partidas'])}")
    print(f"   Total requests: {scraper.request_count}")
    print(f"   Tempo: ~{scraper.request_count * 3 / 60:.1f} minutos")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
