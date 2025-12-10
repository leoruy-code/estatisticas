"""
ETAPA 10 - Calibração do Modelo

Verifica se as probabilidades são realistas:
- Quando prevemos 60% de vitória, o time ganha em ~60% dos casos?
- Os gols esperados batem com a realidade?

Se não, ajustamos os parâmetros.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import defaultdict

from src.analysis.predictions import MatchPredictor


@dataclass
class CalibrationResult:
    """Resultado da calibração."""
    
    # Calibração de probabilidades
    # Para cada faixa (0-10%, 10-20%, ...), qual foi a frequência real?
    calibration_curve: Dict[str, float]
    
    # Erro médio (Brier Score)
    brier_score: float
    
    # Erro nos gols
    mae_gols: float  # Mean Absolute Error
    rmse_gols: float  # Root Mean Square Error
    
    # Viés
    vies_gols: float  # Positivo = superestima, Negativo = subestima
    
    # Número de jogos analisados
    n_jogos: int
    
    # Está bem calibrado?
    bem_calibrado: bool
    
    def to_dict(self) -> dict:
        return {
            'calibration_curve': self.calibration_curve,
            'brier_score': round(self.brier_score, 4),
            'mae_gols': round(self.mae_gols, 2),
            'rmse_gols': round(self.rmse_gols, 2),
            'vies_gols': round(self.vies_gols, 2),
            'n_jogos': self.n_jogos,
            'bem_calibrado': self.bem_calibrado,
            'avaliacao': self._avaliar()
        }
    
    def _avaliar(self) -> str:
        if self.brier_score < 0.20:
            return "Excelente"
        elif self.brier_score < 0.25:
            return "Bom"
        elif self.brier_score < 0.30:
            return "Razoável"
        else:
            return "Precisa melhorar"


class ModelCalibrator:
    """
    Calibrador do modelo.
    
    Compara previsões com resultados reais e sugere ajustes.
    """
    
    def __init__(self, db_config: dict, predictor: MatchPredictor):
        self.db_config = db_config
        self.predictor = predictor
    
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def calibrate(
        self,
        league_id: int,
        temporada: str = "2025",
        min_jogos: int = 50
    ) -> CalibrationResult:
        """
        Executa calibração em jogos passados.
        
        Args:
            league_id: ID da liga
            temporada: Temporada a analisar
            min_jogos: Mínimo de jogos para análise confiável
            
        Returns:
            CalibrationResult com métricas de calibração
        """
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar jogos finalizados
        cursor.execute("""
            SELECT 
                m.id,
                m.home_team_id AS mandante_id,
                m.away_team_id AS visitante_id,
                m.home_goals    AS gols_mandante,
                m.away_goals    AS gols_visitante
            FROM matches m
            JOIN teams t ON m.home_team_id = t.id
            WHERE t.league_id = %s
              AND m.status = 'finished'
              AND m.home_goals IS NOT NULL
            ORDER BY m.data DESC
            LIMIT 200
        """, (league_id,))
        
        jogos = cursor.fetchall()
        conn.close()
        
        if len(jogos) < min_jogos:
            return self._resultado_insuficiente(len(jogos))
        
        # Analisar cada jogo
        predictions = []
        actuals = []
        gols_previstos = []
        gols_reais = []
        
        for jogo in jogos:
            try:
                # Fazer previsão
                pred = self.predictor.predict_quick(
                    jogo['mandante_id'],
                    jogo['visitante_id'],
                    league_id
                )
                
                # Resultado real
                gols_m = jogo['gols_mandante']
                gols_v = jogo['gols_visitante']
                
                if gols_m > gols_v:
                    resultado_real = 'mandante'
                elif gols_m < gols_v:
                    resultado_real = 'visitante'
                else:
                    resultado_real = 'empate'
                
                predictions.append({
                    'mandante': pred['vitoria_mandante'] / 100,
                    'empate': pred['empate'] / 100,
                    'visitante': pred['vitoria_visitante'] / 100,
                    'resultado_real': resultado_real
                })
                
                gols_previstos.append(pred['gols_mandante'] + pred['gols_visitante'])
                gols_reais.append(gols_m + gols_v)
                
            except Exception as e:
                continue
        
        if not predictions:
            return self._resultado_insuficiente(0)
        
        # Calcular métricas
        brier = self._calculate_brier_score(predictions)
        calibration = self._calculate_calibration_curve(predictions)
        mae, rmse, vies = self._calculate_goals_error(gols_previstos, gols_reais)
        
        bem_calibrado = brier < 0.25 and abs(vies) < 0.3
        
        return CalibrationResult(
            calibration_curve=calibration,
            brier_score=brier,
            mae_gols=mae,
            rmse_gols=rmse,
            vies_gols=vies,
            n_jogos=len(predictions),
            bem_calibrado=bem_calibrado
        )
    
    def _calculate_brier_score(self, predictions: List[Dict]) -> float:
        """
        Calcula Brier Score.
        
        Menor = melhor. 0 = perfeito, 0.25 = chute aleatório.
        """
        scores = []
        
        for pred in predictions:
            real = pred['resultado_real']
            
            # Probabilidade atribuída ao resultado correto
            if real == 'mandante':
                p_correct = pred['mandante']
            elif real == 'visitante':
                p_correct = pred['visitante']
            else:
                p_correct = pred['empate']
            
            # Brier = (1 - p_correct)²
            scores.append((1 - p_correct) ** 2)
        
        return np.mean(scores)
    
    def _calculate_calibration_curve(self, predictions: List[Dict]) -> Dict[str, float]:
        """
        Calcula curva de calibração.
        
        Para cada faixa de probabilidade prevista, qual foi a frequência real?
        """
        # Agrupar por faixas de 10%
        faixas = defaultdict(list)
        
        for pred in predictions:
            real = pred['resultado_real']
            
            for outcome in ['mandante', 'empate', 'visitante']:
                prob = pred[outcome]
                faixa = f"{int(prob * 10) * 10}-{int(prob * 10) * 10 + 10}%"
                
                # 1 se acertou, 0 se errou
                acertou = 1 if real == outcome else 0
                faixas[faixa].append((prob, acertou))
        
        # Calcular frequência real por faixa
        calibration = {}
        for faixa, valores in sorted(faixas.items()):
            if valores:
                prob_media = np.mean([v[0] for v in valores])
                freq_real = np.mean([v[1] for v in valores])
                calibration[faixa] = {
                    'prob_prevista': round(prob_media * 100, 1),
                    'freq_real': round(freq_real * 100, 1),
                    'n': len(valores)
                }
        
        return calibration
    
    def _calculate_goals_error(
        self, 
        previstos: List[float], 
        reais: List[float]
    ) -> Tuple[float, float, float]:
        """
        Calcula erro nos gols.
        
        Returns:
            (MAE, RMSE, viés)
        """
        previstos = np.array(previstos)
        reais = np.array(reais)
        
        errors = previstos - reais
        
        mae = np.mean(np.abs(errors))
        rmse = np.sqrt(np.mean(errors ** 2))
        vies = np.mean(errors)
        
        return mae, rmse, vies
    
    def _resultado_insuficiente(self, n: int) -> CalibrationResult:
        """Retorna quando não há jogos suficientes."""
        return CalibrationResult(
            calibration_curve={},
            brier_score=0.0,
            mae_gols=0.0,
            rmse_gols=0.0,
            vies_gols=0.0,
            n_jogos=n,
            bem_calibrado=False
        )
    
    def suggest_adjustments(self, calibration: CalibrationResult) -> Dict:
        """
        Sugere ajustes nos parâmetros baseado na calibração.
        """
        suggestions = []
        
        # Analisar viés nos gols
        if calibration.vies_gols > 0.3:
            suggestions.append({
                'parametro': 'lambda',
                'acao': 'reduzir',
                'motivo': f'Superestimando gols em {calibration.vies_gols:.2f} por jogo'
            })
        elif calibration.vies_gols < -0.3:
            suggestions.append({
                'parametro': 'lambda',
                'acao': 'aumentar',
                'motivo': f'Subestimando gols em {abs(calibration.vies_gols):.2f} por jogo'
            })
        
        # Analisar Brier Score
        if calibration.brier_score > 0.30:
            suggestions.append({
                'parametro': 'modelo',
                'acao': 'revisar',
                'motivo': 'Brier Score alto, probabilidades imprecisas'
            })
        
        return {
            'calibracao_atual': calibration.to_dict(),
            'sugestoes': suggestions,
            'acao_recomendada': suggestions[0] if suggestions else None
        }
    
    def save_calibration(self, calibration: CalibrationResult, league_id: int):
        """Salva resultado da calibração no banco."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO calibration_data 
            (league_id, brier_score, mae_gols, vies_gols, n_jogos, data_calibracao)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (league_id) 
            DO UPDATE SET 
                brier_score = EXCLUDED.brier_score,
                mae_gols = EXCLUDED.mae_gols,
                vies_gols = EXCLUDED.vies_gols,
                n_jogos = EXCLUDED.n_jogos,
                data_calibracao = NOW()
        """, (
            league_id,
            calibration.brier_score,
            calibration.mae_gols,
            calibration.vies_gols,
            calibration.n_jogos
        ))
        
        conn.commit()
        conn.close()
