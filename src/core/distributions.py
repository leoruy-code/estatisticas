"""
ETAPA 4 - Distribuições Estatísticas

Implementa as distribuições para gols, cartões e escanteios:
- Poisson: quando variância ≈ média
- Binomial Negativa: quando variância >> média (overdispersion)

Cada distribuição pode gerar:
- Probabilidades pontuais P(X = k)
- Probabilidades acumuladas P(X ≤ k), P(X > k)
- Amostras para Monte Carlo
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod


@dataclass
class DistributionResult:
    """Resultado de uma distribuição."""
    media: float
    variancia: float
    mediana: float
    moda: int
    
    # Probabilidades de cada valor (0, 1, 2, ...)
    probabilidades: List[float]
    
    # Intervalos de confiança
    intervalo_50: Tuple[int, int]
    intervalo_80: Tuple[int, int]
    intervalo_95: Tuple[int, int]


class BaseDistribution(ABC):
    """Classe base para distribuições."""
    
    @abstractmethod
    def pmf(self, k: int) -> float:
        """Probabilidade P(X = k)."""
        pass
    
    @abstractmethod
    def cdf(self, k: int) -> float:
        """Probabilidade acumulada P(X ≤ k)."""
        pass
    
    @abstractmethod
    def sample(self, n: int = 1) -> np.ndarray:
        """Gera n amostras da distribuição."""
        pass
    
    @abstractmethod
    def get_stats(self) -> DistributionResult:
        """Retorna estatísticas completas."""
        pass
    
    def prob_over(self, k: float) -> float:
        """P(X > k) - probabilidade de over."""
        return 1 - self.cdf(int(k))
    
    def prob_under(self, k: float) -> float:
        """P(X < k) - probabilidade de under."""
        return self.cdf(int(k) - 1) if k > 0 else 0.0
    
    def prob_exact(self, k: int) -> float:
        """P(X = k) - probabilidade exata."""
        return self.pmf(k)
    
    def prob_range(self, a: int, b: int) -> float:
        """P(a ≤ X ≤ b)."""
        return self.cdf(b) - self.cdf(a - 1) if a > 0 else self.cdf(b)


class PoissonModel(BaseDistribution):
    """
    Distribuição de Poisson.
    
    Usada quando:
    - Eventos são independentes
    - Taxa média é constante
    - Variância ≈ Média
    
    Ideal para: gols, escanteios (em geral)
    """
    
    def __init__(self, lambda_: float):
        """
        Args:
            lambda_: Taxa média de eventos (ex: 2.5 gols/jogo)
        """
        self.lambda_ = max(lambda_, 0.01)  # Evitar lambda = 0
        self._dist = stats.poisson(self.lambda_)
    
    def pmf(self, k: int) -> float:
        return self._dist.pmf(k)
    
    def cdf(self, k: int) -> float:
        return self._dist.cdf(k)
    
    def sample(self, n: int = 1) -> np.ndarray:
        return self._dist.rvs(size=n)
    
    def get_stats(self) -> DistributionResult:
        # Calcular probabilidades até valor onde acumula 99.9%
        max_k = int(self.lambda_ * 4 + 10)  # Margem segura
        probs = [self.pmf(k) for k in range(max_k + 1)]
        
        # Intervalos de confiança
        return DistributionResult(
            media=self.lambda_,
            variancia=self.lambda_,  # Na Poisson, var = média
            mediana=int(self._dist.median()),
            moda=max(0, int(self.lambda_) - 1) if self.lambda_ < 1 else int(self.lambda_),
            probabilidades=probs,
            intervalo_50=self._get_interval(0.25, 0.75),
            intervalo_80=self._get_interval(0.10, 0.90),
            intervalo_95=self._get_interval(0.025, 0.975)
        )
    
    def _get_interval(self, lower: float, upper: float) -> Tuple[int, int]:
        """Calcula intervalo de confiança."""
        return (
            int(self._dist.ppf(lower)),
            int(self._dist.ppf(upper))
        )
    
    def __repr__(self):
        return f"Poisson(λ={self.lambda_:.2f})"


class NegBinomialModel(BaseDistribution):
    """
    Distribuição Binomial Negativa.
    
    Usada quando:
    - Variância > Média (overdispersion)
    - Dados têm mais variabilidade que Poisson permite
    
    Ideal para: cartões (mais imprevisíveis)
    
    Parametrização: média (μ) e dispersão (α)
    - Variância = μ + α*μ²
    - Quando α → 0, converge para Poisson
    """
    
    def __init__(self, mu: float, alpha: float = 0.5):
        """
        Args:
            mu: Média esperada
            alpha: Parâmetro de dispersão (0 = Poisson, maior = mais disperso)
        """
        self.mu = max(mu, 0.01)
        self.alpha = max(alpha, 0.01)
        
        # Converter para parametrização scipy (n, p)
        # n = 1/alpha, p = 1/(1 + alpha*mu)
        self.n = 1 / self.alpha
        self.p = 1 / (1 + self.alpha * self.mu)
        self._dist = stats.nbinom(self.n, self.p)
    
    def pmf(self, k: int) -> float:
        return self._dist.pmf(k)
    
    def cdf(self, k: int) -> float:
        return self._dist.cdf(k)
    
    def sample(self, n: int = 1) -> np.ndarray:
        return self._dist.rvs(size=n)
    
    def get_stats(self) -> DistributionResult:
        max_k = int(self.mu * 4 + 15)
        probs = [self.pmf(k) for k in range(max_k + 1)]
        
        var = self.mu + self.alpha * self.mu ** 2
        
        return DistributionResult(
            media=self.mu,
            variancia=var,
            mediana=int(self._dist.median()),
            moda=max(0, int(self.mu) - 1) if self.mu < 1 else int(self.mu),
            probabilidades=probs,
            intervalo_50=self._get_interval(0.25, 0.75),
            intervalo_80=self._get_interval(0.10, 0.90),
            intervalo_95=self._get_interval(0.025, 0.975)
        )
    
    def _get_interval(self, lower: float, upper: float) -> Tuple[int, int]:
        return (
            int(self._dist.ppf(lower)),
            int(self._dist.ppf(upper))
        )
    
    def __repr__(self):
        return f"NegBinomial(μ={self.mu:.2f}, α={self.alpha:.2f})"


class DistributionFactory:
    """
    Factory para criar a distribuição apropriada.
    
    Decide automaticamente entre Poisson e NegBinomial
    baseado na relação variância/média.
    """
    
    THRESHOLD_OVERDISPERSION = 1.5  # var/mean > 1.5 → NegBinomial
    
    @classmethod
    def create(
        cls, 
        mean: float, 
        variance: Optional[float] = None,
        force_type: Optional[str] = None
    ) -> BaseDistribution:
        """
        Cria distribuição apropriada.
        
        Args:
            mean: Média esperada
            variance: Variância (se conhecida)
            force_type: 'poisson' ou 'negbinomial' para forçar
            
        Returns:
            Instância da distribuição apropriada
        """
        if force_type == 'poisson':
            return PoissonModel(mean)
        elif force_type == 'negbinomial':
            alpha = (variance - mean) / (mean ** 2) if variance and mean > 0 else 0.5
            return NegBinomialModel(mean, max(alpha, 0.1))
        
        # Decisão automática
        if variance is None:
            return PoissonModel(mean)
        
        ratio = variance / mean if mean > 0 else 1
        
        if ratio > cls.THRESHOLD_OVERDISPERSION:
            alpha = (variance - mean) / (mean ** 2)
            return NegBinomialModel(mean, max(alpha, 0.1))
        else:
            return PoissonModel(mean)
    
    @classmethod
    def create_for_goals(cls, lambda_: float) -> PoissonModel:
        """Cria distribuição para gols (geralmente Poisson)."""
        return PoissonModel(lambda_)
    
    @classmethod
    def create_for_cards(cls, mu: float, alpha: float = 0.5) -> NegBinomialModel:
        """Cria distribuição para cartões (geralmente NegBinomial)."""
        return NegBinomialModel(mu, alpha)
    
    @classmethod
    def create_for_corners(cls, lambda_: float) -> PoissonModel:
        """Cria distribuição para escanteios."""
        return PoissonModel(lambda_)
