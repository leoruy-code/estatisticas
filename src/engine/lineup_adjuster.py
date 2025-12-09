"""
ETAPA 7.3 - Ajuste por Escalação

Ajusta os parâmetros λ, μ, κ baseado na escalação:
- Escalação mais ofensiva → λ sobe
- Escalação com jogadores indisciplinados → μ sobe
- Jogadores chave fora → ajuste proporcional
"""

from typing import List, Optional, Dict
import numpy as np

from src.core.player_model import PlayerModel, PlayerRating


class LineupAdjuster:
    """
    Ajusta parâmetros baseado na escalação.
    
    Lógica:
    λ_ajustado = λ_base × (1 + α × (rating_escalação - rating_médio))
    
    onde α é um fator de sensibilidade.
    """
    
    # Rating médio de referência (time "normal")
    RATING_MEDIO_ATAQUE = 50.0
    RATING_MEDIO_DEFESA = 50.0
    RATING_MEDIO_DISCIPLINA = 70.0
    
    # Sensibilidade dos ajustes (quanto 1 ponto de rating afeta)
    ALPHA_ATAQUE = 0.01      # +1 rating = +1% em λ
    ALPHA_DEFESA = 0.01      # +1 rating = +1% em defesa
    ALPHA_DISCIPLINA = 0.015 # +1 rating = +1.5% em cartões
    
    def __init__(self, player_model: PlayerModel):
        self.player_model = player_model
    
    def adjust_for_lineup(
        self,
        params: dict,
        lineup_mandante: List[int],
        lineup_visitante: List[int],
        confidence_mandante: float = 1.0,
        confidence_visitante: float = 1.0
    ) -> dict:
        """
        Ajusta parâmetros baseado nas escalações.
        
        Args:
            params: Dict com lambda_mandante, lambda_visitante, etc.
            lineup_mandante: IDs dos jogadores titulares do mandante
            lineup_visitante: IDs dos jogadores titulares do visitante
            
        Returns:
            Dict com parâmetros ajustados
        """
        # Multiplicadores a partir das escalações
        ratios_m = self.player_model.calculate_lineup_ratios(lineup_mandante)
        ratios_v = self.player_model.calculate_lineup_ratios(lineup_visitante)
        
        def _blend(base_ratio: float, confidence: float) -> float:
            """Blenda ratio com neutro=1.0 de acordo com confiança (0=ignora lineup)."""
            conf = max(0.0, min(1.0, confidence))
            return 1.0 + (base_ratio - 1.0) * conf

        adjusted = {
            'lambda_mandante': params['lambda_mandante'] * _blend(ratios_m['off_ratio'], confidence_mandante) * max(0.8, min(1.2, 1.0 / _blend(ratios_v.get('off_ratio', 1.0), confidence_visitante))),
            'lambda_visitante': params['lambda_visitante'] * _blend(ratios_v['off_ratio'], confidence_visitante) * max(0.8, min(1.2, 1.0 / _blend(ratios_m.get('off_ratio', 1.0), confidence_mandante))),
            'mu_mandante': params['mu_mandante'] * _blend(ratios_m['foul_ratio'], confidence_mandante),
            'mu_visitante': params['mu_visitante'] * _blend(ratios_v['foul_ratio'], confidence_visitante),
            'kappa_mandante': params.get('kappa_mandante', 5.0) * _blend(ratios_m['cross_ratio'], confidence_mandante),
            'kappa_visitante': params.get('kappa_visitante', 4.0) * _blend(ratios_v['cross_ratio'], confidence_visitante),
            
            # Metadados
            'ajuste_aplicado': True,
            'lineup_ratios': {
                'mandante': ratios_m,
                'visitante': ratios_v
            },
            'lineup_confidence': {
                'mandante': max(0.0, min(1.0, confidence_mandante)),
                'visitante': max(0.0, min(1.0, confidence_visitante))
            }
        }
        
        return adjusted
    
    def get_key_players_impact(
        self,
        team_id: int,
        missing_player_ids: List[int]
    ) -> dict:
        """
        Calcula impacto de jogadores chave ausentes.
        
        Returns:
            Dict com impacto estimado em cada dimensão
        """
        # Pegar ratings do time completo
        all_players = self.player_model.get_team_players_ratings(team_id)
        
        # Identificar ausentes
        missing = [p for p in all_players if p.player_id in missing_player_ids]
        
        if not missing:
            return {'ataque': 0, 'defesa': 0, 'disciplina': 0}
        
        # Calcular impacto (média dos ausentes vs média do elenco)
        avg_team_ataque = np.mean([p.rating_ataque for p in all_players])
        avg_missing_ataque = np.mean([p.rating_ataque for p in missing])
        
        avg_team_defesa = np.mean([p.rating_defesa for p in all_players])
        avg_missing_defesa = np.mean([p.rating_defesa for p in missing])
        
        return {
            'ataque': avg_team_ataque - avg_missing_ataque,
            'defesa': avg_team_defesa - avg_missing_defesa,
            'jogadores_ausentes': [p.nome for p in missing]
        }
    
    def suggest_optimal_lineup(
        self,
        team_id: int,
        objective: str = 'balanced'
    ) -> Dict:
        """
        Sugere escalação otimizada para um objetivo.
        
        Args:
            team_id: ID do time
            objective: 'attack', 'defense', 'balanced'
            
        Returns:
            Dict com escalação sugerida
        """
        players = self.player_model.get_team_players_ratings(team_id)
        
        if not players:
            return {'error': 'Sem jogadores'}
        
        # Separar por posição
        goleiros = [p for p in players if p.posicao == 'Goleiro']
        zagueiros = [p for p in players if p.posicao == 'Zagueiro']
        laterais = [p for p in players if p.posicao == 'Lateral']
        volantes = [p for p in players if p.posicao == 'Volante']
        meias = [p for p in players if p.posicao == 'Meia']
        atacantes = [p for p in players if p.posicao == 'Atacante']
        
        # Ordenar por objetivo
        if objective == 'attack':
            key_func = lambda p: p.rating_ataque
        elif objective == 'defense':
            key_func = lambda p: p.rating_defesa
        else:  # balanced
            key_func = lambda p: p.rating_geral
        
        # Montar 4-3-3 ou formação similar
        lineup = []
        
        if goleiros:
            lineup.extend(sorted(goleiros, key=key_func, reverse=True)[:1])
        if zagueiros:
            lineup.extend(sorted(zagueiros, key=key_func, reverse=True)[:2])
        if laterais:
            lineup.extend(sorted(laterais, key=key_func, reverse=True)[:2])
        if volantes:
            lineup.extend(sorted(volantes, key=key_func, reverse=True)[:1])
        if meias:
            lineup.extend(sorted(meias, key=key_func, reverse=True)[:2])
        if atacantes:
            lineup.extend(sorted(atacantes, key=key_func, reverse=True)[:3])
        
        # Completar até 11 se necessário
        all_sorted = sorted(players, key=key_func, reverse=True)
        while len(lineup) < 11 and all_sorted:
            candidate = all_sorted.pop(0)
            if candidate not in lineup:
                lineup.append(candidate)
        
        return {
            'formacao': '4-3-3',
            'objetivo': objective,
            'jogadores': [
                {
                    'id': p.player_id,
                    'nome': p.nome,
                    'posicao': p.posicao,
                    'rating': round(p.rating_geral, 1)
                }
                for p in lineup[:11]
            ],
            'strength': self.player_model.calculate_lineup_strength(
                [p.player_id for p in lineup[:11]]
            )
        }
