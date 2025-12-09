"""
SofaScore Scraper - Série A 2025
================================
Scraper profissional para coletar dados atualizados do Brasileirão.

Seguindo boas práticas:
- Rate limiting com jitter
- Estrutura de dados com dataclasses
- Cache local para evitar requisições repetidas
- Logs detalhados
- Tratamento de erros robusto
"""

import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== MODELOS DE DADOS ====================

@dataclass
class PlayerStats:
    """Estatísticas de um jogador."""
    jogos: int = 0
    minutos: int = 0
    gols: int = 0
    assistencias: int = 0
    chutes: int = 0
    chutes_no_gol: int = 0
    passes: int = 0
    passes_certos: int = 0
    dribles: int = 0
    dribles_certos: int = 0
    duelos: int = 0
    duelos_ganhos: int = 0
    faltas_cometidas: int = 0
    faltas_sofridas: int = 0
    cartoes_amarelos: int = 0
    cartoes_vermelhos: int = 0
    impedimentos: int = 0
    cruzamentos: int = 0
    passes_chave: int = 0
    grandes_chances_criadas: int = 0
    grandes_chances_perdidas: int = 0
    xg: float = 0.0
    xa: float = 0.0
    
    # Médias por 90 minutos (calculadas)
    gols_por_90: float = 0.0
    chutes_por_90: float = 0.0
    chutes_gol_por_90: float = 0.0
    faltas_por_90: float = 0.0
    cartoes_por_90: float = 0.0
    xg_por_90: float = 0.0


@dataclass
class Player:
    """Jogador com estatísticas."""
    id: int
    nome: str
    time: str
    time_id: int
    posicao: str = ""
    idade: int = 0
    nacionalidade: str = ""
    altura: int = 0  # cm
    pe_preferido: str = ""
    numero_camisa: Optional[int] = None
    valor_mercado: Optional[float] = None
    stats: PlayerStats = field(default_factory=PlayerStats)
    
    def calcular_medias_por_90(self):
        """Calcula estatísticas por 90 minutos."""
        if self.stats.minutos > 0:
            fator = 90 / self.stats.minutos
            self.stats.gols_por_90 = round(self.stats.gols * fator, 2)
            self.stats.chutes_por_90 = round(self.stats.chutes * fator, 2)
            self.stats.chutes_gol_por_90 = round(self.stats.chutes_no_gol * fator, 2)
            self.stats.faltas_por_90 = round(self.stats.faltas_cometidas * fator, 2)
            self.stats.cartoes_por_90 = round((self.stats.cartoes_amarelos + self.stats.cartoes_vermelhos) * fator, 2)
            self.stats.xg_por_90 = round(self.stats.xg * fator, 2)


@dataclass  
class TeamStats:
    """Estatísticas agregadas do time."""
    jogos: int = 0
    vitorias: int = 0
    empates: int = 0
    derrotas: int = 0
    gols_marcados: int = 0
    gols_sofridos: int = 0
    
    # Médias por jogo
    gols_marcados_media: float = 0.0
    gols_sofridos_media: float = 0.0
    chutes_media: float = 0.0
    chutes_gol_media: float = 0.0
    posse_media: float = 0.0
    escanteios_media: float = 0.0
    faltas_media: float = 0.0
    cartoes_media: float = 0.0
    
    # Força relativa
    attack_strength: float = 1.0
    defense_weakness: float = 1.0


@dataclass
class Team:
    """Time com jogadores e estatísticas."""
    id: int
    nome: str
    nome_curto: str = ""
    liga: str = "Brasileirão Série A"
    temporada: int = 2025
    escudo_url: str = ""
    jogadores: List[Player] = field(default_factory=list)
    stats: TeamStats = field(default_factory=TeamStats)
    partidas: List[Dict] = field(default_factory=list)


@dataclass
class Match:
    """Partida com estatísticas."""
    id: int
    data: datetime
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_goals: int = 0
    away_goals: int = 0
    status: str = "finished"  # scheduled, live, finished
    
    # Estatísticas da partida
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0


# ==================== SCRAPER ====================

class SofaScoreScraper:
    """Scraper para SofaScore API."""
    
    BASE_URL = "https://www.sofascore.com/api/v1"
    
    # Brasileirão Série A 2025
    TOURNAMENT_ID = 325   # Brasileirão
    SEASON_ID = 72034     # Temporada 2025 (Mirassol, Santos, Ceará, Sport)
    
    # Headers para parecer um browser real
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com"
    }
    
    def __init__(self, cache_dir: str = "data/cache"):
        """Inicializa o scraper."""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.teams: List[Team] = []
        self.players: List[Player] = []
        self.matches: List[Match] = []
        
        # Rate limiting
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.last_request = 0
    
    def _rate_limit(self):
        """Aplica rate limiting com jitter."""
        elapsed = time.time() - self.last_request
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"Rate limit: dormindo {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request = time.time()
    
    def _get(self, endpoint: str, use_cache: bool = True) -> Optional[Dict]:
        """Faz requisição GET com cache e rate limiting."""
        # Verificar cache
        cache_file = self.cache_dir / f"{endpoint.replace('/', '_')}.json"
        
        if use_cache and cache_file.exists():
            # Cache válido por 1 hora
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < 3600:
                logger.debug(f"Usando cache: {endpoint}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Fazer requisição
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.info(f"Requisição: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 429:
                logger.warning("Rate limit atingido! Esperando 60s...")
                time.sleep(60)
                return self._get(endpoint, use_cache=False)
            
            if response.status_code == 403:
                logger.error("Acesso bloqueado (403). Pode precisar de proxy ou headers diferentes.")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Salvar cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição {url}: {e}")
            return None
    
    def get_tournament_teams(self) -> List[Team]:
        """Busca todos os times do torneio."""
        logger.info("Buscando times do Brasileirão Série A 2025...")
        
        endpoint = f"unique-tournament/{self.TOURNAMENT_ID}/season/{self.SEASON_ID}/standings/total"
        data = self._get(endpoint)
        
        if not data or 'standings' not in data:
            logger.error("Não foi possível buscar times")
            return []
        
        teams = []
        for standing in data.get('standings', []):
            for row in standing.get('rows', []):
                team_data = row.get('team', {})
                
                team = Team(
                    id=team_data.get('id'),
                    nome=team_data.get('name'),
                    nome_curto=team_data.get('shortName', ''),
                    temporada=2025
                )
                
                # Estatísticas da tabela
                team.stats.jogos = row.get('matches', 0)
                team.stats.vitorias = row.get('wins', 0)
                team.stats.empates = row.get('draws', 0)
                team.stats.derrotas = row.get('losses', 0)
                team.stats.gols_marcados = row.get('scoresFor', 0)
                team.stats.gols_sofridos = row.get('scoresAgainst', 0)
                
                if team.stats.jogos > 0:
                    team.stats.gols_marcados_media = round(team.stats.gols_marcados / team.stats.jogos, 2)
                    team.stats.gols_sofridos_media = round(team.stats.gols_sofridos / team.stats.jogos, 2)
                
                teams.append(team)
                logger.info(f"  ✅ {team.nome} (ID: {team.id})")
        
        self.teams = teams
        logger.info(f"Total: {len(teams)} times encontrados")
        return teams
    
    def get_team_players(self, team: Team) -> List[Player]:
        """Busca jogadores de um time."""
        logger.info(f"Buscando jogadores do {team.nome}...")
        
        endpoint = f"team/{team.id}/players"
        data = self._get(endpoint)
        
        if not data or 'players' not in data:
            logger.warning(f"Não foi possível buscar jogadores do {team.nome}")
            return []
        
        players = []
        for player_data in data.get('players', []):
            p = player_data.get('player', {})
            
            player = Player(
                id=p.get('id'),
                nome=p.get('name'),
                time=team.nome,
                time_id=team.id,
                posicao=p.get('position', ''),
                nacionalidade=p.get('country', {}).get('name', ''),
                altura=p.get('height', 0),
                pe_preferido=p.get('preferredFoot', ''),
                numero_camisa=p.get('shirtNumber')
            )
            
            # Calcular idade
            if p.get('dateOfBirthTimestamp'):
                birth = datetime.fromtimestamp(p['dateOfBirthTimestamp'])
                player.idade = (datetime.now() - birth).days // 365
            
            players.append(player)
        
        team.jogadores = players
        logger.info(f"  ✅ {len(players)} jogadores encontrados")
        return players
    
    def get_player_stats(self, player: Player, season_id: Optional[int] = None) -> PlayerStats:
        """Busca estatísticas de um jogador."""
        season = season_id or self.SEASON_ID
        
        endpoint = f"player/{player.id}/unique-tournament/{self.TOURNAMENT_ID}/season/{season}/statistics/overall"
        data = self._get(endpoint)
        
        if not data or 'statistics' not in data:
            return player.stats
        
        stats_data = data.get('statistics', {})
        
        player.stats = PlayerStats(
            jogos=stats_data.get('appearances', 0),
            minutos=stats_data.get('minutesPlayed', 0),
            gols=stats_data.get('goals', 0),
            assistencias=stats_data.get('assists', 0),
            chutes=stats_data.get('totalShots', 0),
            chutes_no_gol=stats_data.get('shotsOnTarget', 0),
            passes=stats_data.get('totalPasses', 0),
            passes_certos=stats_data.get('accuratePasses', 0),
            dribles=stats_data.get('dribbleAttempts', 0),
            dribles_certos=stats_data.get('successfulDribbles', 0),
            duelos=stats_data.get('totalDuels', 0),
            duelos_ganhos=stats_data.get('duelsWon', 0),
            faltas_cometidas=stats_data.get('fouls', 0),
            faltas_sofridas=stats_data.get('wasFouled', 0),
            cartoes_amarelos=stats_data.get('yellowCards', 0),
            cartoes_vermelhos=stats_data.get('redCards', 0),
            impedimentos=stats_data.get('offsides', 0),
            cruzamentos=stats_data.get('totalCrosses', 0),
            passes_chave=stats_data.get('keyPasses', 0),
            grandes_chances_criadas=stats_data.get('bigChancesCreated', 0),
            grandes_chances_perdidas=stats_data.get('bigChancesMissed', 0),
            xg=stats_data.get('expectedGoals', 0.0),
            xa=stats_data.get('expectedAssists', 0.0)
        )
        
        player.calcular_medias_por_90()
        return player.stats
    
    def get_team_stats(self, team: Team) -> TeamStats:
        """Busca estatísticas detalhadas do time."""
        endpoint = f"team/{team.id}/unique-tournament/{self.TOURNAMENT_ID}/season/{self.SEASON_ID}/statistics/overall"
        data = self._get(endpoint)
        
        if not data or 'statistics' not in data:
            return team.stats
        
        stats = data.get('statistics', {})
        
        # Atualizar estatísticas do time
        if team.stats.jogos > 0:
            team.stats.chutes_media = round(stats.get('shotsTotal', 0) / team.stats.jogos, 2)
            team.stats.chutes_gol_media = round(stats.get('shotsOnTarget', 0) / team.stats.jogos, 2)
            team.stats.posse_media = round(stats.get('possessionAvg', 50.0), 1)
            team.stats.escanteios_media = round(stats.get('cornersTotal', 0) / team.stats.jogos, 2)
            team.stats.faltas_media = round(stats.get('foulsCommitted', 0) / team.stats.jogos, 2)
            team.stats.cartoes_media = round(
                (stats.get('yellowCards', 0) + stats.get('redCards', 0)) / team.stats.jogos, 2
            )
        
        return team.stats
    
    def get_team_matches(self, team: Team, last_n: int = 10) -> List[Dict]:
        """Busca últimas partidas do time."""
        endpoint = f"team/{team.id}/events/last/0"
        data = self._get(endpoint)
        
        if not data or 'events' not in data:
            return []
        
        matches = []
        for event in data.get('events', [])[:last_n]:
            home_team = event.get('homeTeam', {})
            away_team = event.get('awayTeam', {})
            home_score = event.get('homeScore', {})
            away_score = event.get('awayScore', {})
            
            match = {
                'id': event.get('id'),
                'data': event.get('startTimestamp'),
                'adversario': away_team.get('name') if home_team.get('id') == team.id else home_team.get('name'),
                'casa_fora': 'casa' if home_team.get('id') == team.id else 'fora',
                'gols_pro': home_score.get('current', 0) if home_team.get('id') == team.id else away_score.get('current', 0),
                'gols_contra': away_score.get('current', 0) if home_team.get('id') == team.id else home_score.get('current', 0),
                'torneio': event.get('tournament', {}).get('name', '')
            }
            
            # Resultado
            if match['gols_pro'] > match['gols_contra']:
                match['resultado'] = 'V'
            elif match['gols_pro'] < match['gols_contra']:
                match['resultado'] = 'D'
            else:
                match['resultado'] = 'E'
            
            matches.append(match)
        
        team.partidas = matches
        return matches
    
    def scrape_all(self, include_player_stats: bool = True) -> Dict:
        """Executa scraping completo."""
        logger.info("=" * 60)
        logger.info("🚀 Iniciando scraping do Brasileirão Série A 2025")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # 1. Buscar times
        self.get_tournament_teams()
        
        if not self.teams:
            logger.error("Nenhum time encontrado. Abortando.")
            return {}
        
        # 2. Para cada time, buscar jogadores e estatísticas
        for team in self.teams:
            # Jogadores
            self.get_team_players(team)
            
            # Estatísticas do time
            self.get_team_stats(team)
            
            # Últimas partidas
            self.get_team_matches(team)
            
            # Estatísticas dos jogadores (opcional, demora mais)
            if include_player_stats:
                for player in team.jogadores[:25]:  # Top 25 jogadores
                    self.get_player_stats(player)
                    logger.debug(f"    Stats: {player.nome} - {player.stats.gols}G {player.stats.assistencias}A")
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ Scraping concluído em {elapsed:.1f}s")
        logger.info(f"   Times: {len(self.teams)}")
        logger.info(f"   Jogadores: {sum(len(t.jogadores) for t in self.teams)}")
        logger.info("=" * 60)
        
        return self.export_data()
    
    def export_data(self) -> Dict:
        """Exporta dados para dicionário."""
        return {
            'times': [asdict(t) for t in self.teams],
            'atualizado_em': datetime.now().isoformat(),
            'temporada': 2025,
            'liga': 'Brasileirão Série A'
        }
    
    def save_to_json(self, filepath: str = "data/brasileirao_2025.json"):
        """Salva dados em JSON."""
        data = self.export_data()
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"💾 Dados salvos em: {filepath}")
        return filepath
    
    def convert_to_legacy_format(self) -> tuple:
        """Converte para formato legado (times.json e jogadores.json)."""
        times_legacy = []
        jogadores_legacy = []
        
        for team in self.teams:
            # Formato times.json
            team_legacy = {
                'id': team.id,
                'nome': team.nome,
                'season': team.temporada,
                'jogadores': [p.nome for p in team.jogadores],
                'partidas': team.partidas,
                'metricas': {
                    'gols_media': team.stats.gols_marcados_media,
                    'gols_sofridos_media': team.stats.gols_sofridos_media,
                    'chutes_media': team.stats.chutes_media,
                    'chutes_gol_media': team.stats.chutes_gol_media,
                    'escanteios_media': team.stats.escanteios_media,
                    'faltas_media': team.stats.faltas_media,
                    'cartoes_media': team.stats.cartoes_media
                }
            }
            times_legacy.append(team_legacy)
            
            # Formato jogadores.json
            for player in team.jogadores:
                jogador_legacy = {
                    'id': player.id,
                    'nome': player.nome,
                    'time': player.time,
                    'posicao': player.posicao,
                    'idade': player.idade,
                    'partidas': player.stats.jogos,
                    'minutos': player.stats.minutos,
                    'gols': player.stats.gols,
                    'assistencias': player.stats.assistencias,
                    'chutes': player.stats.chutes,
                    'chutes_no_gol': player.stats.chutes_no_gol,
                    'passes': player.stats.passes,
                    'passes_certos': player.stats.passes_certos,
                    'faltas_cometidas': player.stats.faltas_cometidas,
                    'faltas_sofridas': player.stats.faltas_sofridas,
                    'cartoes_amarelos': player.stats.cartoes_amarelos,
                    'cartoes_vermelhos': player.stats.cartoes_vermelhos,
                    'cruzamentos': player.stats.cruzamentos,
                    'passes_chave': player.stats.passes_chave,
                    'xg': player.stats.xg,
                    'gols_por_90': player.stats.gols_por_90,
                    'chutes_por_90': player.stats.chutes_por_90,
                    'faltas_por_90': player.stats.faltas_por_90,
                    'cartoes_por_90': player.stats.cartoes_por_90
                }
                jogadores_legacy.append(jogador_legacy)
        
        return times_legacy, jogadores_legacy
    
    def save_legacy_format(self, times_path: str = "data/times.json", jogadores_path: str = "data/jogadores.json"):
        """Salva nos arquivos legado."""
        times, jogadores = self.convert_to_legacy_format()
        
        with open(times_path, 'w', encoding='utf-8') as f:
            json.dump(times, f, ensure_ascii=False, indent=2)
        
        with open(jogadores_path, 'w', encoding='utf-8') as f:
            json.dump(jogadores, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 times.json: {len(times)} times")
        logger.info(f"💾 jogadores.json: {len(jogadores)} jogadores")


# ==================== CLI ====================

def main():
    """Executa o scraper via CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SofaScore Scraper - Brasileirão 2025")
    parser.add_argument('--full', action='store_true', help='Scraping completo com estatísticas de jogadores')
    parser.add_argument('--teams-only', action='store_true', help='Apenas times (sem jogadores)')
    parser.add_argument('--output', default='data/brasileirao_2025.json', help='Arquivo de saída')
    parser.add_argument('--legacy', action='store_true', help='Também salvar em formato legado (times.json, jogadores.json)')
    
    args = parser.parse_args()
    
    scraper = SofaScoreScraper()
    
    if args.teams_only:
        scraper.get_tournament_teams()
    else:
        scraper.scrape_all(include_player_stats=args.full)
    
    scraper.save_to_json(args.output)
    
    if args.legacy:
        scraper.save_legacy_format()


if __name__ == "__main__":
    main()
