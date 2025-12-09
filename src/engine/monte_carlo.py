"""
ETAPA 8 - Simulação Monte Carlo

Transforma parâmetros (λ, μ, κ) em probabilidades através de simulação.

Para cada partida:
1. Sorteia gols de cada time (Poisson ou NegBinomial)
2. Sorteia cartões e escanteios
3. Registra resultados
4. Repete milhares de vezes
5. Calcula frequências relativas = probabilidades
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import Counter

from src.core.distributions import PoissonModel, NegBinomialModel, DistributionFactory


@dataclass
class SimulationResult:
    """Resultado de uma simulação Monte Carlo."""
    
    # Número de simulações
    n_simulations: int
    
    # Probabilidades de resultado
    prob_vitoria_mandante: float
    prob_empate: float
    prob_vitoria_visitante: float
    
    # Distribuição de gols
    gols_mandante_media: float
    gols_visitante_media: float
    gols_total_media: float
    prob_over_15: float
    prob_over_25: float
    prob_over_35: float
    prob_under_25: float
    prob_btts: float  # Both teams to score
    
    # Placares mais prováveis
    placares_provaveis: List[Dict]
    
    # Distribuição de cartões
    cartoes_mandante_media: float
    cartoes_visitante_media: float
    cartoes_total_media: float
    prob_over_35_cartoes: float
    prob_over_45_cartoes: float
    
    # Distribuição de escanteios
    escanteios_mandante_media: float
    escanteios_visitante_media: float
    escanteios_total_media: float
    prob_over_85_escanteios: float
    prob_over_105_escanteios: float
    
    # Intervalos de confiança
    intervalo_gols_80: Tuple[int, int] = (0, 0)
    intervalo_cartoes_80: Tuple[int, int] = (0, 0)
    intervalo_escanteios_80: Tuple[int, int] = (0, 0)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'simulacoes': self.n_simulations,
            'resultado': {
                'vitoria_mandante': round(self.prob_vitoria_mandante * 100, 1),
                'empate': round(self.prob_empate * 100, 1),
                'vitoria_visitante': round(self.prob_vitoria_visitante * 100, 1)
            },
            'gols': {
                'mandante_media': round(self.gols_mandante_media, 2),
                'visitante_media': round(self.gols_visitante_media, 2),
                'total_media': round(self.gols_total_media, 2),
                'over_1.5': round(self.prob_over_15 * 100, 1),
                'over_2.5': round(self.prob_over_25 * 100, 1),
                'over_3.5': round(self.prob_over_35 * 100, 1),
                'under_2.5': round(self.prob_under_25 * 100, 1),
                'btts': round(self.prob_btts * 100, 1)
            },
            'placares': self.placares_provaveis,
            'cartoes': {
                'mandante_media': round(self.cartoes_mandante_media, 2),
                'visitante_media': round(self.cartoes_visitante_media, 2),
                'total_media': round(self.cartoes_total_media, 2),
                'over_3.5': round(self.prob_over_35_cartoes * 100, 1),
                'over_4.5': round(self.prob_over_45_cartoes * 100, 1)
            },
            'escanteios': {
                'mandante_media': round(self.escanteios_mandante_media, 2),
                'visitante_media': round(self.escanteios_visitante_media, 2),
                'total_media': round(self.escanteios_total_media, 2),
                'over_8.5': round(self.prob_over_85_escanteios * 100, 1),
                'over_10.5': round(self.prob_over_105_escanteios * 100, 1)
            }
        }


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para partidas de futebol.
    
    Gera milhares de "mundos possíveis" e calcula probabilidades
    como frequências relativas.
    """
    
    DEFAULT_SIMULATIONS = 100_000
    
    def __init__(self, n_simulations: int = DEFAULT_SIMULATIONS, seed: Optional[int] = None):
        """
        Args:
            n_simulations: Número de simulações (mais = mais preciso)
            seed: Seed para reprodutibilidade
        """
        self.n_simulations = n_simulations
        if seed is not None:
            np.random.seed(seed)
    
    def simulate(
        self,
        lambda_mandante: float,
        lambda_visitante: float,
        mu_mandante: float = 2.0,
        mu_visitante: float = 2.5,
        kappa_mandante: float = 5.0,
        kappa_visitante: float = 4.0,
        use_negbinomial_cards: bool = True
    ) -> SimulationResult:
        """
        Executa simulação Monte Carlo.
        
        Args:
            lambda_mandante: λ para gols do mandante
            lambda_visitante: λ para gols do visitante
            mu_mandante: μ para cartões do mandante
            mu_visitante: μ para cartões do visitante
            kappa_mandante: κ para escanteios do mandante
            kappa_visitante: κ para escanteios do visitante
            use_negbinomial_cards: Se True, usa NegBinomial para cartões
            
        Returns:
            SimulationResult com todas as probabilidades
        """
        n = self.n_simulations
        
        # Criar distribuições
        dist_gols_m = PoissonModel(lambda_mandante)
        dist_gols_v = PoissonModel(lambda_visitante)
        
        if use_negbinomial_cards:
            dist_cart_m = NegBinomialModel(mu_mandante, alpha=0.5)
            dist_cart_v = NegBinomialModel(mu_visitante, alpha=0.5)
        else:
            dist_cart_m = PoissonModel(mu_mandante)
            dist_cart_v = PoissonModel(mu_visitante)
        
        dist_esc_m = PoissonModel(kappa_mandante)
        dist_esc_v = PoissonModel(kappa_visitante)
        
        # Simular
        gols_m = dist_gols_m.sample(n)
        gols_v = dist_gols_v.sample(n)
        cart_m = dist_cart_m.sample(n)
        cart_v = dist_cart_v.sample(n)
        esc_m = dist_esc_m.sample(n)
        esc_v = dist_esc_v.sample(n)
        
        # Totais
        gols_total = gols_m + gols_v
        cart_total = cart_m + cart_v
        esc_total = esc_m + esc_v
        
        # Resultados
        vitorias_m = np.sum(gols_m > gols_v)
        empates = np.sum(gols_m == gols_v)
        vitorias_v = np.sum(gols_m < gols_v)
        
        # Over/Under gols
        over_15 = np.sum(gols_total > 1.5)
        over_25 = np.sum(gols_total > 2.5)
        over_35 = np.sum(gols_total > 3.5)
        under_25 = np.sum(gols_total < 2.5)
        btts = np.sum((gols_m > 0) & (gols_v > 0))
        
        # Over/Under cartões
        over_35_cart = np.sum(cart_total > 3.5)
        over_45_cart = np.sum(cart_total > 4.5)
        
        # Over/Under escanteios
        over_85_esc = np.sum(esc_total > 8.5)
        over_105_esc = np.sum(esc_total > 10.5)
        
        # Placares mais prováveis
        placares = Counter(zip(gols_m, gols_v))
        top_placares = placares.most_common(10)
        placares_list = [
            {
                'placar': f"{int(p[0])}-{int(p[1])}",
                'mandante': int(p[0]),
                'visitante': int(p[1]),
                'probabilidade': round(count / n * 100, 2)
            }
            for (p, count) in top_placares
        ]
        
        # Intervalos de confiança (percentis 10-90)
        intervalo_gols = (int(np.percentile(gols_total, 10)), int(np.percentile(gols_total, 90)))
        intervalo_cart = (int(np.percentile(cart_total, 10)), int(np.percentile(cart_total, 90)))
        intervalo_esc = (int(np.percentile(esc_total, 10)), int(np.percentile(esc_total, 90)))
        
        return SimulationResult(
            n_simulations=n,
            prob_vitoria_mandante=vitorias_m / n,
            prob_empate=empates / n,
            prob_vitoria_visitante=vitorias_v / n,
            gols_mandante_media=np.mean(gols_m),
            gols_visitante_media=np.mean(gols_v),
            gols_total_media=np.mean(gols_total),
            prob_over_15=over_15 / n,
            prob_over_25=over_25 / n,
            prob_over_35=over_35 / n,
            prob_under_25=under_25 / n,
            prob_btts=btts / n,
            placares_provaveis=placares_list,
            cartoes_mandante_media=np.mean(cart_m),
            cartoes_visitante_media=np.mean(cart_v),
            cartoes_total_media=np.mean(cart_total),
            prob_over_35_cartoes=over_35_cart / n,
            prob_over_45_cartoes=over_45_cart / n,
            escanteios_mandante_media=np.mean(esc_m),
            escanteios_visitante_media=np.mean(esc_v),
            escanteios_total_media=np.mean(esc_total),
            prob_over_85_escanteios=over_85_esc / n,
            prob_over_105_escanteios=over_105_esc / n,
            intervalo_gols_80=intervalo_gols,
            intervalo_cartoes_80=intervalo_cart,
            intervalo_escanteios_80=intervalo_esc
        )
    
    def simulate_from_params(self, params: dict) -> SimulationResult:
        """
        Simula a partir de um dict de parâmetros.
        
        Útil para integração com ParameterCalculator.
        """
        return self.simulate(
            lambda_mandante=params.get('lambda_mandante', 1.5),
            lambda_visitante=params.get('lambda_visitante', 1.0),
            mu_mandante=params.get('mu_mandante', 2.0),
            mu_visitante=params.get('mu_visitante', 2.5),
            kappa_mandante=params.get('kappa_mandante', 5.0),
            kappa_visitante=params.get('kappa_visitante', 4.0)
        )
    
    def quick_simulate(
        self,
        lambda_mandante: float,
        lambda_visitante: float
    ) -> dict:
        """
        Simulação rápida apenas para gols.
        
        Útil para testes ou quando só precisa do resultado.
        """
        n = self.n_simulations
        
        gols_m = np.random.poisson(lambda_mandante, n)
        gols_v = np.random.poisson(lambda_visitante, n)
        
        return {
            'vitoria_mandante': round(np.sum(gols_m > gols_v) / n * 100, 1),
            'empate': round(np.sum(gols_m == gols_v) / n * 100, 1),
            'vitoria_visitante': round(np.sum(gols_m < gols_v) / n * 100, 1),
            'gols_mandante': round(np.mean(gols_m), 2),
            'gols_visitante': round(np.mean(gols_v), 2),
            'over_2.5': round(np.sum(gols_m + gols_v > 2.5) / n * 100, 1)
        }
