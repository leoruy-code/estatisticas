"""
Scraper COMPLETO do SofaScore com TODAS as estatísticas detalhadas
Baseado nos endpoints reais das páginas de jogador e time
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

BRASILEIRAO_ID = 325

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class SofaScoreCompleto:
    """Scraper completo com todas as estatísticas detalhadas"""
    
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
        """Request genérico"""
        self._delay()
        url = f"{BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, headers=self._headers(), timeout=TIMEOUT)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    def descobrir_season_id(self, year: int = 2025) -> Optional[int]:
        """Descobre Season ID para um ano"""
        print(f"🔍 Descobrindo Season ID para {year}...")
        
        data = self._get(f"unique-tournament/{BRASILEIRAO_ID}/seasons")
        
        if data and 'seasons' in data:
            for season in data['seasons']:
                if season.get('year') == str(year):
                    season_id = season.get('id')
                    print(f"✅ Season {year} ID: {season_id}")
                    return season_id
        
        print(f"⚠️  Season {year} não encontrada")
        return None
    
    def buscar_elenco_time(self, team_id: int) -> List[Dict]:
        """Busca elenco completo do time"""
        print(f"   👥 Buscando elenco...")
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
                })
            print(f"   ✅ {len(jogadores)} jogadores")
            return jogadores
        return []
    
    def _calcular_idade(self, timestamp: Optional[int]) -> Optional[int]:
        if timestamp:
            from datetime import datetime
            birth = datetime.fromtimestamp(timestamp)
            hoje = datetime.now()
            return hoje.year - birth.year - ((hoje.month, hoje.day) < (birth.month, birth.day))
        return None
    
    def buscar_stats_jogador_completas(self, player_id: int, season_id: int) -> Dict:
        """
        Busca estatísticas do jogador na temporada (todas competições somadas quando disponível).
        Preferência: /player/{ID}/statistics/season/{SEASON_ID}
        Fallback: /player/{ID}/statistics/seasons agregando todas competições daquele season.
        """
        # 1) Tentar endpoint direto por temporada
        direct = self._get(f"player/{player_id}/statistics/season/{season_id}")
        stats = None
        if direct and isinstance(direct, dict) and direct.get('statistics'):
            stats = direct['statistics']
        else:
            # 2) Fallback: agregar via seasons
            data = self._get(f"player/{player_id}/statistics/seasons")
            if not data or 'uniqueTournamentSeasons' not in data:
                return {}
            stats_agregadas: Dict[str, Any] = {}
            competicoes = 0
            for ts in data['uniqueTournamentSeasons']:
                season = ts.get('season', {})
                if season.get('id') != season_id and season.get('year') != str(season_id):
                    continue
                s = ts.get('statistics', {})
                if not s:
                    continue
                competicoes += 1
                for k, v in s.items():
                    if isinstance(v, (int, float)):
                        stats_agregadas[k] = stats_agregadas.get(k, 0) + v
                    else:
                        stats_agregadas.setdefault(k, v)
            if competicoes == 0:
                return {}
            stats = stats_agregadas
        return {
            'partidas': stats.get('appearances', 0),
            'gols': stats.get('goals', 0),
            'assistencias': stats.get('assists', 0),
            'rating': round(float(stats.get('rating', 0)), 2),
            'gols_esperados_xg': round(float(stats.get('expectedGoals', 0)), 2),
            'frequencia_gols_min': stats.get('goalFrequency'),
            'gols_por_partida': round(float(stats.get('goalsPerGame', 0)), 1),
            'finalizacoes': stats.get('totalShots', 0),
            'chutes_no_gol': stats.get('shotsOnTarget', 0),
            'grandes_chances_perdidas': stats.get('bigChancesMissed', 0),
            'conversao_gols_pct': stats.get('goalConversionPercentage', 0),
            'gols_de_falta': stats.get('freeKickGoal', 0),
            'eficacia_gols_livres_pct': stats.get('freeKickGoalConversion'),
            'gols_dentro_area': stats.get('goalsInsideBox', 0),
            'gols_fora_area': stats.get('goalsOutsideBox', 0),
            'gols_cabeca': stats.get('headedGoals', 0),
            'gols_pe_esquerdo': stats.get('leftFootGoals', 0),
            'gols_pe_direito': stats.get('rightFootGoals', 0),
            'penaltis_sofridos': stats.get('penaltiesWon', 0),
            'interceptacoes': round(float(stats.get('interceptions', 0)), 1),
            'desarmes_por_jogo': round(float(stats.get('tacklesPerGame', 0)), 1),
            'bolas_recuperadas_ataque': round(float(stats.get('ballRecoveryInOpponentsHalf', 0)), 1),
            'bolas_recuperadas_por_jogo': round(float(stats.get('ballsRecoveredPerGame', 0)), 1),
            'dribles_sofridos_por_jogo': round(float(stats.get('dribbledPastPerGame', 0)), 1),
            'cortes_por_jogo': round(float(stats.get('clearancesPerGame', 0)), 1),
            'chutes_bloqueados_por_jogo': round(float(stats.get('blockedShotsPerGame', 0)), 2),
            'erros_levaram_finalizacao': stats.get('errorLeadToShot', 0),
            'erros_levaram_gol': stats.get('errorLeadToGoal', 0),
            'penaltis_cometidos': stats.get('penaltiesConceded', 0),
            'cartoes_amarelos': stats.get('yellowCards', 0),
            'vermelhos_2_amarelos': stats.get('yellowRedCards', 0),
            'cartoes_vermelhos': stats.get('redCards', 0),
            'assistencias_esperadas_xa': round(float(stats.get('expectedAssists', 0)), 2),
            'acoes_com_bola': round(float(stats.get('touches', 0)), 1),
            'grandes_chances_criadas': stats.get('bigChancesCreated', 0),
            'passes_decisivos': round(float(stats.get('keyPasses', 0)), 1),
            'passes_certos': round(float(stats.get('accuratePasses', 0)), 1),
            'passes_certos_pct': round(float(stats.get('accuratePassesPercentage', 0)), 1),
            'passes_proprio_campo': round(float(stats.get('accurateOwnHalfPasses', 0)), 1),
            'passes_terco_final': round(float(stats.get('accurateFinalThirdPasses', 0)), 1),
            'passes_longos_certos': round(float(stats.get('accurateLongBalls', 0)), 1),
            'passes_longos_pct': round(float(stats.get('longBallsWinPercentage', 0)), 1),
            'passes_tensos_certos': round(float(stats.get('accurateThroughBalls', 0)), 1),
            'cruzamentos_certos': round(float(stats.get('accurateCrosses', 0)), 1),
            'cruzamentos_pct': round(float(stats.get('crossesWinPercentage', 0)), 1),
            'dribles_certos': round(float(stats.get('successfulDribbles', 0)), 1),
            'dribles_pct': round(float(stats.get('successfulDribblesPercentage', 0)), 1),
            'duelos_chao_ganhos': round(float(stats.get('groundDuelsWon', 0)), 1),
            'duelos_aereos_ganhos': round(float(stats.get('aerialDuelsWon', 0)), 1),
            'duelos_aereos_pct': round(float(stats.get('aerialDuelsWonPercentage', 0)), 1),
            'perda_posse_bola_por_jogo': round(float(stats.get('possessionLostPerGame', 0)), 1),
            'faltas_por_jogo': round(float(stats.get('foulsPerGame', 0)), 1),
            'faltas_sofridas': round(float(stats.get('wasFouled', 0)), 1),
            'impedimentos': round(float(stats.get('offsides', 0)), 2),
            'foto_url': f"https://img.sofascore.com/api/v1/player/{player_id}/image",
            'sofascore_id': player_id
        }
    
    def buscar_stats_time_agregadas(self, team_id: int, season_id: int) -> Dict:
        """
        Busca estatísticas agregadas do time (Foto 3)
        Endpoint: /team/{TEAM_ID}/statistics/season/{SEASON_ID}
        """
        print(f"   📊 Buscando stats do time...")
        data = self._get(f"team/{team_id}/statistics/season/{season_id}")
        
        if data and 'statistics' in data:
            s = data['statistics']
            return {
                # ATACANDO
                'gols_por_partida': round(float(s.get('avgGoals', 0)), 1),
                'gols_penalti': s.get('penaltyGoals', 0),
                'gols_falta': s.get('freeKickGoal', 0),
                'gols_dentro_area': s.get('goalsFromInsideBox', 0),
                'gols_fora_area': s.get('goalsFromOutsideBox', 0),
                'gols_pe_esquerdo': s.get('leftFootGoals', 0),
                'gols_pe_direito': s.get('rightFootGoals', 0),
                'gols_cabeca': s.get('headedGoals', 0),
                'grandes_chances_gol_por_jogo': round(float(s.get('bigChancesPerGame', 0)), 1),
                'grandes_chances_perdidas_por_jogo': round(float(s.get('bigChancesMissedPerGame', 0)), 1),
                'total_finalizacoes_por_jogo': round(float(s.get('shotsPerGame', 0)), 1),
                'chutes_certos_por_jogo': round(float(s.get('shotsOnTargetPerGame', 0)), 1),
                'chutes_errados_por_jogo': round(float(s.get('shotsOffTargetPerGame', 0)), 1),
                'chutes_bloqueados_por_jogo': round(float(s.get('blockedShotsPerGame', 0)), 1),
                'dribles_certos_por_jogo': round(float(s.get('successfulDribblesPerGame', 0)), 1),
                'escanteios_por_jogo': round(float(s.get('cornersPerGame', 0)), 1),
                'faltas_tiros_diretos_por_jogo': round(float(s.get('freeKicksPerGame', 0)), 1),
                'finalizacoes_na_trave': s.get('hitWoodwork', 0),
                'contra_ataques': s.get('counterAttacks', 0),
                
                # PASSES
                'posse_bola_pct': round(float(s.get('possessionPercentage', 0)), 1),
                'passes_certos': s.get('accuratePasses', 0),
                'passes_certos_pct': round(float(s.get('accuratePassesPercentage', 0)), 1),
                'passes_proprio_campo': s.get('accurateOwnHalfPasses', 0),
                'passes_terco_final': s.get('accurateFinalThirdPasses', 0),
                'bolas_longas': round(float(s.get('longBalls', 0)), 1),
                'bolas_longas_pct': round(float(s.get('longBallsWinPercentage', 0)), 1),
                'cruzamentos_certos': round(float(s.get('accurateCrosses', 0)), 1),
                'cruzamentos_pct': round(float(s.get('crossesWinPercentage', 0)), 1),
                
                # DEFENDENDO
                'jogos_sem_sofrer_gols': s.get('cleanSheets', 0),
                'gols_sofridos_por_jogo': round(float(s.get('goalsConcededPerGame', 0)), 1),
                'desarmes_por_jogo': round(float(s.get('tacklesPerGame', 0)), 1),
                'interceptacoes_por_jogo': round(float(s.get('interceptionsPerGame', 0)), 1),
                'cortes_por_jogo': round(float(s.get('clearancesPerGame', 0)), 1),
                'defesas_por_jogo': round(float(s.get('savesPerGame', 0)), 1),
                'bolas_recuperadas_por_jogo': round(float(s.get('ballRecoveriesPerGame', 0)), 1),
                'erros_levaram_finalizacao': s.get('errorsLeadingToShot', 0),
                'erros_levaram_gol': s.get('errorsLeadingToGoal', 0),
                'penaltis_cometidos': s.get('penaltiesConceded', 0),
                'gols_penalti_concedidos': s.get('penaltyGoalsConceded', 0),
                'tirar_em_cima_linha': s.get('goallineClearances', 0),
                'ultimo_homem_desarmar': s.get('lastManTackle', 0),
                
                # OUTROS
                'desarmes_por_partida': round(float(s.get('tacklesPerGame', 0)), 1),
                'duelos_ganhos_chao': round(float(s.get('groundDuelsWon', 0)), 1),
                'duelos_chao_pct': round(float(s.get('groundDuelsWonPercentage', 0)), 1),
                'duelos_aereos_ganhos': round(float(s.get('aerialDuelsWon', 0)), 1),
                'duelos_aereos_pct': round(float(s.get('aerialDuelsWonPercentage', 0)), 1),
                'perda_posse_bola_por_jogo': round(float(s.get('possessionLostPerGame', 0)), 1),
                'laterais_por_jogo': s.get('throwInsPerGame', 0),
                'tiros_meta_por_jogo': round(float(s.get('goalKicksPerGame', 0)), 1),
                'impedimentos_por_jogo': round(float(s.get('offsidesPerGame', 0)), 1),
                'faltas_por_jogo': round(float(s.get('foulsPerGame', 0)), 1),
                'cartoes_amarelos_por_partida': round(float(s.get('yellowCardsPerGame', 0)), 1),
                'cartoes_vermelhos': s.get('redCards', 0),
            }
        return {}
    
    def buscar_ultimas_partidas(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Busca últimas partidas do time"""
        print(f"   📅 Últimas {limit} partidas...")
        data = self._get(f"team/{team_id}/events/last/0")
        
        if data and 'events' in data:
            partidas = []
            for event in data['events'][:limit]:
                home = event.get('homeTeam', {})
                away = event.get('awayTeam', {})
                h_score = event.get('homeScore', {}).get('current', 0)
                a_score = event.get('awayScore', {}).get('current', 0)
                
                if home.get('id') == team_id:
                    resultado = 'V' if h_score > a_score else ('D' if h_score < a_score else 'E')
                else:
                    resultado = 'V' if a_score > h_score else ('D' if a_score < h_score else 'E')
                
                partidas.append({
                    'data': event.get('startTimestamp'),
                    'casa': home.get('name'),
                    'fora': away.get('name'),
                    'placar': f"{h_score}-{a_score}",
                    'resultado': resultado
                })
            
            v = sum(1 for p in partidas if p['resultado'] == 'V')
            e = sum(1 for p in partidas if p['resultado'] == 'E')
            d = sum(1 for p in partidas if p['resultado'] == 'D')
            print(f"   ✅ {v}V {e}E {d}D")
            return partidas
        return []
    
    def atualizar_flamengo_completo(self, team_id: int = 5981):
        """Atualiza Flamengo com TODAS as estatísticas"""
        
        print("🔥 FLAMENGO - ATUALIZAÇÃO COMPLETA")
        print("=" * 70)
        
        # 1. Descobrir season
        season_id = self.descobrir_season_id(2025)
        if not season_id:
            season_id = self.descobrir_season_id(2024)
        
        if not season_id:
            print("❌ Season não encontrada!")
            return
        
        # 2. Buscar elenco
        elenco = self.buscar_elenco_time(team_id)
        
        # 3. Stats agregadas do time
        stats_time = self.buscar_stats_time_agregadas(team_id, season_id)
        
        # 4. Últimas partidas
        partidas = self.buscar_ultimas_partidas(team_id)
        
        # 5. Stats detalhadas de cada jogador
        print(f"\n📊 Coletando stats de {len(elenco)} jogadores...")
        jogadores_completos = []
        
        for idx, jogador in enumerate(elenco, 1):
            player_id = jogador['id']
            nome = jogador['nome']
            print(f"[{idx}/{len(elenco)}] {nome}", end=' ')
            
            stats = self.buscar_stats_jogador_completas(player_id, season_id)
            
            if stats:
                jogador.update(stats)
                jogador.update({
                    'time': 'Flamengo',
                    'time_id': team_id,
                    'season': 2025 if season_id > 62000 else 2024
                })
                print(f"→ {stats.get('partidas', 0)}j {stats.get('gols', 0)}g ⭐{stats.get('rating', 0)}")
            else:
                jogador.update({
                    'time': 'Flamengo',
                    'time_id': team_id,
                    'season': 2025 if season_id > 62000 else 2024,
                    'partidas': 0,
                    'gols': 0,
                    'rating': 0,
                    'foto_url': f"https://img.sofascore.com/api/v1/player/{player_id}/image",
                    'sofascore_id': player_id
                })
                print("→ sem stats")
            
            jogadores_completos.append(jogador)
        
        # 6. Salvar jogadores
        with open('data/jogadores.json', 'w', encoding='utf-8') as f:
            json.dump(jogadores_completos, f, ensure_ascii=False, indent=2)
        
        # 7. Salvar time
        time_data = {
            'id': team_id,
            'nome': 'Flamengo',
            'season': 2025 if season_id > 62000 else 2024,
            'jogadores': [j['nome'] for j in jogadores_completos],
            'estatisticas': stats_time,
            'ultimas_partidas': partidas
        }
        
        with open('data/times.json', 'w', encoding='utf-8') as f:
            json.dump([time_data], f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 70)
        print("✅ FLAMENGO ATUALIZADO!")
        print(f"   Jogadores: {len(jogadores_completos)}")
        print(f"   Com stats: {sum(1 for j in jogadores_completos if j.get('partidas', 0) > 0)}")
        print(f"   Partidas: {len(partidas)}")
        print(f"   Requests: {self.request_count}")
        print("=" * 70)


if __name__ == '__main__':
    scraper = SofaScoreCompleto()
    scraper.atualizar_flamengo_completo()
