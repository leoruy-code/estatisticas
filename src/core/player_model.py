"""
ETAPA 7 - Modelo de Jogadores

Cria ratings individuais por jogador:
- Ataque: gols, xG, finalizações, passes decisivos
- Defesa: desarmes, interceptações, duelos ganhos
- Disciplina: faltas, cartões
- Influência em escanteios

Usado para ajustar as previsões baseado na escalação.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from typing import Optional, List, Dict
import numpy as np
import json


@dataclass
class PlayerRating:
    """Rating individual de um jogador."""
    player_id: int
    nome: str
    posicao: str
    
    # Ratings normalizados (0-100)
    rating_geral: float = 50.0
    rating_ataque: float = 50.0
    rating_defesa: float = 50.0
    rating_disciplina: float = 50.0  # Menor = mais cartões
    rating_escanteios: float = 50.0  # Influência em escanteios
    
    # Estatísticas por 90 min
    gols_p90: float = 0.0
    assistencias_p90: float = 0.0
    finalizacoes_p90: float = 0.0
    passes_decisivos_p90: float = 0.0
    desarmes_p90: float = 0.0
    interceptacoes_p90: float = 0.0
    duelos_ganhos_p90: float = 0.0
    faltas_p90: float = 0.0
    cartoes_p90: float = 0.0
    
    # Metadados
    minutos_jogados: int = 0
    jogos: int = 0
    titular: bool = False


class PlayerModel:
    """
    Modelo para calcular ratings de jogadores.
    
    Os ratings são usados para ajustar λ, μ, κ baseado na escalação.
    """
    
    # Pesos por posição para cada tipo de rating
    PESOS_POSICAO = {
        'Goleiro': {'ataque': 0.0, 'defesa': 1.0, 'disciplina': 0.8},
        'Zagueiro': {'ataque': 0.2, 'defesa': 1.0, 'disciplina': 0.9},
        'Lateral': {'ataque': 0.5, 'defesa': 0.7, 'disciplina': 0.8},
        'Volante': {'ataque': 0.3, 'defesa': 0.8, 'disciplina': 1.0},
        'Meia': {'ataque': 0.7, 'defesa': 0.4, 'disciplina': 0.7},
        'Atacante': {'ataque': 1.0, 'defesa': 0.1, 'disciplina': 0.6},
    }
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self._cache: Dict[int, PlayerRating] = {}
    
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def calculate_player_rating(self, player_id: int) -> PlayerRating:
        """
        Calcula o rating completo de um jogador.
        
        Usa as estatísticas raw_stats armazenadas em JSONB.
        """
        if player_id in self._cache:
            return self._cache[player_id]
        
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar jogador e estatísticas
        cursor.execute("""
            SELECT 
                p.id, p.nome, p.posicao,
                ps.raw_stats
            FROM players p
            LEFT JOIN player_stats ps ON ps.player_id = p.id
            WHERE p.id = %s
        """, (player_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return self._default_rating(player_id)
        
        stats = result['raw_stats'] or {}
        posicao = self._normalize_position(result['posicao'])
        
        # Extrair estatísticas relevantes
        minutos = stats.get('minutos_jogados', 0) or stats.get('minutes_played', 0) or 0
        jogos = stats.get('jogos', 0) or stats.get('appearances', 0) or 0
        
        # Calcular por 90 minutos
        p90_factor = 90 / max(minutos / max(jogos, 1), 1) if minutos > 0 else 0
        
        gols = (stats.get('gols', 0) or stats.get('goals', 0) or 0)
        assistencias = (stats.get('assistencias', 0) or stats.get('assists', 0) or 0)
        finalizacoes = (stats.get('finalizacoes', 0) or stats.get('shots', 0) or 0)
        escanteios_batidos = (stats.get('escanteios_batidos', 0) or stats.get('corners', 0) or stats.get('crosses', 0) or 0)
        desarmes = (stats.get('desarmes', 0) or stats.get('tackles', 0) or 0)
        interceptacoes = (stats.get('interceptacoes', 0) or stats.get('interceptions', 0) or 0)
        faltas = (stats.get('faltas_cometidas', 0) or stats.get('fouls', 0) or 0)
        cartoes_amarelos = (stats.get('cartoes_amarelos', 0) or stats.get('yellow_cards', 0) or 0)
        cartoes_vermelhos = (stats.get('cartoes_vermelhos', 0) or stats.get('red_cards', 0) or 0)
        
        # Ratings
        rating_geral = stats.get('nota_media', 6.0) or stats.get('rating', 6.0) or 6.0
        
        # Calcular ratings específicos
        rating_ataque = self._calculate_attack_rating(
            gols, assistencias, finalizacoes, jogos, posicao
        )
        rating_defesa = self._calculate_defense_rating(
            desarmes, interceptacoes, jogos, posicao
        )
        rating_disciplina = self._calculate_discipline_rating(
            faltas, cartoes_amarelos, cartoes_vermelhos, jogos
        )
        rating_escanteios = self._calculate_corners_rating(
            escanteios_batidos, finalizacoes, jogos, posicao
        )
        
        rating = PlayerRating(
            player_id=player_id,
            nome=result['nome'],
            posicao=posicao,
            rating_geral=min(rating_geral * 10, 100),  # Converter 0-10 para 0-100
            rating_ataque=rating_ataque,
            rating_defesa=rating_defesa,
            rating_disciplina=rating_disciplina,
            rating_escanteios=rating_escanteios,
            gols_p90=gols * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            assistencias_p90=assistencias * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            finalizacoes_p90=finalizacoes * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            desarmes_p90=desarmes * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            interceptacoes_p90=interceptacoes * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            faltas_p90=faltas * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            cartoes_p90=(cartoes_amarelos + cartoes_vermelhos * 2) * p90_factor / max(jogos, 1) if jogos > 0 else 0,
            minutos_jogados=minutos,
            jogos=jogos
        )
        
        self._cache[player_id] = rating
        return rating
    
    def _normalize_position(self, posicao: str) -> str:
        """Normaliza posição para categorias padrão."""
        if not posicao:
            return 'Meia'
        
        posicao = posicao.lower()
        
        if 'goleiro' in posicao or 'goalkeeper' in posicao:
            return 'Goleiro'
        elif 'zagueiro' in posicao or 'defender' in posicao or 'defensor' in posicao:
            return 'Zagueiro'
        elif 'lateral' in posicao:
            return 'Lateral'
        elif 'volante' in posicao or 'defensive mid' in posicao:
            return 'Volante'
        elif 'meia' in posicao or 'midfielder' in posicao:
            return 'Meia'
        elif 'atacante' in posicao or 'forward' in posicao or 'striker' in posicao:
            return 'Atacante'
        else:
            return 'Meia'
    
    def _calculate_attack_rating(
        self, gols: int, assists: int, shots: int, jogos: int, posicao: str
    ) -> float:
        """
        Calcula rating ofensivo (0-100).
        Ajustado pela posição.
        """
        if jogos == 0:
            return 50.0
        
        # Gols e assistências por jogo
        gols_pj = gols / jogos
        assists_pj = assists / jogos
        shots_pj = shots / jogos
        
        # Score base (ajustado por posição)
        peso = self.PESOS_POSICAO.get(posicao, {'ataque': 0.5})['ataque']
        
        if peso == 0:  # Goleiro
            return 50.0
        
        # Normalizar para 0-100
        # Referência: atacante elite = 0.7 gols/jogo, 0.4 assists/jogo
        score = (
            (gols_pj / 0.7) * 40 +      # Peso maior para gols
            (assists_pj / 0.4) * 35 +    # Assistências
            (shots_pj / 3.0) * 25        # Finalizações
        ) * peso
        
        return min(max(score, 0), 100)
    
    def _calculate_defense_rating(
        self, desarmes: int, interceptacoes: int, jogos: int, posicao: str
    ) -> float:
        """Calcula rating defensivo (0-100)."""
        if jogos == 0:
            return 50.0
        
        peso = self.PESOS_POSICAO.get(posicao, {'defesa': 0.5})['defesa']
        
        if peso == 0:  # Atacante não é cobrado por defesa
            return 50.0
        
        # Por jogo
        desarmes_pj = desarmes / jogos
        inter_pj = interceptacoes / jogos
        
        # Normalizar (zagueiro elite = 3 desarmes + 2 interceptações por jogo)
        score = (
            (desarmes_pj / 3.0) * 50 +
            (inter_pj / 2.0) * 50
        ) * peso
        
        return min(max(score, 0), 100)

    def _calculate_corners_rating(
        self, escanteios_batidos: int, finalizacoes: int, jogos: int, posicao: str
    ) -> float:
        """Calcula influência em escanteios (0-100) combinando bolas paradas e volume ofensivo."""
        if jogos == 0:
            return 50.0
        # Referência: especialista bate ~2.5 escanteios/jogo
        esc_pj = escanteios_batidos / jogos
        fin_pj = finalizacoes / jogos
        peso = 0.6 if posicao in ['Lateral', 'Meia'] else 0.4
        score = (esc_pj / 2.5) * 70 + (fin_pj / 3.0) * 30
        return min(max(score * peso, 0), 100)
    
    def _calculate_discipline_rating(
        self, faltas: int, amarelos: int, vermelhos: int, jogos: int
    ) -> float:
        """
        Calcula rating de disciplina (0-100).
        100 = sem cartões, 0 = muitos cartões.
        """
        if jogos == 0:
            return 70.0  # Sem dados, assume razoável
        
        # Cartões por jogo (vermelho = 3x amarelo)
        cartoes_pj = (amarelos + vermelhos * 3) / jogos
        
        # 0 cartões = 100, 1 cartão/jogo = 0
        score = 100 - (cartoes_pj * 100)
        
        return min(max(score, 0), 100)
    
    def _default_rating(self, player_id: int) -> PlayerRating:
        """Rating padrão quando não há dados."""
        return PlayerRating(
            player_id=player_id,
            nome=f"Jogador {player_id}",
            posicao="Meia",
            rating_geral=50.0,
            rating_ataque=50.0,
            rating_defesa=50.0,
            rating_disciplina=70.0
        )
    
    def get_team_players_ratings(self, team_id: int) -> List[PlayerRating]:
        """Retorna ratings de todos os jogadores de um time."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id FROM players WHERE time_atual_id = %s
        """, (team_id,))
        
        players = cursor.fetchall()
        conn.close()
        
        return [self.calculate_player_rating(p['id']) for p in players]
    
    def calculate_lineup_strength(self, player_ids: List[int]) -> dict:
        """
        Calcula força agregada de uma escalação.
        
        Usado para ajustar λ, μ, κ baseado em quem vai jogar.
        """
        if not player_ids:
            return {
                'ataque': 50.0,
                'defesa': 50.0,
                'disciplina': 70.0,
                'escanteios': 50.0,
                'rating_medio': 50.0
            }
        
        ratings = [self.calculate_player_rating(pid) for pid in player_ids]
        
        return {
            'ataque': np.mean([r.rating_ataque for r in ratings]),
            'defesa': np.mean([r.rating_defesa for r in ratings]),
            'disciplina': np.mean([r.rating_disciplina for r in ratings]),
            'escanteios': np.mean([r.rating_escanteios for r in ratings]),
            'rating_medio': np.mean([r.rating_geral for r in ratings]),
            'jogadores': len(ratings)
        }

    def calculate_lineup_ratios(self, player_ids: List[int]) -> dict:
        """Converte força da escalação em multiplicadores (ratios) para λ/κ/μ."""
        strength = self.calculate_lineup_strength(player_ids)
        ataque = strength['ataque']
        esc = strength.get('escanteios', 50.0)
        disciplina = strength['disciplina']
        
        def _ratio(value: float, base: float, sens: float, low: float = 0.7, high: float = 1.35) -> float:
            delta = (value - base) / 100.0
            return max(low, min(high, 1.0 + delta * sens))
        
        indisciplina = max(0.0, 70.0 - disciplina)
        return {
            'off_ratio': _ratio(ataque, 50.0, 0.8),
            'cross_ratio': _ratio(esc, 50.0, 0.6),
            'foul_ratio': _ratio(indisciplina, 0.0, 0.8, low=0.85, high=1.6),
            'strength_snapshot': strength
        }
