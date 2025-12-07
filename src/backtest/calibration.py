"""
Sistema de Calibração de Probabilidades.

Implementa:
- Platt Scaling (Regressão Logística)
- Isotonic Regression
- Métricas de calibração (Brier Score, ECE)
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import calibration_curve
import json
from pathlib import Path


@dataclass
class CalibrationMetrics:
    """Métricas de qualidade da calibração."""
    brier_score: float  # Menor é melhor (0 = perfeito)
    brier_score_calibrated: float  # Após calibração
    ece: float  # Expected Calibration Error
    ece_calibrated: float
    n_samples: int
    improvement_pct: float  # % de melhoria


class PlattScaling:
    """
    Calibração usando Platt Scaling (Regressão Logística).
    
    prob_calibrada = sigmoid(a * prob_modelo + b)
    
    Funciona melhor quando:
    - Poucos dados (< 1000 amostras)
    - Probabilidades próximas de 50%
    - Distribuição sigmóide dos erros
    """
    
    def __init__(self):
        self.model = LogisticRegression(solver='lbfgs', max_iter=1000)
        self.is_fitted = False
    
    def fit(self, probs: np.ndarray, outcomes: np.ndarray) -> 'PlattScaling':
        """
        Treina o calibrador.
        
        Args:
            probs: Array de probabilidades previstas (0-1)
            outcomes: Array de resultados reais (0 ou 1)
        """
        if len(probs) < 10:
            raise ValueError("Precisa de pelo menos 10 amostras para calibração")
        
        # Reshape para sklearn
        X = probs.reshape(-1, 1)
        y = outcomes.astype(int)
        
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """Aplica calibração às probabilidades."""
        if not self.is_fitted:
            raise RuntimeError("Calibrador não foi treinado. Use fit() primeiro.")
        
        X = probs.reshape(-1, 1)
        return self.model.predict_proba(X)[:, 1]
    
    def calibrate_single(self, prob: float) -> float:
        """Calibra uma única probabilidade."""
        return float(self.calibrate(np.array([prob]))[0])


class IsotonicCalibrator:
    """
    Calibração usando Isotonic Regression.
    
    Não-paramétrico - não assume forma da curva.
    
    Funciona melhor quando:
    - Muitos dados (> 1000 amostras)
    - Probabilidades extremas (< 20% ou > 80%)
    - Relação não-linear entre prob_modelo e realidade
    """
    
    def __init__(self):
        self.model = IsotonicRegression(out_of_bounds='clip')
        self.is_fitted = False
    
    def fit(self, probs: np.ndarray, outcomes: np.ndarray) -> 'IsotonicCalibrator':
        """Treina o calibrador."""
        if len(probs) < 10:
            raise ValueError("Precisa de pelo menos 10 amostras para calibração")
        
        self.model.fit(probs, outcomes)
        self.is_fitted = True
        return self
    
    def calibrate(self, probs: np.ndarray) -> np.ndarray:
        """Aplica calibração às probabilidades."""
        if not self.is_fitted:
            raise RuntimeError("Calibrador não foi treinado. Use fit() primeiro.")
        
        return self.model.predict(probs)
    
    def calibrate_single(self, prob: float) -> float:
        """Calibra uma única probabilidade."""
        return float(self.calibrate(np.array([prob]))[0])


class Calibrator:
    """
    Calibrador principal que gerencia múltiplos mercados.
    
    Salva/carrega calibradores treinados para cada mercado:
    - over_25_goals
    - over_35_goals
    - btts
    - over_95_corners
    - etc.
    """
    
    def __init__(self, calibrators_path: str = 'data/calibrators.json'):
        self.path = Path(calibrators_path)
        self.calibrators: Dict[str, dict] = {}  # mercado -> {params, type}
        self._load()
    
    def _load(self):
        """Carrega calibradores salvos."""
        if self.path.exists():
            with open(self.path, 'r') as f:
                self.calibrators = json.load(f)
    
    def _save(self):
        """Salva calibradores."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(self.calibrators, f, indent=2)
    
    def train(
        self, 
        market: str, 
        probs: np.ndarray, 
        outcomes: np.ndarray,
        method: str = 'auto'
    ) -> CalibrationMetrics:
        """
        Treina calibrador para um mercado específico.
        
        Args:
            market: Nome do mercado (ex: 'over_25_goals')
            probs: Probabilidades previstas
            outcomes: Resultados reais (0 ou 1)
            method: 'platt', 'isotonic', ou 'auto' (escolhe melhor)
        
        Returns:
            Métricas de calibração
        """
        probs = np.array(probs)
        outcomes = np.array(outcomes)
        
        # Calcular métricas antes da calibração
        brier_before = self._brier_score(probs, outcomes)
        ece_before = self._ece(probs, outcomes)
        
        # Escolher método
        if method == 'auto':
            # Platt para poucos dados, Isotonic para muitos
            method = 'platt' if len(probs) < 500 else 'isotonic'
        
        # Treinar
        if method == 'platt':
            calibrator = PlattScaling()
            calibrator.fit(probs, outcomes)
            
            # Salvar parâmetros (coef_ e intercept_)
            self.calibrators[market] = {
                'type': 'platt',
                'coef': float(calibrator.model.coef_[0][0]),
                'intercept': float(calibrator.model.intercept_[0])
            }
        else:
            calibrator = IsotonicCalibrator()
            calibrator.fit(probs, outcomes)
            
            # Salvar pontos da curva isotônica
            self.calibrators[market] = {
                'type': 'isotonic',
                'x': calibrator.model.X_thresholds_.tolist(),
                'y': calibrator.model.y_thresholds_.tolist()
            }
        
        self._save()
        
        # Calcular métricas após calibração
        probs_calibrated = calibrator.calibrate(probs)
        brier_after = self._brier_score(probs_calibrated, outcomes)
        ece_after = self._ece(probs_calibrated, outcomes)
        
        improvement = ((brier_before - brier_after) / brier_before * 100) if brier_before > 0 else 0
        
        return CalibrationMetrics(
            brier_score=brier_before,
            brier_score_calibrated=brier_after,
            ece=ece_before,
            ece_calibrated=ece_after,
            n_samples=len(probs),
            improvement_pct=improvement
        )
    
    def calibrate(self, market: str, prob: float) -> float:
        """
        Aplica calibração a uma probabilidade.
        
        Args:
            market: Nome do mercado
            prob: Probabilidade do modelo (0-1)
        
        Returns:
            Probabilidade calibrada
        """
        if market not in self.calibrators:
            return prob  # Sem calibrador, retorna original
        
        cal = self.calibrators[market]
        
        if cal['type'] == 'platt':
            # sigmoid(coef * prob + intercept)
            z = cal['coef'] * prob + cal['intercept']
            return 1 / (1 + np.exp(-z))
        
        elif cal['type'] == 'isotonic':
            # Interpolação linear na curva isotônica
            x_vals = np.array(cal['x'])
            y_vals = np.array(cal['y'])
            return float(np.interp(prob, x_vals, y_vals))
        
        return prob
    
    def calibrate_prediction(self, prediction: dict) -> dict:
        """
        Calibra todas as probabilidades de uma previsão.
        
        Args:
            prediction: Dict com probabilidades (prob_over_25_goals, etc.)
        
        Returns:
            Dict com probabilidades calibradas
        """
        result = prediction.copy()
        
        # Mapeamento de campos para mercados
        mappings = {
            'prob_over_25_goals': 'over_25_goals',
            'prob_over_35_goals': 'over_35_goals',
            'prob_over_15_goals': 'over_15_goals',
            'prob_btts': 'btts',
            'prob_over_95_corners': 'over_95_corners',
            'prob_over_105_corners': 'over_105_corners',
            'prob_home_win': 'home_win',
            'prob_draw': 'draw',
            'prob_away_win': 'away_win',
        }
        
        for field, market in mappings.items():
            if field in result and market in self.calibrators:
                result[field] = self.calibrate(market, result[field])
        
        return result
    
    def get_status(self) -> Dict[str, dict]:
        """Retorna status de todos os calibradores."""
        return {
            market: {
                'type': cal['type'],
                'trained': True
            }
            for market, cal in self.calibrators.items()
        }
    
    @staticmethod
    def _brier_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
        """Calcula Brier Score."""
        return float(np.mean((probs - outcomes) ** 2))
    
    @staticmethod
    def _ece(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
        """
        Expected Calibration Error.
        Mede quão bem as probabilidades estão calibradas em diferentes faixas.
        """
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        
        for i in range(n_bins):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
            if mask.sum() > 0:
                bin_prob = probs[mask].mean()
                bin_outcome = outcomes[mask].mean()
                ece += mask.sum() * abs(bin_prob - bin_outcome)
        
        return ece / len(probs) if len(probs) > 0 else 0.0


def plot_calibration_curve(probs: np.ndarray, outcomes: np.ndarray, title: str = "Calibration Curve"):
    """
    Gera dados para curva de calibração (para uso no Streamlit).
    
    Returns:
        Dict com dados para plotagem
    """
    prob_true, prob_pred = calibration_curve(outcomes, probs, n_bins=10, strategy='uniform')
    
    return {
        'prob_pred': prob_pred.tolist(),
        'prob_true': prob_true.tolist(),
        'title': title,
        'brier_score': float(np.mean((probs - outcomes) ** 2))
    }
