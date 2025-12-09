"""
ETAPA 3 - Modelo de Times

Calcula força ofensiva e defensiva de cada time:
- Força de ataque = gols marcados / média da liga
- Força de defesa = gols sofridos / média da liga

Separa por mando de campo (casa/fora).
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import numpy as np
from .league_stats import LeagueStats, LeagueAverages


@dataclass
class TeamStrength:
    """Força de um time em todas as dimensões."""
    team_id: int
    team_name: str
    
    # Força de ataque (> 1 = acima da média, < 1 = abaixo)
    ataque_casa: float = 1.0
    ataque_fora: float = 1.0
    ataque_geral: float = 1.0
    
    # Força de defesa (< 1 = boa defesa, > 1 = defesa ruim)
    defesa_casa: float = 1.0
    defesa_fora: float = 1.0
    defesa_geral: float = 1.0
    
    # Cartões (tendência)
    cartoes_favor: float = 1.0   # Cartões que o time recebe
    cartoes_contra: float = 1.0  # Cartões que provoca no adversário
    
    # Escanteios
    escanteios_favor: float = 1.0
    escanteios_contra: float = 1.0
    
    # Metadados
    jogos_casa: int = 0
    jogos_fora: int = 0
    confianca: float = 0.5  # 0-1, baseado no número de jogos


class TeamModel:
    """
    Modelo para calcular força relativa dos times.
    
    Princípio: Comparar com a média da liga
    - Time que faz 2.0 gols/jogo numa liga de média 1.5 tem ataque = 1.33
    - Time que sofre 1.0 gol/jogo numa liga de média 1.5 tem defesa = 0.67 (boa)
    """
    
    MIN_JOGOS_CONFIAVEL = 10  # Mínimo de jogos para confiar 100%
    
    def __init__(self, db_config: dict, league_stats: LeagueStats):
        self.db_config = db_config
        self.league_stats = league_stats
        self._cache: Dict[int, TeamStrength] = {}
    
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def calculate_team_strength(
        self, 
        team_id: int, 
        league_id: int,
        temporada: str = "2025"
    ) -> TeamStrength:
        """
        Calcula a força completa de um time.
        
        Usa regressão à média para times com poucos jogos:
        força_final = peso * força_calculada + (1 - peso) * 1.0
        
        onde peso = min(jogos / MIN_JOGOS_CONFIAVEL, 1.0)
        """
        cache_key = f"{team_id}_{league_id}_{temporada}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Pegar médias da liga como referência
        league_avg = self.league_stats.calculate_averages(league_id, temporada)
        
        # Buscar estatísticas do time
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar nome do time
        cursor.execute("SELECT nome FROM teams WHERE id = %s", (team_id,))
        team_result = cursor.fetchone()
        team_name = team_result['nome'] if team_result else f"Time {team_id}"
        
        # Jogos como mandante
        cursor.execute("""
            SELECT 
                AVG(home_goals) as gols_marcados,
                AVG(away_goals) as gols_sofridos,
                AVG(home_yellow_cards + home_red_cards) as cartoes,
                AVG(home_corners) as escanteios,
                COUNT(*) as jogos
            FROM matches
            WHERE home_team_id = %s AND status = 'finished'
        """, (team_id,))
        casa = cursor.fetchone()
        
        # Jogos como visitante
        cursor.execute("""
            SELECT 
                AVG(away_goals) as gols_marcados,
                AVG(home_goals) as gols_sofridos,
                AVG(away_yellow_cards + away_red_cards) as cartoes,
                AVG(away_corners) as escanteios,
                COUNT(*) as jogos
            FROM matches
            WHERE away_team_id = %s AND status = 'finished'
        """, (team_id,))
        fora = cursor.fetchone()
        
        conn.close()
        
        # Calcular forças relativas
        jogos_casa = casa['jogos'] if casa and casa['jogos'] else 0
        jogos_fora = fora['jogos'] if fora and fora['jogos'] else 0
        total_jogos = jogos_casa + jogos_fora
        
        # Peso de confiança (regressão à média)
        confianca = min(total_jogos / self.MIN_JOGOS_CONFIAVEL, 1.0)
        
        # Força de ataque
        ataque_casa_raw = self._safe_div(
            casa['gols_marcados'] if casa else None, 
            league_avg.gols_mandante
        )
        ataque_fora_raw = self._safe_div(
            fora['gols_marcados'] if fora else None,
            league_avg.gols_visitante
        )
        
        # Força de defesa (invertida: menos gols = melhor)
        defesa_casa_raw = self._safe_div(
            casa['gols_sofridos'] if casa else None,
            league_avg.gols_visitante
        )
        defesa_fora_raw = self._safe_div(
            fora['gols_sofridos'] if fora else None,
            league_avg.gols_mandante
        )
        
        # Aplicar regressão à média
        # Tratando valores None
        cartoes_casa = float(casa['cartoes'] or 0) if casa and casa['cartoes'] else 0
        cartoes_fora = float(fora['cartoes'] or 0) if fora and fora['cartoes'] else 0
        escanteios_casa = float(casa['escanteios'] or 0) if casa and casa['escanteios'] else 0
        escanteios_fora = float(fora['escanteios'] or 0) if fora and fora['escanteios'] else 0
        
        strength = TeamStrength(
            team_id=team_id,
            team_name=team_name,
            ataque_casa=self._regress_to_mean(ataque_casa_raw, confianca),
            ataque_fora=self._regress_to_mean(ataque_fora_raw, confianca),
            ataque_geral=self._regress_to_mean(
                (ataque_casa_raw + ataque_fora_raw) / 2, confianca
            ),
            defesa_casa=self._regress_to_mean(defesa_casa_raw, confianca),
            defesa_fora=self._regress_to_mean(defesa_fora_raw, confianca),
            defesa_geral=self._regress_to_mean(
                (defesa_casa_raw + defesa_fora_raw) / 2, confianca
            ),
            cartoes_favor=self._regress_to_mean(
                self._safe_div(
                    (cartoes_casa + cartoes_fora) / 2,
                    league_avg.cartoes_total / 2
                ),
                confianca
            ),
            escanteios_favor=self._regress_to_mean(
                self._safe_div(
                    (escanteios_casa + escanteios_fora) / 2,
                    league_avg.escanteios_total / 2
                ),
                confianca
            ),
            jogos_casa=jogos_casa,
            jogos_fora=jogos_fora,
            confianca=confianca
        )
        
        self._cache[cache_key] = strength
        return strength
    
    def _safe_div(self, value: Optional[float], divisor: float) -> float:
        """Divisão segura que retorna 1.0 se não houver dados."""
        if value is None or divisor == 0:
            return 1.0
        return float(value) / float(divisor)
    
    def _regress_to_mean(self, value: float, weight: float) -> float:
        """
        Aplica regressão à média.
        
        Com poucos jogos (weight baixo), puxa para 1.0 (média da liga).
        Com muitos jogos (weight = 1.0), usa o valor calculado.
        """
        return weight * value + (1 - weight) * 1.0
    
    def get_all_teams_strength(self, league_id: int, temporada: str = "2025") -> List[TeamStrength]:
        """Retorna força de todos os times da liga."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id FROM teams WHERE league_id = %s
        """, (league_id,))
        
        teams = cursor.fetchall()
        conn.close()
        
        return [
            self.calculate_team_strength(t['id'], league_id, temporada)
            for t in teams
        ]
    
    def compare_teams(
        self, 
        team1_id: int, 
        team2_id: int, 
        league_id: int,
        team1_home: bool = True
    ) -> dict:
        """
        Compara dois times e retorna análise.
        
        Returns:
            dict com comparação detalhada
        """
        t1 = self.calculate_team_strength(team1_id, league_id)
        t2 = self.calculate_team_strength(team2_id, league_id)
        
        # Ataque vs Defesa
        if team1_home:
            t1_attack = t1.ataque_casa
            t1_defense = t1.defesa_casa
            t2_attack = t2.ataque_fora
            t2_defense = t2.defesa_fora
        else:
            t1_attack = t1.ataque_fora
            t1_defense = t1.defesa_fora
            t2_attack = t2.ataque_casa
            t2_defense = t2.defesa_casa
        
        return {
            'team1': {
                'id': team1_id,
                'nome': t1.team_name,
                'ataque': t1_attack,
                'defesa': t1_defense,
                'confianca': t1.confianca
            },
            'team2': {
                'id': team2_id,
                'nome': t2.team_name,
                'ataque': t2_attack,
                'defesa': t2_defense,
                'confianca': t2.confianca
            },
            'vantagem_ataque': t1_attack / t2_attack if t2_attack else 1.0,
            'vantagem_defesa': t2_defense / t1_defense if t1_defense else 1.0
        }
