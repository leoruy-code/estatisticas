"""
Busca dados completos de jogadores no SofaScore
Inclui foto e estatísticas detalhadas por temporada
"""

import json
import time
import random
import requests
from typing import Dict, Any, Optional

# Configurações conservadoras
MIN_DELAY = 3
MAX_DELAY = 6
TIMEOUT = 30

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class SofaScoreAPI:
    """API do SofaScore para buscar dados de jogadores"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.sofascore.com/api/v1"
        self.request_count = 0
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
        }
    
    def _delay(self):
        """Delay aleatório entre requests"""
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    def buscar_jogador_por_nome(self, nome: str, time: str = None) -> Optional[Dict]:
        """
        Busca jogador pelo nome usando API de search
        Retorna dados básicos incluindo ID do SofaScore
        """
        self._delay()
        
        url = f"{self.base_url}/search/all"
        params = {'q': nome}
        
        try:
            response = self.session.get(
                url, 
                headers=self._get_headers(),
                params=params,
                timeout=TIMEOUT
            )
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Procurar em resultados de jogadores
                for result in data.get('results', []):
                    if result.get('type') == 'player':
                        player = result.get('entity', {})
                        
                        # Se time foi especificado, validar
                        if time:
                            player_team = player.get('team', {}).get('name', '')
                            if time.lower() not in player_team.lower():
                                continue
                        
                        print(f"   ✅ Encontrado: {player.get('name')} (ID: {player.get('id')})")
                        return player
                
                print(f"   ⚠️  Jogador '{nome}' não encontrado")
                return None
            else:
                print(f"   ❌ Erro {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro ao buscar '{nome}': {e}")
            return None
    
    def buscar_estatisticas_temporada(self, player_id: int, tournament_id: int = 325) -> Optional[Dict]:
        """
        Busca estatísticas detalhadas de um jogador na temporada
        Endpoint: /player/{id}/statistics/seasons
        
        tournament_id 325 = Brasileirão Série A
        """
        self._delay()
        
        # Endpoint correto: buscar todas as temporadas e filtrar
        url = f"{self.base_url}/player/{player_id}/statistics/seasons"
        
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=TIMEOUT
            )
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Procurar pela temporada do Brasileirão 2025, se não houver tentar 2024
                if 'uniqueTournamentSeasons' in data:
                    # Tentar 2025 primeiro
                    for season_data in data['uniqueTournamentSeasons']:
                        tournament = season_data.get('uniqueTournament', {})
                        season = season_data.get('season', {})
                        
                        if tournament.get('id') == tournament_id and season.get('year') == '2025':
                            print(f"   ✅ Stats 2025 encontradas")
                            return season_data.get('statistics', {})
                    
                    # Fallback para 2024 se não houver 2025
                    for season_data in data['uniqueTournamentSeasons']:
                        tournament = season_data.get('uniqueTournament', {})
                        season = season_data.get('season', {})
                        
                        if tournament.get('id') == tournament_id and season.get('year') == '2024':
                            print(f"   ⚠️  Usando stats 2024 (2025 indisponível)")
                            return season_data.get('statistics', {})
                
                print(f"   ⚠️  Brasileirão 2024/2025 não encontrado nas stats")
                return None
            else:
                print(f"   ⚠️  Stats não disponíveis (status {response.status_code})")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro ao buscar stats: {e}")
            return None
    
    def extrair_estatisticas(self, stats_data: Dict) -> Dict:
        """
        Extrai estatísticas do formato SofaScore para nosso formato
        """
        if not stats_data:
            return {}
        
        stats = stats_data
        
        # Mapeamento de campos
        result = {
            'partidas': stats.get('appearances', 0),
            'gols': stats.get('goals', 0),
            'assistencias': stats.get('assists', 0),
            'rating': float(stats.get('rating', 0)),
            
            # Estatísticas detalhadas de ataque
            'gols_esperados': float(stats.get('expectedGoals', 0)),
            'finalizacoes': stats.get('totalShots', 0),
            'chutes_no_gol': stats.get('shotsOnTarget', 0),
            'grandes_chances_perdidas': stats.get('bigChancesMissed', 0),
            'conversao_gols': stats.get('goalConversionPercentage', 0),
            
            # Estatísticas de passe
            'acoes_com_bola': stats.get('touches', 0),
            'grandes_chances_criadas': stats.get('bigChancesCreated', 0),
            'passes_decisivos': stats.get('keyPasses', 0),
            'passes_certos': stats.get('accuratePasses', 0),
            'total_passes': stats.get('totalPasses', 0),
            'percentual_passes': stats.get('accuratePassesPercentage', 0),
            
            # Estatísticas defensivas
            'interceptacoes': stats.get('interceptions', 0),
            'desarmes': stats.get('tackles', 0),
            'bolas_recuperadas': stats.get('ballsRecovered', 0),
            'duelos_ganhos': stats.get('duelsWon', 0),
            'total_duelos': stats.get('totalDuels', 0),
            
            # Dribles
            'dribles_certos': stats.get('successfulDribbles', 0),
            'total_dribles': stats.get('totalDribbles', 0),
            
            # Disciplina
            'cartoes_amarelos': stats.get('yellowCards', 0),
            'cartoes_vermelhos': stats.get('redCards', 0),
            'faltas_cometidas': stats.get('fouls', 0),
            'faltas_sofridas': stats.get('wasFouled', 0),
        }
        
        return result


def atualizar_jogadores_flamengo():
    """
    Atualiza todos os jogadores do Flamengo com dados do SofaScore
    """
    api = SofaScoreAPI()
    
    # Carregar jogadores
    with open('data/jogadores.json', 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    flamengo = [j for j in jogadores if j.get('time') == 'Flamengo']
    
    print(f"🔍 Buscando dados de {len(flamengo)} jogadores do Flamengo...")
    print("=" * 70)
    
    atualizados_foto = 0
    atualizados_stats = 0
    
    for idx, jogador in enumerate(flamengo, 1):
        nome = jogador['nome']
        print(f"\n[{idx}/{len(flamengo)}] 🔎 {nome}")
        
        # Buscar jogador no SofaScore
        sofascore_player = api.buscar_jogador_por_nome(nome, "Flamengo")
        
        if sofascore_player:
            player_id = sofascore_player.get('id')
            
            # Adicionar foto
            foto_url = f"https://img.sofascore.com/api/v1/player/{player_id}/image"
            jogador['foto_url'] = foto_url
            jogador['sofascore_id'] = player_id
            atualizados_foto += 1
            print(f"   ✅ Foto adicionada (ID: {player_id})")
            
            # Buscar estatísticas da temporada 2024 (tournament_id 325 = Brasileirão)
            stats_data = api.buscar_estatisticas_temporada(player_id, 325)
            
            if stats_data:
                stats = api.extrair_estatisticas(stats_data)
                jogador.update(stats)
                
                print(f"   ✅ Stats: {stats.get('partidas', 0)} jogos | {stats.get('gols', 0)} gols | {stats.get('assistencias', 0)} assist | rating {stats.get('rating', 0):.2f}")
                atualizados_stats += 1
                
                # Salvar a cada jogador atualizado (segurança)
                with open('data/jogadores.json', 'w', encoding='utf-8') as f:
                    json.dump(jogadores, f, ensure_ascii=False, indent=2)
                print(f"   💾 Salvo!")
            else:
                print(f"   ⚠️  Sem stats disponíveis para 2024")
        else:
            print(f"   ❌ Não encontrado no SofaScore")
        
        # Mostrar progresso
        print(f"   📊 Progresso: {atualizados_foto} fotos | {atualizados_stats} stats completos")
    
    print("\n" + "=" * 70)
    print(f"✅ CONCLUÍDO!")
    print(f"   Fotos adicionadas: {atualizados_foto}/{len(flamengo)}")
    print(f"   Stats completos: {atualizados_stats}/{len(flamengo)}")
    print(f"   Total de requests: {api.request_count}")
    print(f"   Tempo total: ~{api.request_count * 4.5 / 60:.1f} minutos")


if __name__ == '__main__':
    atualizar_jogadores_flamengo()
