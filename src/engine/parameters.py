"""
ETAPA 5 - Cálculo de Parâmetros (λ, μ, κ)

Transforma força de times em parâmetros das distribuições:
- λ (lambda): gols esperados
- μ (mu): cartões esperados  
- κ (kappa): escanteios esperados

Usa modelo log-linear:
log(λ₁) = β₀ + A₁ (ataque time 1) + D₂ (defesa time 2) + H (mando)

Ou forma multiplicativa:
λ₁ = λ_base × f(A₁) × g(D₂) × h(mando)
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from src.core.league_stats import LeagueStats, LeagueAverages
from src.core.team_model import TeamModel, TeamStrength


@dataclass
class MatchParameters:
    """Parâmetros calculados para uma partida."""
    # Gols
    lambda_mandante: float  # Gols esperados do mandante
    lambda_visitante: float  # Gols esperados do visitante
    lambda_total: float
    
    # Cartões
    mu_mandante: float
    mu_visitante: float
    mu_total: float
    
    # Escanteios
    kappa_mandante: float
    kappa_visitante: float
    kappa_total: float
    
    # Metadados
    confianca: float  # 0-1, quão confiável é a previsão
    base_params: dict = field(default_factory=dict)
    lineup_adjustments: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'gols': {
                'mandante': round(self.lambda_mandante, 2),
                'visitante': round(self.lambda_visitante, 2),
                'total': round(self.lambda_total, 2)
            },
            'cartoes': {
                'mandante': round(self.mu_mandante, 2),
                'visitante': round(self.mu_visitante, 2),
                'total': round(self.mu_total, 2)
            },
            'escanteios': {
                'mandante': round(self.kappa_mandante, 2),
                'visitante': round(self.kappa_visitante, 2),
                'total': round(self.kappa_total, 2)
            },
            'confianca': round(self.confianca, 2),
            'base_params': self.base_params,
            'lineup_adjustments': self.lineup_adjustments
        }


class ParameterCalculator:
    """
    Calcula os parâmetros λ, μ, κ para uma partida.
    
    Modelo:
    λ₁ = média_liga × ataque_time1 × defesa_time2 × fator_mando
    
    Trabalhamos no log para somar efeitos:
    log(λ₁) = log(média) + log(ataque₁) + log(defesa₂) + log(mando)
    """
    
    # Fatores de ajuste
    FATOR_MANDANTE_GOLS = 1.15      # Mandante faz 15% mais gols
    FATOR_VISITANTE_GOLS = 0.90     # Visitante faz 10% menos
    FATOR_MANDANTE_CARTOES = 0.90   # Mandante leva menos cartões
    FATOR_VISITANTE_CARTOES = 1.15  # Visitante leva mais cartões
    FATOR_MANDANTE_ESCANTEIOS = 1.10
    FATOR_VISITANTE_ESCANTEIOS = 0.95
    
    def __init__(self, league_stats: LeagueStats, team_model: TeamModel):
        self.league_stats = league_stats
        self.team_model = team_model
    
    def calculate(
        self,
        mandante_id: int,
        visitante_id: int,
        league_id: int,
        temporada: str = "2025"
    ) -> MatchParameters:
        """
        Calcula parâmetros para uma partida.
        
        Args:
            mandante_id: ID do time da casa
            visitante_id: ID do visitante
            league_id: ID da liga
            temporada: Temporada
            
        Returns:
            MatchParameters com λ, μ, κ calculados
        """
        # Médias da liga (âncoras)
        league_avg = self.league_stats.calculate_averages(league_id, temporada)
        
        # Força dos times
        mandante = self.team_model.calculate_team_strength(mandante_id, league_id, temporada)
        visitante = self.team_model.calculate_team_strength(visitante_id, league_id, temporada)
        
        # Calcular λ (gols)
        lambda_m, lambda_v, lambda_meta = self._calculate_goals_lambda(
            league_avg, mandante, visitante
        )
        
        # Calcular μ (cartões)
        mu_m, mu_v, mu_meta = self._calculate_cards_mu(
            league_avg, mandante, visitante
        )
        
        # Calcular κ (escanteios)
        kappa_m, kappa_v, kappa_meta = self._calculate_corners_kappa(
            league_avg, mandante, visitante
        )
        
        # Confiança baseada no mínimo de jogos dos times
        confianca = min(mandante.confianca, visitante.confianca)
        
        return MatchParameters(
            lambda_mandante=lambda_m,
            lambda_visitante=lambda_v,
            lambda_total=lambda_m + lambda_v,
            mu_mandante=mu_m,
            mu_visitante=mu_v,
            mu_total=mu_m + mu_v,
            kappa_mandante=kappa_m,
            kappa_visitante=kappa_v,
            kappa_total=kappa_m + kappa_v,
            confianca=confianca,
            base_params={
                'mandante': {
                    'gols': round(lambda_m, 4),
                    'cartoes': round(mu_m, 4),
                    'escanteios': round(kappa_m, 4)
                },
                'visitante': {
                    'gols': round(lambda_v, 4),
                    'cartoes': round(mu_v, 4),
                    'escanteios': round(kappa_v, 4)
                },
                'fatores': {
                    'gols': lambda_meta,
                    'cartoes': mu_meta,
                    'escanteios': kappa_meta,
                    'anchors': {
                        'gols_mandante': league_avg.gols_mandante,
                        'gols_visitante': league_avg.gols_visitante,
                        'cartoes_mandante': league_avg.cartoes_mandante,
                        'cartoes_visitante': league_avg.cartoes_visitante,
                        'escanteios_mandante': league_avg.escanteios_mandante,
                        'escanteios_visitante': league_avg.escanteios_visitante
                    }
                }
            }
        )
    
    def _calculate_goals_lambda(
        self,
        league: LeagueAverages,
        mandante: TeamStrength,
        visitante: TeamStrength
    ) -> tuple:
        """
        Calcula λ para gols usando modelo multiplicativo.
        
        λ_mandante = média_gols_mandante × ataque_mandante × defesa_visitante × fator_casa
        λ_visitante = média_gols_visitante × ataque_visitante × defesa_mandante × fator_fora
        """
        # Mandante: seu ataque em casa vs defesa do visitante fora
        lambda_m = (
            league.gols_mandante *
            mandante.ataque_casa *
            visitante.defesa_fora *
            self.FATOR_MANDANTE_GOLS
        )
        
        # Visitante: seu ataque fora vs defesa do mandante em casa
        lambda_v = (
            league.gols_visitante *
            visitante.ataque_fora *
            mandante.defesa_casa *
            self.FATOR_VISITANTE_GOLS
        )
        
        # Limitar valores extremos
        raw_meta = {
            'mandante': {
                'anchor': league.gols_mandante,
                'ataque': mandante.ataque_casa,
                'defesa_adversario': visitante.defesa_fora,
                'fator_mando': self.FATOR_MANDANTE_GOLS
            },
            'visitante': {
                'anchor': league.gols_visitante,
                'ataque': visitante.ataque_fora,
                'defesa_adversario': mandante.defesa_casa,
                'fator_mando': self.FATOR_VISITANTE_GOLS
            }
        }
        
        lambda_m = max(0.3, min(lambda_m, 5.0))
        lambda_v = max(0.2, min(lambda_v, 4.0))
        
        return lambda_m, lambda_v, raw_meta
    
    def _calculate_cards_mu(
        self,
        league: LeagueAverages,
        mandante: TeamStrength,
        visitante: TeamStrength
    ) -> tuple:
        """Calcula μ para cartões."""
        mu_m = (
            league.cartoes_mandante *
            mandante.cartoes_favor *
            visitante.cartoes_contra *
            self.FATOR_MANDANTE_CARTOES
        )
        
        mu_v = (
            league.cartoes_visitante *
            visitante.cartoes_favor *
            mandante.cartoes_contra *
            self.FATOR_VISITANTE_CARTOES
        )
        
        # Limitar
        raw_meta = {
            'mandante': {
                'anchor': league.cartoes_mandante,
                'disciplina_propria': mandante.cartoes_favor,
                'disciplina_adv': visitante.cartoes_contra,
                'fator_mando': self.FATOR_MANDANTE_CARTOES
            },
            'visitante': {
                'anchor': league.cartoes_visitante,
                'disciplina_propria': visitante.cartoes_favor,
                'disciplina_adv': mandante.cartoes_contra,
                'fator_mando': self.FATOR_VISITANTE_CARTOES
            }
        }
        
        mu_m = max(1.0, min(mu_m, 6.0))
        mu_v = max(1.0, min(mu_v, 6.0))
        
        return mu_m, mu_v, raw_meta
    
    def _calculate_corners_kappa(
        self,
        league: LeagueAverages,
        mandante: TeamStrength,
        visitante: TeamStrength
    ) -> tuple:
        """Calcula κ para escanteios."""
        kappa_m = (
            league.escanteios_mandante *
            mandante.escanteios_favor *
            visitante.escanteios_contra *
            self.FATOR_MANDANTE_ESCANTEIOS
        )
        
        kappa_v = (
            league.escanteios_visitante *
            visitante.escanteios_favor *
            mandante.escanteios_contra *
            self.FATOR_VISITANTE_ESCANTEIOS
        )
        
        # Limitar
        raw_meta = {
            'mandante': {
                'anchor': league.escanteios_mandante,
                'forca_propria': mandante.escanteios_favor,
                'concede_adv': visitante.escanteios_contra,
                'fator_mando': self.FATOR_MANDANTE_ESCANTEIOS
            },
            'visitante': {
                'anchor': league.escanteios_visitante,
                'forca_propria': visitante.escanteios_favor,
                'concede_adv': mandante.escanteios_contra,
                'fator_mando': self.FATOR_VISITANTE_ESCANTEIOS
            }
        }
        
        kappa_m = max(2.0, min(kappa_m, 12.0))
        kappa_v = max(2.0, min(kappa_v, 10.0))
        
        return kappa_m, kappa_v, raw_meta
    
    def calculate_with_log(
        self,
        mandante_id: int,
        visitante_id: int,
        league_id: int,
        temporada: str = "2025"
    ) -> MatchParameters:
        """
        Versão alternativa usando modelo log-linear.
        
        log(λ) = β₀ + β₁·ataque + β₂·defesa + β₃·mando
        λ = exp(log(λ))
        
        Vantagem: efeitos são aditivos no log, não há valores negativos.
        """
        league_avg = self.league_stats.calculate_averages(league_id, temporada)
        mandante = self.team_model.calculate_team_strength(mandante_id, league_id, temporada)
        visitante = self.team_model.calculate_team_strength(visitante_id, league_id, temporada)
        
        # Coeficientes (podem ser calibrados)
        beta_0 = np.log(league_avg.gols_mandante)  # Intercepto
        beta_ataque = 0.5  # Peso do ataque
        beta_defesa = 0.5  # Peso da defesa
        beta_mando = np.log(self.FATOR_MANDANTE_GOLS)
        
        # Log-linear para mandante
        log_lambda_m = (
            beta_0 +
            beta_ataque * np.log(mandante.ataque_casa) +
            beta_defesa * np.log(visitante.defesa_fora) +
            beta_mando
        )
        
        # Log-linear para visitante
        log_lambda_v = (
            np.log(league_avg.gols_visitante) +
            beta_ataque * np.log(visitante.ataque_fora) +
            beta_defesa * np.log(mandante.defesa_casa) +
            np.log(self.FATOR_VISITANTE_GOLS)
        )
        
        lambda_m = np.exp(log_lambda_m)
        lambda_v = np.exp(log_lambda_v)
        
        # Cartões e escanteios seguem mesma lógica
        mu_m, mu_v = self._calculate_cards_mu(league_avg, mandante, visitante)
        kappa_m, kappa_v = self._calculate_corners_kappa(league_avg, mandante, visitante)
        
        return MatchParameters(
            lambda_mandante=max(0.3, min(lambda_m, 5.0)),
            lambda_visitante=max(0.2, min(lambda_v, 4.0)),
            lambda_total=lambda_m + lambda_v,
            mu_mandante=mu_m,
            mu_visitante=mu_v,
            mu_total=mu_m + mu_v,
            kappa_mandante=kappa_m,
            kappa_visitante=kappa_v,
            kappa_total=kappa_m + kappa_v,
            confianca=min(mandante.confianca, visitante.confianca)
        )
