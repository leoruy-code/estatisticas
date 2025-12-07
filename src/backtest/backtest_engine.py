"""
Engine de Backtest para validar o modelo Poisson.

Funcionalidades:
- Buscar partidas históricas
- Gerar previsões para cada partida
- Comparar com resultados reais
- Calcular métricas de performance
- Treinar calibradores
"""

import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_times import TIMES_BRASILEIRAO, BRASILEIRAO_TOURNAMENT_ID

BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 1.5
MAX_DELAY = 2.5
TIMEOUT = 25

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


@dataclass
class HistoricalMatch:
    """Dados de uma partida histórica."""
    event_id: int
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total_goals: int
    total_corners: int
    home_corners: int
    away_corners: int
    
    # Resultados binários para calibração
    over_05_goals: bool
    over_15_goals: bool
    over_25_goals: bool
    over_35_goals: bool
    btts: bool
    over_85_corners: bool
    over_95_corners: bool
    over_105_corners: bool
    home_win: bool
    draw: bool
    away_win: bool


@dataclass
class BacktestResult:
    """Resultado de um backtest."""
    market: str
    predictions: List[float]  # Probabilidades previstas
    outcomes: List[int]  # Resultados reais (0 ou 1)
    brier_score: float
    accuracy: float  # % de acertos quando prob > 0.5
    n_samples: int
    
    # Análise por faixa de probabilidade
    bins_analysis: Dict[str, dict]


class BacktestEngine:
    """Engine principal de backtest."""
    
    def __init__(self, data_path: str = 'data/backtest_matches.json'):
        self.data_path = Path(data_path)
        self.matches: List[HistoricalMatch] = []
        self._load_matches()
    
    def _load_matches(self):
        """Carrega partidas históricas salvas."""
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.matches = [HistoricalMatch(**m) for m in data]
    
    def _save_matches(self):
        """Salva partidas históricas."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(m) for m in self.matches], f, indent=2, ensure_ascii=False)
    
    def _headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
        }
    
    def _delay(self):
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    def fetch_historical_matches(self, n_rounds: int = 10) -> int:
        """
        Busca partidas históricas do Brasileirão.
        
        Args:
            n_rounds: Número de rodadas passadas para buscar
        
        Returns:
            Número de partidas adicionadas
        """
        print(f"🔍 Buscando partidas históricas do Brasileirão...")
        
        added = 0
        existing_ids = {m.event_id for m in self.matches}
        
        # Buscar partidas de cada time
        for nome, team_id in TIMES_BRASILEIRAO.items():
            print(f"  📥 {nome}...")
            self._delay()
            
            try:
                url = f"{BASE_URL}/team/{team_id}/events/last/0"
                r = requests.get(url, headers=self._headers(), timeout=TIMEOUT)
                
                if r.status_code != 200:
                    continue
                
                events = r.json().get('events', [])
                
                for ev in events:
                    # Filtrar apenas Brasileirão e partidas finalizadas
                    tournament = ev.get('tournament', {}).get('uniqueTournament', {})
                    if tournament.get('id') != BRASILEIRAO_TOURNAMENT_ID:
                        continue
                    if ev.get('status', {}).get('type') != 'finished':
                        continue
                    
                    event_id = ev.get('id')
                    if event_id in existing_ids:
                        continue
                    
                    # Extrair dados básicos
                    home_team = ev.get('homeTeam', {}).get('name', '')
                    away_team = ev.get('awayTeam', {}).get('name', '')
                    home_score = ev.get('homeScore', {}).get('current', 0) or 0
                    away_score = ev.get('awayScore', {}).get('current', 0) or 0
                    
                    # Buscar estatísticas (escanteios)
                    corners = self._fetch_corners(event_id)
                    home_corners = corners.get('home', 0)
                    away_corners = corners.get('away', 0)
                    total_corners = home_corners + away_corners
                    
                    total_goals = home_score + away_score
                    
                    # Criar registro
                    match = HistoricalMatch(
                        event_id=event_id,
                        date=datetime.fromtimestamp(ev.get('startTimestamp', 0)).strftime('%Y-%m-%d'),
                        home_team=home_team,
                        away_team=away_team,
                        home_score=home_score,
                        away_score=away_score,
                        total_goals=total_goals,
                        total_corners=total_corners,
                        home_corners=home_corners,
                        away_corners=away_corners,
                        over_05_goals=total_goals > 0,
                        over_15_goals=total_goals > 1,
                        over_25_goals=total_goals > 2,
                        over_35_goals=total_goals > 3,
                        btts=home_score > 0 and away_score > 0,
                        over_85_corners=total_corners > 8,
                        over_95_corners=total_corners > 9,
                        over_105_corners=total_corners > 10,
                        home_win=home_score > away_score,
                        draw=home_score == away_score,
                        away_win=home_score < away_score,
                    )
                    
                    self.matches.append(match)
                    existing_ids.add(event_id)
                    added += 1
                    
                    print(f"    ✅ {home_team} {home_score}-{away_score} {away_team} | ⚽{total_goals} 🚩{total_corners}")
                    
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                continue
        
        self._save_matches()
        print(f"\n✅ Total: {added} partidas adicionadas. Base: {len(self.matches)} partidas.")
        return added
    
    def _fetch_corners(self, event_id: int) -> Dict[str, int]:
        """Busca estatísticas de escanteios de uma partida."""
        self._delay()
        
        try:
            url = f"{BASE_URL}/event/{event_id}/statistics"
            r = requests.get(url, headers=self._headers(), timeout=TIMEOUT)
            
            if r.status_code != 200:
                return {'home': 0, 'away': 0}
            
            data = r.json()
            
            for period in data.get('statistics', []):
                if period.get('period') == 'ALL':
                    for group in period.get('groups', []):
                        for item in group.get('statisticsItems', []):
                            if 'corner' in item.get('name', '').lower():
                                home = int(item.get('home', 0) or 0)
                                away = int(item.get('away', 0) or 0)
                                return {'home': home, 'away': away}
            
            return {'home': 0, 'away': 0}
            
        except:
            return {'home': 0, 'away': 0}
    
    def run_backtest(self, analyzer) -> Dict[str, BacktestResult]:
        """
        Executa backtest completo.
        
        Args:
            analyzer: Instância de PoissonAnalyzer
        
        Returns:
            Dict com resultados por mercado
        """
        if not self.matches:
            print("⚠️ Nenhuma partida histórica. Execute fetch_historical_matches() primeiro.")
            return {}
        
        print(f"🔬 Executando backtest em {len(self.matches)} partidas...")
        
        results = {
            'over_25_goals': {'preds': [], 'outcomes': []},
            'over_35_goals': {'preds': [], 'outcomes': []},
            'btts': {'preds': [], 'outcomes': []},
            'over_95_corners': {'preds': [], 'outcomes': []},
            'over_105_corners': {'preds': [], 'outcomes': []},
            'home_win': {'preds': [], 'outcomes': []},
        }
        
        for match in self.matches:
            # Verificar se temos dados dos times
            if match.home_team not in analyzer.times_stats or match.away_team not in analyzer.times_stats:
                continue
            
            # Gerar previsão
            pred = analyzer.prever_partida(match.home_team, match.away_team)
            if not pred:
                continue
            
            # Coletar resultados
            results['over_25_goals']['preds'].append(pred.prob_over_25_goals)
            results['over_25_goals']['outcomes'].append(int(match.over_25_goals))
            
            results['over_35_goals']['preds'].append(pred.prob_over_35_goals)
            results['over_35_goals']['outcomes'].append(int(match.over_35_goals))
            
            results['btts']['preds'].append(pred.prob_btts)
            results['btts']['outcomes'].append(int(match.btts))
            
            results['over_95_corners']['preds'].append(pred.prob_over_95_corners)
            results['over_95_corners']['outcomes'].append(int(match.over_95_corners))
            
            results['over_105_corners']['preds'].append(pred.prob_over_105_corners)
            results['over_105_corners']['outcomes'].append(int(match.over_105_corners))
            
            results['home_win']['preds'].append(pred.prob_home_win)
            results['home_win']['outcomes'].append(int(match.home_win))
        
        # Calcular métricas por mercado
        backtest_results = {}
        
        for market, data in results.items():
            if not data['preds']:
                continue
            
            preds = np.array(data['preds'])
            outcomes = np.array(data['outcomes'])
            
            brier = float(np.mean((preds - outcomes) ** 2))
            
            # Accuracy: quando prob > 0.5, prevemos "sim"
            predicted = (preds > 0.5).astype(int)
            accuracy = float(np.mean(predicted == outcomes))
            
            # Análise por faixa
            bins_analysis = self._analyze_bins(preds, outcomes)
            
            backtest_results[market] = BacktestResult(
                market=market,
                predictions=preds.tolist(),
                outcomes=outcomes.tolist(),
                brier_score=brier,
                accuracy=accuracy,
                n_samples=len(preds),
                bins_analysis=bins_analysis
            )
            
            print(f"  📊 {market}: Brier={brier:.4f}, Accuracy={accuracy*100:.1f}%, N={len(preds)}")
        
        return backtest_results
    
    def _analyze_bins(self, preds: np.ndarray, outcomes: np.ndarray) -> Dict[str, dict]:
        """Analisa performance por faixa de probabilidade."""
        bins = {
            '0-20%': (0.0, 0.2),
            '20-40%': (0.2, 0.4),
            '40-60%': (0.4, 0.6),
            '60-80%': (0.6, 0.8),
            '80-100%': (0.8, 1.0),
        }
        
        analysis = {}
        for name, (low, high) in bins.items():
            mask = (preds >= low) & (preds < high)
            if mask.sum() > 0:
                actual_rate = outcomes[mask].mean()
                expected_rate = preds[mask].mean()
                analysis[name] = {
                    'n': int(mask.sum()),
                    'expected': float(expected_rate),
                    'actual': float(actual_rate),
                    'diff': float(actual_rate - expected_rate),
                }
        
        return analysis
    
    def train_calibrators(self, backtest_results: Dict[str, BacktestResult]) -> Dict[str, dict]:
        """
        Treina calibradores para todos os mercados.
        
        Args:
            backtest_results: Resultados do backtest
        
        Returns:
            Métricas de calibração por mercado
        """
        from .calibration import Calibrator
        
        calibrator = Calibrator()
        metrics = {}
        
        print("\n🎯 Treinando calibradores...")
        
        for market, result in backtest_results.items():
            if result.n_samples < 20:
                print(f"  ⚠️ {market}: Poucos dados ({result.n_samples}), pulando...")
                continue
            
            preds = np.array(result.predictions)
            outcomes = np.array(result.outcomes)
            
            cal_metrics = calibrator.train(market, preds, outcomes)
            metrics[market] = {
                'brier_before': cal_metrics.brier_score,
                'brier_after': cal_metrics.brier_score_calibrated,
                'improvement': cal_metrics.improvement_pct,
                'n_samples': cal_metrics.n_samples,
            }
            
            print(f"  ✅ {market}: Brier {cal_metrics.brier_score:.4f} → {cal_metrics.brier_score_calibrated:.4f} ({cal_metrics.improvement_pct:+.1f}%)")
        
        return metrics
    
    def get_summary(self) -> dict:
        """Retorna resumo da base de dados."""
        if not self.matches:
            return {'n_matches': 0}
        
        return {
            'n_matches': len(self.matches),
            'date_range': {
                'first': min(m.date for m in self.matches),
                'last': max(m.date for m in self.matches),
            },
            'avg_goals': np.mean([m.total_goals for m in self.matches]),
            'avg_corners': np.mean([m.total_corners for m in self.matches]),
            'over_25_rate': np.mean([m.over_25_goals for m in self.matches]),
            'btts_rate': np.mean([m.btts for m in self.matches]),
        }


if __name__ == '__main__':
    # Teste
    engine = BacktestEngine()
    
    print("📊 Status da base:")
    print(engine.get_summary())
    
    if len(engine.matches) < 50:
        print("\n🔄 Buscando mais partidas...")
        engine.fetch_historical_matches()
