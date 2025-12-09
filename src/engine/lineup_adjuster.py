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
        lineup_visitante: List[int]
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
        # Calcular força das escalações
        strength_m = self.player_model.calculate_lineup_strength(lineup_mandante)
        strength_v = self.player_model.calculate_lineup_strength(lineup_visitante)
        
        # Desvio do rating médio
        delta_ataque_m = strength_m['ataque'] - self.RATING_MEDIO_ATAQUE
        delta_ataque_v = strength_v['ataque'] - self.RATING_MEDIO_ATAQUE
        delta_defesa_m = strength_m['defesa'] - self.RATING_MEDIO_DEFESA
        delta_defesa_v = strength_v['defesa'] - self.RATING_MEDIO_DEFESA
        delta_disc_m = self.RATING_MEDIO_DISCIPLINA - strength_m['disciplina']  # Invertido
        delta_disc_v = self.RATING_MEDIO_DISCIPLINA - strength_v['disciplina']
        
        # Ajustar gols
        # λ_mandante aumenta se: ataque mandante bom OU defesa visitante ruim
        fator_lambda_m = (
            1.0 + 
            self.ALPHA_ATAQUE * delta_ataque_m +
            self.ALPHA_DEFESA * (-delta_defesa_v)  # Defesa ruim do visitante = mais gols
        )
        
        fator_lambda_v = (
            1.0 +
            self.ALPHA_ATAQUE * delta_ataque_v +
            self.ALPHA_DEFESA * (-delta_defesa_m)
        )
        
        # Ajustar cartões (disciplina ruim = mais cartões)
        fator_mu_m = 1.0 + self.ALPHA_DISCIPLINA * delta_disc_m
        fator_mu_v = 1.0 + self.ALPHA_DISCIPLINA * delta_disc_v
        
        # Aplicar ajustes
        adjusted = {
            'lambda_mandante': params['lambda_mandante'] * max(0.7, min(fator_lambda_m, 1.4)),
            'lambda_visitante': params['lambda_visitante'] * max(0.7, min(fator_lambda_v, 1.4)),
            'mu_mandante': params['mu_mandante'] * max(0.7, min(fator_mu_m, 1.5)),
            'mu_visitante': params['mu_visitante'] * max(0.7, min(fator_mu_v, 1.5)),
            'kappa_mandante': params.get('kappa_mandante', 5.0),
            'kappa_visitante': params.get('kappa_visitante', 4.0),
            
            # Metadados
            'ajuste_aplicado': True,
            'strength_mandante': strength_m,
            'strength_visitante': strength_v
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
