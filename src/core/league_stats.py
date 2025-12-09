"""
ETAPA 2 - Médias de Referência da Liga

Calcula as âncoras estatísticas:
- Média de gols (mandante/visitante)
- Média de cartões (mandante/visitante)
- Média de escanteios (mandante/visitante)

Essas médias servem como referência para times com poucos jogos.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class LeagueAverages:
    """Médias de referência da liga."""
    # Gols
    gols_mandante: float
    gols_visitante: float
    gols_total: float
    
    # Cartões
    cartoes_mandante: float
    cartoes_visitante: float
    cartoes_total: float
    
    # Escanteios
    escanteios_mandante: float
    escanteios_visitante: float
    escanteios_total: float
    
    # Metadados
    total_jogos: int
    temporada: str


class LeagueStats:
    """
    Calcula e gerencia as estatísticas médias da liga.
    
    Princípio: Lei dos Grandes Números
    - Quanto mais jogos, mais confiáveis as médias
    - Times com poucos jogos não fogem muito dessas médias
    """
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self._cache: dict = {}
    
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def calculate_averages(self, league_id: int, temporada: str = "2025") -> LeagueAverages:
        """
        Calcula as médias da liga baseado em todas as partidas.
        
        Args:
            league_id: ID da liga no banco
            temporada: Temporada a analisar
            
        Returns:
            LeagueAverages com todas as médias calculadas
        """
        cache_key = f"{league_id}_{temporada}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar todas as partidas da liga/temporada
        cursor.execute("""
            SELECT 
                m.home_goals as gols_mandante,
                m.away_goals as gols_visitante,
                (m.home_yellow_cards + m.home_red_cards) as cartoes_mandante,
                (m.away_yellow_cards + m.away_red_cards) as cartoes_visitante,
                m.home_corners as escanteios_mandante,
                m.away_corners as escanteios_visitante
            FROM matches m
            JOIN teams t ON m.home_team_id = t.id
            WHERE t.league_id = %s
            AND m.status = 'finished'
        """, (league_id,))
        
        partidas = cursor.fetchall()
        conn.close()
        
        if not partidas:
            # Retorna médias históricas típicas do Brasileirão
            return self._get_default_averages(temporada)
        
        # Calcular médias
        n = len(partidas)
        
        gols_m = [p['gols_mandante'] or 0 for p in partidas]
        gols_v = [p['gols_visitante'] or 0 for p in partidas]
        cart_m = [p['cartoes_mandante'] or 0 for p in partidas]
        cart_v = [p['cartoes_visitante'] or 0 for p in partidas]
        esc_m = [p['escanteios_mandante'] or 0 for p in partidas]
        esc_v = [p['escanteios_visitante'] or 0 for p in partidas]
        
        averages = LeagueAverages(
            gols_mandante=np.mean(gols_m),
            gols_visitante=np.mean(gols_v),
            gols_total=np.mean(gols_m) + np.mean(gols_v),
            cartoes_mandante=np.mean(cart_m),
            cartoes_visitante=np.mean(cart_v),
            cartoes_total=np.mean(cart_m) + np.mean(cart_v),
            escanteios_mandante=np.mean(esc_m),
            escanteios_visitante=np.mean(esc_v),
            escanteios_total=np.mean(esc_m) + np.mean(esc_v),
            total_jogos=n,
            temporada=temporada
        )
        
        self._cache[cache_key] = averages
        return averages
    
    def _get_default_averages(self, temporada: str) -> LeagueAverages:
        """
        Médias históricas típicas do Brasileirão quando não há dados.
        Baseado em análises de temporadas anteriores.
        """
        return LeagueAverages(
            gols_mandante=1.45,      # Mandante marca mais
            gols_visitante=1.05,     # Visitante marca menos
            gols_total=2.50,
            cartoes_mandante=2.1,
            cartoes_visitante=2.4,   # Visitante leva mais cartões
            cartoes_total=4.5,
            escanteios_mandante=5.2,
            escanteios_visitante=4.3,
            escanteios_total=9.5,
            total_jogos=0,
            temporada=temporada
        )
    
    def get_variance_stats(self, league_id: int, temporada: str = "2025") -> dict:
        """
        Calcula variância para determinar se Poisson é adequado.
        
        Se variância >> média: usar Binomial Negativa
        Se variância ≈ média: Poisson é adequado
        """
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                m.home_goals as gols_mandante,
                m.away_goals as gols_visitante,
                (m.home_yellow_cards + m.home_red_cards) as cartoes_mandante,
                (m.away_yellow_cards + m.away_red_cards) as cartoes_visitante,
                m.home_corners as escanteios_mandante,
                m.away_corners as escanteios_visitante
            FROM matches m
            JOIN teams t ON m.home_team_id = t.id
            WHERE t.league_id = %s
            AND m.status = 'finished'
        """, (league_id,))
        
        partidas = cursor.fetchall()
        conn.close()
        
        if not partidas:
            return self._get_default_variance()
        
        gols_m = [p['gols_mandante'] or 0 for p in partidas]
        gols_v = [p['gols_visitante'] or 0 for p in partidas]
        
        return {
            'gols': {
                'mandante': {'media': np.mean(gols_m), 'variancia': np.var(gols_m)},
                'visitante': {'media': np.mean(gols_v), 'variancia': np.var(gols_v)},
                'usar_negbinomial': np.var(gols_m) > np.mean(gols_m) * 1.5
            },
            'recomendacao': 'poisson' if np.var(gols_m) <= np.mean(gols_m) * 1.5 else 'negbinomial'
        }
    
    def _get_default_variance(self) -> dict:
        return {
            'gols': {
                'mandante': {'media': 1.45, 'variancia': 1.5},
                'visitante': {'media': 1.05, 'variancia': 1.2},
                'usar_negbinomial': False
            },
            'recomendacao': 'poisson'
        }
