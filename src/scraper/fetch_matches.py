"""
SofaScore Match Scraper - Coleta de Partidas Históricas
========================================================
Coleta dados de partidas do Brasileirão seguindo a especificação:
- Gols (home_goals, away_goals)
- Escanteios (home_corners, away_corners)
- Estatísticas detalhadas (chutes, faltas, cartões, posse)
- Escalações e minutos jogados
"""

import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MatchScraper:
    """Scraper para buscar partidas do SofaScore e salvar no banco."""
    
    BASE_URL = "https://www.sofascore.com/api/v1"
    
    # Brasileirão Série A 2025
    TOURNAMENT_ID = 325   # Brasileirão
    SEASON_ID = 72034     # Temporada 2025
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com"
    }
    
    def __init__(self, db_config: Dict[str, str]):
        """Inicializa o scraper com configuração do banco."""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        self.db_config = db_config
        self.conn = None
        
        # Rate limiting (1-2 segundos otimizado)
        self.min_delay = 1.0
        self.max_delay = 2.0
        self.last_request = 0
        self.blocked_count = 0  # Contador de bloqueios 403
        
        # Cache de mapeamento sofascore_id -> db_id
        self.team_mapping = {}
        self.player_mapping = {}
        self.existing_event_ids = set()  # Cache de eventos já no banco
    
    def connect_db(self):
        """Conecta ao banco de dados."""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("✅ Conectado ao banco de dados")
    
    def close_db(self):
        """Fecha conexão com banco."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Conexão com banco fechada")
    
    def _rate_limit(self):
        """Aplica rate limiting com jitter."""
        elapsed = time.time() - self.last_request
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)
        
        self.last_request = time.time()
    
    def _get(self, endpoint: str) -> Optional[Dict]:
        """Faz requisição GET com rate limiting."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.debug(f"GET {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 429:
                logger.warning("Rate limit! Esperando 60s...")
                time.sleep(60)
                return self._get(endpoint)
            
            if response.status_code == 403:
                self.blocked_count += 1
                wait_time = min(120, 30 * (2 ** (self.blocked_count - 1)))  # Backoff: 30s, 60s, 120s...
                logger.warning(f"Bloqueado (403) - Tentativa {self.blocked_count}. Aguardando {wait_time}s...")
                time.sleep(wait_time)
                
                # Aumentar delays permanentemente após bloqueio
                self.min_delay = min(3.0, self.min_delay + 0.5)
                self.max_delay = min(5.0, self.max_delay + 0.5)
                logger.info(f"Delays ajustados: {self.min_delay}-{self.max_delay}s")
                
                # Tentar novamente
                if self.blocked_count <= 5:  # Máximo 5 tentativas
                    return self._get(endpoint)
                else:
                    logger.error("Máximo de tentativas 403 atingido")
                    return None
            
            response.raise_for_status()
            
            # Resetar contador de bloqueios em sucesso
            if self.blocked_count > 0:
                logger.info("✅ Recuperado do bloqueio")
                self.blocked_count = 0
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro em {url}: {e}")
            return None
    
    def load_existing_events(self):
        """Carrega eventos já processados para evitar duplicatas."""
        self.connect_db()
        
        with self.conn.cursor() as cur:
            cur.execute("SELECT sofascore_event_id FROM matches WHERE sofascore_event_id IS NOT NULL")
            rows = cur.fetchall()
            self.existing_event_ids = {row[0] for row in rows}
        
        logger.info(f"✅ {len(self.existing_event_ids)} eventos já no banco (serão pulados)")
    
    def load_team_mapping(self):
        """Carrega mapeamento sofascore_id -> team_id do banco."""
        self.connect_db()
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, sofascore_id FROM teams WHERE sofascore_id IS NOT NULL")
            rows = cur.fetchall()
            
            for row in rows:
                self.team_mapping[row['sofascore_id']] = row['id']
        
        logger.info(f"✅ {len(self.team_mapping)} times mapeados")
    
    def load_player_mapping(self):
        """Carrega mapeamento sofascore_id -> player_id do banco."""
        self.connect_db()
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, sofascore_id FROM players WHERE sofascore_id IS NOT NULL")
            rows = cur.fetchall()
            
            for row in rows:
                self.player_mapping[row['sofascore_id']] = row['id']
        
        logger.info(f"✅ {len(self.player_mapping)} jogadores mapeados")
    
    def get_season_events(self) -> List[int]:
        """Busca todos os IDs de eventos (partidas) da temporada do Brasileirão."""
        logger.info("Buscando partidas do Brasileirão 2025...")
        
        endpoint = f"unique-tournament/{self.TOURNAMENT_ID}/season/{self.SEASON_ID}/events/last/0"
        data = self._get(endpoint)
        
        if not data or 'events' not in data:
            logger.error("Não foi possível buscar eventos do Brasileirão")
            return []
        
        event_ids = []
        for event in data['events']:
            event_id = event.get('id')
            status = event.get('status', {}).get('code')
            
            # Apenas partidas finalizadas
            if status == 100:  # finished
                event_ids.append(event_id)
        
        logger.info(f"✅ {len(event_ids)} partidas do Brasileirão encontradas")
        return event_ids
    
    def get_team_all_matches(self, team_id: int, season_year: int = 2025) -> List[int]:
        """Busca TODOS os jogos de um time em 2025 (todas as competições)."""
        logger.info(f"Buscando todos os jogos do time {team_id} em {season_year}...")
        
        all_events = []
        event_ids = []
        
        # Paginar através de todas as partidas (30 por página)
        for page in range(20):  # máximo 20 páginas (600 partidas)
            endpoint = f"team/{team_id}/events/last/{page}"
            data = self._get(endpoint)
            
            if not data or 'events' not in data or len(data['events']) == 0:
                break
            
            events = data['events']
            all_events.extend(events)
            
            # Se todos os eventos já são de anos anteriores, parar
            from datetime import datetime
            oldest_year = min(datetime.fromtimestamp(e.get('startTimestamp', 0)).year 
                            for e in events)
            if oldest_year < season_year:
                # Já passou do ano desejado, pode parar
                break
        
        logger.debug(f"  Total de eventos brutos: {len(all_events)}")
        
        # Filtrar apenas finalizados do ano desejado
        from datetime import datetime
        for event in all_events:
            event_id = event.get('id')
            status = event.get('status', {}).get('code')
            timestamp = event.get('startTimestamp', 0)
            event_year = datetime.fromtimestamp(timestamp).year
            
            # Apenas partidas finalizadas do ano especificado
            if status == 100 and event_year == season_year:
                event_ids.append(event_id)
        
        logger.info(f"  ✅ {len(event_ids)} partidas finalizadas em {season_year}")
        return event_ids
    
    def get_match_details(self, event_id: int) -> Optional[Dict]:
        """Busca detalhes completos de uma partida."""
        endpoint = f"event/{event_id}"
        data = self._get(endpoint)
        
        if not data or 'event' not in data:
            return None
        
        return data['event']
    
    def get_match_statistics(self, event_id: int) -> Optional[Dict]:
        """Busca estatísticas detalhadas da partida."""
        endpoint = f"event/{event_id}/statistics"
        data = self._get(endpoint)
        
        if not data or 'statistics' not in data:
            return None
        
        # Retorna estatísticas organizadas por time
        stats_by_period = data['statistics']
        
        # Vamos pegar o ALL (jogo completo)
        all_stats = None
        for period in stats_by_period:
            if period.get('period') == 'ALL':
                all_stats = period.get('groups', [])
                break
        
        return all_stats
    
    def get_match_lineups(self, event_id: int) -> Optional[Dict]:
        """Busca escalações da partida."""
        endpoint = f"event/{event_id}/lineups"
        data = self._get(endpoint)
        
        if not data:
            return None
        
        return data
    
    def parse_statistics(self, stats_groups: List[Dict]) -> Dict:
        """Extrai estatísticas relevantes dos grupos."""
        result = {
            'home_shots': 0,
            'away_shots': 0,
            'home_shots_on_target': 0,
            'away_shots_on_target': 0,
            'home_corners': 0,
            'away_corners': 0,
            'home_fouls': 0,
            'away_fouls': 0,
            'home_yellow_cards': 0,
            'away_yellow_cards': 0,
            'home_red_cards': 0,
            'away_red_cards': 0
        }
        
        for group in stats_groups:
            for stat in group.get('statisticsItems', []):
                name = stat.get('name', '')
                home = stat.get('home')
                away = stat.get('away')
                
                # Mapear nomes do SofaScore para nossos campos
                if name == 'Total shots':
                    result['home_shots'] = int(home) if home else 0
                    result['away_shots'] = int(away) if away else 0
                
                elif name == 'Shots on target':
                    result['home_shots_on_target'] = int(home) if home else 0
                    result['away_shots_on_target'] = int(away) if away else 0
                
                elif name == 'Corner kicks':
                    result['home_corners'] = int(home) if home else 0
                    result['away_corners'] = int(away) if away else 0
                
                elif name == 'Fouls':
                    result['home_fouls'] = int(home) if home else 0
                    result['away_fouls'] = int(away) if away else 0
                
                elif name == 'Yellow cards':
                    result['home_yellow_cards'] = int(home) if home else 0
                    result['away_yellow_cards'] = int(away) if away else 0
                
                elif name == 'Red cards':
                    result['home_red_cards'] = int(home) if home else 0
                    result['away_red_cards'] = int(away) if away else 0
        
        return result
    
    def save_match(self, match_data: Dict, stats: Dict) -> Optional[int]:
        """Salva partida no banco de dados."""
        self.connect_db()
        
        # Mapear IDs do SofaScore para IDs do banco
        home_sofascore_id = match_data['homeTeam']['id']
        away_sofascore_id = match_data['awayTeam']['id']
        
        home_team_id = self.team_mapping.get(home_sofascore_id)
        away_team_id = self.team_mapping.get(away_sofascore_id)
        
        if not home_team_id or not away_team_id:
            logger.warning(f"Times não mapeados: {home_sofascore_id}, {away_sofascore_id}")
            return None
        
        # Extrair dados
        home_score = match_data.get('homeScore', {})
        away_score = match_data.get('awayScore', {})
        
        match_insert = {
            'sofascore_event_id': match_data['id'],
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'data': datetime.fromtimestamp(match_data['startTimestamp']),
            'rodada': match_data.get('roundInfo', {}).get('round', 0) if match_data.get('roundInfo') else None,
            'home_goals': home_score.get('current', 0),
            'away_goals': away_score.get('current', 0),
            'status': 'finished',
            'liga': match_data.get('tournament', {}).get('name', 'Brasileirão'),
            **stats
        }
        
        try:
            with self.conn.cursor() as cur:
                # Verificar se já existe
                cur.execute(
                    "SELECT id FROM matches WHERE sofascore_event_id = %s",
                    (match_insert['sofascore_event_id'],)
                )
                existing = cur.fetchone()
                
                if existing:
                    logger.debug(f"Partida {match_insert['sofascore_event_id']} já existe")
                    return existing[0]
                
                # Inserir
                columns = ', '.join(match_insert.keys())
                placeholders = ', '.join(['%s'] * len(match_insert))
                
                cur.execute(
                    f"INSERT INTO matches ({columns}) VALUES ({placeholders}) RETURNING id",
                    list(match_insert.values())
                )
                
                match_id = cur.fetchone()[0]
                self.conn.commit()
                
                logger.info(f"✅ Partida salva: ID {match_id} - {match_data['homeTeam']['name']} {match_insert['home_goals']} x {match_insert['away_goals']} {match_data['awayTeam']['name']}")
                return match_id
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao salvar partida: {e}")
            return None
    
    def save_lineup(self, match_id: int, match_data: Dict, lineup_data: Dict):
        """Salva escalação da partida."""
        self.connect_db()
        
        if not lineup_data or not lineup_data.get('confirmed'):
            return
        
        # Mapear times usando os dados da partida
        home_sofascore_id = match_data['homeTeam']['id']
        away_sofascore_id = match_data['awayTeam']['id']
        
        home_team_id = self.team_mapping.get(home_sofascore_id)
        away_team_id = self.team_mapping.get(away_sofascore_id)
        
        if not home_team_id or not away_team_id:
            return
        
        # Processar home e away
        teams = [
            ('home', home_team_id),
            ('away', away_team_id)
        ]
        
        for side, team_id in teams:
            team_data = lineup_data.get(side)
            if not team_data or 'players' not in team_data:
                continue
            
            # Jogadores que começaram
            for player_data in team_data.get('players', []):
                player = player_data.get('player', {})
                stats = player_data.get('statistics', {})
                
                player_sofascore_id = player.get('id')
                player_id = self.player_mapping.get(player_sofascore_id)
                
                if not player_id:
                    logger.debug(f"Jogador não mapeado: {player.get('name')} (ID: {player_sofascore_id})")
                    continue
                
                # Inserir na tabela lineups
                try:
                    with self.conn.cursor() as cur:
                        # Verificar se já existe
                        cur.execute("""
                            SELECT id FROM lineups WHERE match_id = %s AND player_id = %s
                        """, (match_id, player_id))
                        
                        if cur.fetchone():
                            # Atualizar
                            cur.execute("""
                                UPDATE lineups 
                                SET minutes_played = %s, is_starter = %s
                                WHERE match_id = %s AND player_id = %s
                            """, (stats.get('minutesPlayed', 0), True, match_id, player_id))
                        else:
                            # Inserir
                            cur.execute("""
                                INSERT INTO lineups (match_id, team_id, player_id, is_starter, minutes_played)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (
                                match_id,
                                team_id,
                                player_id,
                                True,
                                stats.get('minutesPlayed', 0)
                            ))
                    
                    self.conn.commit()
                    
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Erro ao salvar lineup: {e}")
            
            # Substitutos que entraram
            for sub_data in team_data.get('substitutes', []):
                player = sub_data.get('player', {})
                stats = sub_data.get('statistics', {})
                
                # Se jogou, adicionar
                minutes = stats.get('minutesPlayed', 0)
                if minutes > 0:
                    player_sofascore_id = player.get('id')
                    player_id = self.player_mapping.get(player_sofascore_id)
                    
                    if not player_id:
                        continue
                    
                    try:
                        with self.conn.cursor() as cur:
                            # Verificar se já existe
                            cur.execute("""
                                SELECT id FROM lineups WHERE match_id = %s AND player_id = %s
                            """, (match_id, player_id))
                            
                            if cur.fetchone():
                                # Atualizar
                                cur.execute("""
                                    UPDATE lineups 
                                    SET minutes_played = %s, is_starter = %s
                                    WHERE match_id = %s AND player_id = %s
                                """, (minutes, False, match_id, player_id))
                            else:
                                # Inserir
                                cur.execute("""
                                    INSERT INTO lineups (match_id, team_id, player_id, is_starter, minutes_played)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (
                                    match_id,
                                    team_id,
                                    player_id,
                                    False,
                                    minutes
                                ))
                        
                        self.conn.commit()
                        
                    except Exception as e:
                        self.conn.rollback()
                        logger.error(f"Erro ao salvar substituto: {e}")
    
    def scrape_all_matches(self, mode: str = 'all_teams'):
        """
        Executa scraping de partidas.
        
        Args:
            mode: 'brasileirao' (apenas Brasileirão) ou 'all_teams' (todos jogos de 2025 de cada time)
        """
        logger.info("=" * 70)
        if mode == 'all_teams':
            logger.info("🚀 Coletando TODOS os jogos de 2025 de cada time")
        else:
            logger.info("🚀 Coletando partidas do Brasileirão 2025")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # 1. Carregar mapeamentos
        self.load_team_mapping()
        self.load_player_mapping()
        self.load_existing_events()  # Carregar eventos já processados
        
        # 2. Buscar eventos
        if mode == 'all_teams':
            # Buscar todos os jogos de cada time
            event_ids = set()  # usar set para evitar duplicatas
            total_teams = len(self.team_mapping)
            
            print(f"\n{'='*60}")
            print(f"🚀 INICIANDO COLETA DE EVENTOS")
            print(f"{'='*60}")
            print(f"✅ {total_teams} times carregados")
            print(f"⏱️  Rate limit: {self.min_delay}-{self.max_delay}s por requisição\n")
            
            for idx, (sofascore_id, team_id) in enumerate(sorted(self.team_mapping.items(), key=lambda x: x[1]), 1):
                # Buscar nome do time
                with self.conn.cursor() as cur:
                    cur.execute('SELECT nome FROM teams WHERE id = %s', (team_id,))
                    team_name = cur.fetchone()[0]
                
                print(f"[{idx}/{total_teams}] 🔄 {team_name:20s} (SofaScore ID {sofascore_id})...")
                
                before_count = len(event_ids)
                team_events = self.get_team_all_matches(sofascore_id, season_year=2025)
                event_ids.update(team_events)
                new_events = len(event_ids) - before_count
                
                print(f"          ✓ {len(team_events)} partidas | {new_events} novas | Total: {len(event_ids)}")
            
            event_ids = list(event_ids)
            print(f"\n{'='*60}")
            print(f"📊 RESUMO DA COLETA DE EVENTOS")
            print(f"{'='*60}")
            print(f"Total de eventos únicos: {len(event_ids)}")
            print(f"{'='*60}\n")
        else:
            # Apenas Brasileirão
            event_ids = self.get_season_events()
        
        if not event_ids:
            logger.error("Nenhuma partida encontrada")
            return
        
        # 3. Para cada evento, buscar detalhes e salvar
        saved_count = 0
        skipped_count = 0
        
        print(f"\n{'='*60}")
        print(f"💾 INICIANDO SALVAMENTO NO BANCO DE DADOS")
        print(f"{'='*60}")
        print(f"Total de partidas para processar: {len(event_ids)}\n")
        
        for i, event_id in enumerate(event_ids, 1):
            progress_pct = (i / len(event_ids)) * 100
            
            # Pular se já existe no banco
            if event_id in self.existing_event_ids:
                if i % 50 == 0:  # Log a cada 50
                    print(f"[{i}/{len(event_ids)}] ({progress_pct:.1f}%) ⏩ Pulando eventos já existentes...")
                skipped_count += 1
                continue
            
            print(f"[{i}/{len(event_ids)}] ({progress_pct:.1f}%) Processando evento {event_id}...", end=' ')
            
            # Detalhes da partida
            match_data = self.get_match_details(event_id)
            if not match_data:
                print("❌ Sem detalhes")
                skipped_count += 1
                continue
            
            # Estatísticas
            stats_data = self.get_match_statistics(event_id)
            if stats_data:
                stats = self.parse_statistics(stats_data)
            else:
                stats = {}
            
            # Salvar partida
            match_id = self.save_match(match_data, stats)
            if match_id:
                saved_count += 1
                self.existing_event_ids.add(event_id)  # Adicionar ao cache
                print(f"✅ Salvo (ID {match_id})")
                
                # Escalações
                lineup_data = self.get_match_lineups(event_id)
                if lineup_data:
                    self.save_lineup(match_id, match_data, lineup_data)
            else:
                print("⚠️  Já existe")
                skipped_count += 1
                self.existing_event_ids.add(event_id)  # Adicionar ao cache
            
            # Atualizar progresso a cada 10 partidas
            if i % 10 == 0:
                print(f"\n📊 Progresso: {saved_count} salvas | {skipped_count} puladas\n")
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ SCRAPING FINALIZADO em {elapsed/60:.1f} minutos")
        print(f"{'='*60}")
        print(f"Partidas processadas: {len(event_ids)}")
        print(f"Novas partidas salvas: {saved_count}")
        print(f"Partidas já existentes: {skipped_count}")
        print(f"{'='*60}\n")
        
        self.close_db()


def main():
    """CLI para executar o scraper."""
    import os
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="SofaScore Match Scraper")
    parser.add_argument('--mode', choices=['brasileirao', 'all_teams'], default='all_teams',
                        help='brasileirao: apenas Brasileirão | all_teams: todos jogos de 2025')
    args = parser.parse_args()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'estatisticas'),
        'user': os.getenv('DB_USER', 'estatisticas_user'),
        'password': os.getenv('DB_PASSWORD', 'estatisticas_password')
    }
    
    scraper = MatchScraper(db_config)
    scraper.scrape_all_matches(mode=args.mode)


if __name__ == "__main__":
    main()
