"""
ETAPA 9 - Predictions (Previsões Finais)

Orquestra todo o pipeline:
1. Carrega dados dos times
2. Calcula parâmetros
3. Ajusta por contexto e escalação
4. Roda Monte Carlo
5. Retorna previsões completas
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import json

from src.core.league_stats import LeagueStats
from src.core.team_model import TeamModel
from src.core.player_model import PlayerModel
from src.engine.parameters import ParameterCalculator, MatchParameters
from src.engine.context import MatchContext, ContextAdjuster
from src.engine.lineup_adjuster import LineupAdjuster
from src.engine.monte_carlo import MonteCarloSimulator, SimulationResult


@dataclass
class MatchPrediction:
    """Previsão completa para uma partida."""
    
    # Times
    mandante: str
    visitante: str
    mandante_id: int
    visitante_id: int
    
    # Parâmetros calculados
    parameters: MatchParameters
    
    # Resultado da simulação
    simulation: SimulationResult
    
    # Confiança geral
    confianca: float
    
    # Se usou escalação
    com_escalacao: bool = False
    
    def to_dict(self) -> dict:
        """Converte para dicionário completo."""
        return {
            'partida': {
                'mandante': self.mandante,
                'visitante': self.visitante,
                'mandante_id': self.mandante_id,
                'visitante_id': self.visitante_id
            },
            'parametros': self.parameters.to_dict(),
            'previsao': self.simulation.to_dict(),
            'confianca': round(self.confianca * 100, 1),
            'com_escalacao': self.com_escalacao
        }
    
    def resumo(self) -> dict:
        """Resumo executivo da previsão."""
        sim = self.simulation
        return {
            'partida': f"{self.mandante} x {self.visitante}",
            'resultado': {
                'favorito': self._get_favorito(),
                'vitoria_mandante': f"{sim.prob_vitoria_mandante * 100:.1f}%",
                'empate': f"{sim.prob_empate * 100:.1f}%",
                'vitoria_visitante': f"{sim.prob_vitoria_visitante * 100:.1f}%"
            },
            'gols': {
                'esperados': f"{sim.gols_total_media:.1f}",
                'over_2.5': f"{sim.prob_over_25 * 100:.1f}%"
            },
            'placar_provavel': sim.placares_provaveis[0] if sim.placares_provaveis else None,
            'confianca': f"{self.confianca * 100:.0f}%"
        }
    
    def _get_favorito(self) -> str:
        sim = self.simulation
        if sim.prob_vitoria_mandante > sim.prob_vitoria_visitante:
            if sim.prob_vitoria_mandante > sim.prob_empate:
                return self.mandante
        elif sim.prob_vitoria_visitante > sim.prob_empate:
            return self.visitante
        return "Equilíbrio"


class MatchPredictor:
    """
    Preditor principal de partidas.
    
    Integra todos os módulos para gerar previsões completas.
    """
    
    def __init__(self, db_config: dict, n_simulations: int = 100_000):
        """
        Args:
            db_config: Configuração do banco de dados
            n_simulations: Número de simulações Monte Carlo
        """
        self.db_config = db_config
        
        # Inicializar componentes
        self.league_stats = LeagueStats(db_config)
        self.team_model = TeamModel(db_config, self.league_stats)
        self.player_model = PlayerModel(db_config)
        self.param_calculator = ParameterCalculator(self.league_stats, self.team_model)
        self.context_adjuster = ContextAdjuster()
        self.lineup_adjuster = LineupAdjuster(self.player_model)
        self.simulator = MonteCarloSimulator(n_simulations)
    
    def predict(
        self,
        mandante_id: int,
        visitante_id: int,
        league_id: int,
        temporada: str = "2025",
        context: Optional[MatchContext] = None,
        lineup_mandante: Optional[List[int]] = None,
        lineup_visitante: Optional[List[int]] = None
    ) -> MatchPrediction:
        """
        Gera previsão completa para uma partida.
        
        Args:
            mandante_id: ID do time da casa
            visitante_id: ID do visitante
            league_id: ID da liga
            temporada: Temporada
            context: Contexto da partida (opcional)
            lineup_mandante: Escalação do mandante (opcional)
            lineup_visitante: Escalação do visitante (opcional)
            
        Returns:
            MatchPrediction com previsão completa
        """
        # 1. Calcular parâmetros base
        params = self.param_calculator.calculate(
            mandante_id, visitante_id, league_id, temporada
        )
        
        # Converter para dict para ajustes
        params_dict = {
            'lambda_mandante': params.lambda_mandante,
            'lambda_visitante': params.lambda_visitante,
            'mu_mandante': params.mu_mandante,
            'mu_visitante': params.mu_visitante,
            'kappa_mandante': params.kappa_mandante,
            'kappa_visitante': params.kappa_visitante
        }
        
        # 2. Ajustar por contexto
        if context:
            params_dict = self.context_adjuster.adjust_parameters(params_dict, context)
        
        # 3. Ajustar por escalação
        com_escalacao = False
        if lineup_mandante and lineup_visitante:
            params_dict = self.lineup_adjuster.adjust_for_lineup(
                params_dict, lineup_mandante, lineup_visitante
            )
            com_escalacao = True
        
        # 4. Rodar Monte Carlo
        simulation = self.simulator.simulate_from_params(params_dict)
        
        # 5. Buscar nomes dos times
        mandante = self.team_model.calculate_team_strength(mandante_id, league_id)
        visitante = self.team_model.calculate_team_strength(visitante_id, league_id)
        
        return MatchPrediction(
            mandante=mandante.team_name,
            visitante=visitante.team_name,
            mandante_id=mandante_id,
            visitante_id=visitante_id,
            parameters=params,
            simulation=simulation,
            confianca=params.confianca,
            com_escalacao=com_escalacao
        )
    
    def predict_quick(
        self,
        mandante_id: int,
        visitante_id: int,
        league_id: int
    ) -> dict:
        """
        Previsão rápida (só probabilidades de resultado).
        """
        params = self.param_calculator.calculate(mandante_id, visitante_id, league_id)
        
        result = self.simulator.quick_simulate(
            params.lambda_mandante,
            params.lambda_visitante
        )
        
        mandante = self.team_model.calculate_team_strength(mandante_id, league_id)
        visitante = self.team_model.calculate_team_strength(visitante_id, league_id)
        
        return {
            'partida': f"{mandante.team_name} x {visitante.team_name}",
            **result
        }
    
    def predict_round(
        self,
        matches: List[Dict],
        league_id: int
    ) -> List[MatchPrediction]:
        """
        Prevê todas as partidas de uma rodada.
        
        Args:
            matches: Lista de dicts com mandante_id, visitante_id
            league_id: ID da liga
            
        Returns:
            Lista de previsões
        """
        predictions = []
        for match in matches:
            pred = self.predict(
                mandante_id=match['mandante_id'],
                visitante_id=match['visitante_id'],
                league_id=league_id
            )
            predictions.append(pred)
        
        return predictions
    
    def compare_scenarios(
        self,
        mandante_id: int,
        visitante_id: int,
        league_id: int,
        lineups: List[Dict]
    ) -> List[Dict]:
        """
        Compara diferentes cenários de escalação.
        
        Args:
            lineups: Lista de dicts com 'nome', 'mandante', 'visitante'
            
        Returns:
            Comparação dos cenários
        """
        results = []
        
        for scenario in lineups:
            pred = self.predict(
                mandante_id=mandante_id,
                visitante_id=visitante_id,
                league_id=league_id,
                lineup_mandante=scenario.get('mandante'),
                lineup_visitante=scenario.get('visitante')
            )
            
            results.append({
                'cenario': scenario.get('nome', 'Sem nome'),
                'previsao': pred.resumo()
            })
        
        return results
