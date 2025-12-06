"""
Motor de Análise Poisson para Apostas Esportivas
Baseado em metodologia profissional de casas de apostas.

Funcionalidades:
- Cálculo de Attack/Defense Strength por time
- Estimativa de λ (lambda) para eventos (gols, chutes, escanteios, faltas)
- Distribuição Poisson e Negative Binomial
- Probabilidades Over/Under
- Multiplicadores contextuais (casa/fora, forma, etc.)
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
import numpy as np


# ==================== CONFIGURAÇÕES ====================

# Multiplicadores contextuais (valores iniciais — ajustar por backtest)
HOME_ADVANTAGE = 1.08        # 8% mais produção ofensiva em casa
FORM_WEIGHT = 0.2            # Peso da forma recente no ajuste
FORM_CLIP = (0.8, 1.2)       # Limites do multiplicador de forma

# Pesos para combinar ML + Regras (quando ML disponível)
W_ML = 0.7
W_RULE = 0.3

# Threshold para escolher distribuição
OVERDISPERSION_THRESHOLD = 1.2  # Se var/mean > 1.2, usar NegBin


# ==================== DATA CLASSES ====================

@dataclass
class TeamStats:
    """Estatísticas agregadas de um time."""
    nome: str
    total_jogadores: int
    total_partidas: int
    total_gols: int
    total_assistencias: int
    total_chutes: int
    total_chutes_gol: int
    total_faltas: int
    total_desarmes: int
    
    # Médias por partida (calculadas)
    gols_por_partida: float = 0.0
    chutes_por_partida: float = 0.0
    chutes_gol_por_partida: float = 0.0
    faltas_por_partida: float = 0.0
    
    # Força ofensiva/defensiva
    attack_strength: float = 1.0
    defense_weakness: float = 1.0
    
    # Escanteios (novos campos)
    escanteios_media: float = 0.0
    escanteios_casa_media: float = 0.0
    escanteios_fora_media: float = 0.0
    
    def calcular_medias(self, partidas_estimadas: int = None):
        """Calcula médias por partida."""
        p = partidas_estimadas or max(self.total_partidas // self.total_jogadores, 1)
        self.gols_por_partida = self.total_gols / p if p > 0 else 0
        self.chutes_por_partida = self.total_chutes / p if p > 0 else 0
        self.chutes_gol_por_partida = self.total_chutes_gol / p if p > 0 else 0
        self.faltas_por_partida = self.total_faltas / p if p > 0 else 0


@dataclass
class MatchPrediction:
    """Previsão para uma partida."""
    home_team: str
    away_team: str
    
    # Lambdas estimados
    lambda_home_goals: float
    lambda_away_goals: float
    lambda_total_goals: float
    lambda_total_shots: float
    lambda_total_corners: float
    lambda_total_fouls: float
    
    # Lambdas de escanteios por time
    lambda_home_corners: float = 0.0
    lambda_away_corners: float = 0.0
    
    # Probabilidades Gols
    prob_over_05_goals: float = 0.0
    prob_over_15_goals: float = 0.0
    prob_over_25_goals: float = 0.0
    prob_over_35_goals: float = 0.0
    
    # Probabilidades Escanteios
    prob_over_85_corners: float = 0.0
    prob_over_95_corners: float = 0.0
    prob_over_105_corners: float = 0.0
    prob_over_115_corners: float = 0.0
    
    prob_btts: float = 0.0  # Both Teams To Score
    
    # Odds justas (sem margem)
    odds_over_25: float = 0.0
    odds_under_25: float = 0.0


# ==================== FUNÇÕES POISSON ====================

def poisson_pmf(k: int, lamb: float) -> float:
    """Probabilidade de exatamente k eventos com média lambda."""
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lamb) * (lamb ** k) / math.factorial(k)


def poisson_cdf(k: int, lamb: float) -> float:
    """Probabilidade acumulada P(X <= k)."""
    return sum(poisson_pmf(i, lamb) for i in range(k + 1))


def prob_over(lamb: float, threshold: float) -> float:
    """Probabilidade de Over X.5 (mais que threshold eventos)."""
    k = int(threshold)
    return 1 - poisson_cdf(k, lamb)


def prob_under(lamb: float, threshold: float) -> float:
    """Probabilidade de Under X.5."""
    k = int(threshold)
    return poisson_cdf(k, lamb)


def prob_exact(lamb: float, k: int) -> float:
    """Probabilidade de exatamente k eventos."""
    return poisson_pmf(k, lamb)


def choose_distribution(data: List[float]) -> str:
    """Escolhe entre Poisson e Negative Binomial baseado em overdispersion."""
    if len(data) < 2:
        return "poisson"
    mean = np.mean(data)
    var = np.var(data)
    if mean == 0:
        return "poisson"
    if var / mean > OVERDISPERSION_THRESHOLD:
        return "negbin"
    return "poisson"


def negbin_prob_over(mean: float, var: float, threshold: float) -> float:
    """Probabilidade Over usando Negative Binomial."""
    if var <= mean:
        return prob_over(mean, threshold)
    
    # Parâmetros NegBin: r (n) e p
    # mean = r(1-p)/p, var = r(1-p)/p^2
    # p = mean/var, r = mean^2 / (var - mean)
    p = mean / var
    r = (mean ** 2) / (var - mean)
    
    k = int(threshold)
    return 1 - stats.nbinom.cdf(k, r, p)


# ==================== CÁLCULO DE FORÇA ====================

def calcular_league_averages(times_stats: List[TeamStats]) -> Dict[str, float]:
    """Calcula médias da liga para normalização."""
    # Usar médias por partida de cada time, depois tirar média geral
    times_ativos = [t for t in times_stats if t.gols_por_partida > 0]
    n_times = len(times_ativos) if times_ativos else 1
    
    avg_goals = sum(t.gols_por_partida for t in times_ativos) / n_times if times_ativos else 1.3
    avg_shots = sum(t.chutes_por_partida for t in times_ativos) / n_times if times_ativos else 12
    avg_fouls = sum(t.faltas_por_partida for t in times_ativos) / n_times if times_ativos else 14
    
    return {
        'avg_goals_per_match': avg_goals,
        'avg_shots_per_match': avg_shots,
        'avg_fouls_per_match': avg_fouls,
        'avg_corners_per_match': 5.0,  # ~5 escanteios por time por jogo (média típica)
    }


def calcular_attack_strength(team: TeamStats, league_avg_goals: float) -> float:
    """
    Attack Strength = Team Goals / League Average Goals
    Valores > 1 indicam ataque acima da média.
    """
    if league_avg_goals == 0:
        return 1.0
    return team.gols_por_partida / league_avg_goals


def calcular_defense_weakness(team: TeamStats, league_avg_goals: float, gols_sofridos: float = None) -> float:
    """
    Defense Weakness = Team Goals Conceded / League Average Goals
    Valores > 1 indicam defesa fraca (sofre mais gols).
    
    Nota: Sem dados de gols sofridos, usamos inverso da força ofensiva como proxy.
    """
    if gols_sofridos is not None and league_avg_goals > 0:
        return gols_sofridos / league_avg_goals
    # Proxy: times que marcam muito geralmente sofrem menos (correlação inversa)
    # Mas isso é aproximação — idealmente ter dados de gols sofridos
    return 1.0  # Default neutro


# ==================== ESTIMATIVA DE LAMBDA ====================

def estimar_lambda_gols(
    home_team: TeamStats,
    away_team: TeamStats,
    league_avg: float,
    home_advantage: float = HOME_ADVANTAGE
) -> Tuple[float, float]:
    """
    Estima λ para gols de cada time usando modelo multiplicativo.
    
    λ_home = league_avg * attack_home * defense_weakness_away * home_mult
    λ_away = league_avg * attack_away * defense_weakness_home
    """
    lambda_home = (
        league_avg 
        * home_team.attack_strength 
        * away_team.defense_weakness 
        * home_advantage
    )
    
    lambda_away = (
        league_avg 
        * away_team.attack_strength 
        * home_team.defense_weakness
    )
    
    return lambda_home, lambda_away


def estimar_lambda_chutes(
    home_team: TeamStats,
    away_team: TeamStats,
    league_avg_shots: float,
    home_advantage: float = HOME_ADVANTAGE
) -> float:
    """Estima λ total de chutes na partida."""
    # Média simples ajustada
    lambda_home = home_team.chutes_por_partida * home_advantage
    lambda_away = away_team.chutes_por_partida
    return lambda_home + lambda_away


def estimar_lambda_escanteios(
    home_team: TeamStats,
    away_team: TeamStats,
    league_avg_corners: float = 10.5
) -> float:
    """
    Estima λ total de escanteios.
    Sem dados diretos, usamos proxy baseado em chutes (mais chutes = mais escanteios).
    """
    # Correlação aproximada: escanteios ~ 0.8 * chutes_bloqueados
    # Proxy: usar média da liga ajustada por força ofensiva
    attack_factor = (home_team.attack_strength + away_team.attack_strength) / 2
    return league_avg_corners * attack_factor


def estimar_lambda_faltas(
    home_team: TeamStats,
    away_team: TeamStats,
    league_avg_fouls: float
) -> float:
    """Estima λ total de faltas na partida."""
    lambda_home = home_team.faltas_por_partida
    lambda_away = away_team.faltas_por_partida
    return lambda_home + lambda_away


# ==================== PROBABILIDADES COMPOSTAS ====================

def calcular_prob_btts(lambda_home: float, lambda_away: float) -> float:
    """
    Both Teams To Score (BTTS).
    P(BTTS) = P(home >= 1) * P(away >= 1)
    """
    prob_home_scores = 1 - poisson_pmf(0, lambda_home)
    prob_away_scores = 1 - poisson_pmf(0, lambda_away)
    return prob_home_scores * prob_away_scores


def calcular_resultado_exato(
    lambda_home: float, 
    lambda_away: float, 
    max_goals: int = 6
) -> Dict[str, float]:
    """
    Calcula probabilidades de cada placar exato.
    Retorna dict com chave "X-Y" e valor probabilidade.
    """
    resultados = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = poisson_pmf(h, lambda_home) * poisson_pmf(a, lambda_away)
            resultados[f"{h}-{a}"] = prob
    return resultados


def calcular_1x2(lambda_home: float, lambda_away: float, max_goals: int = 8) -> Dict[str, float]:
    """
    Calcula probabilidades 1X2 (vitória casa, empate, vitória fora).
    """
    prob_home = 0.0
    prob_draw = 0.0
    prob_away = 0.0
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = poisson_pmf(h, lambda_home) * poisson_pmf(a, lambda_away)
            if h > a:
                prob_home += prob
            elif h == a:
                prob_draw += prob
            else:
                prob_away += prob
    
    return {
        'home': prob_home,
        'draw': prob_draw,
        'away': prob_away
    }


# ==================== CONVERSÃO PARA ODDS ====================

def prob_to_odds(prob: float) -> float:
    """Converte probabilidade para odd decimal justa."""
    if prob <= 0:
        return float('inf')
    return 1 / prob


def aplicar_margem(odds_dict: Dict[str, float], margem: float = 0.05) -> Dict[str, float]:
    """
    Aplica margem (vig) da casa às odds.
    Margem de 5% reduz odds proporcionalmente.
    """
    # Converter para probabilidades
    probs = {k: 1/v for k, v in odds_dict.items() if v > 0}
    total_prob = sum(probs.values())
    
    # Ajustar para incluir margem
    target_total = 1 + margem
    factor = target_total / total_prob if total_prob > 0 else 1
    
    # Reconverter para odds ajustadas
    return {k: 1/(p * factor) for k, p in probs.items()}


# ==================== CLASSE PRINCIPAL ====================

class PoissonAnalyzer:
    """Analisador principal usando distribuição Poisson."""
    
    def __init__(self, jogadores_path: str = 'data/jogadores.json', times_path: str = 'data/times.json'):
        self.jogadores = self._load_json(jogadores_path)
        self.times_data = self._load_json(times_path)
        self.times_stats: Dict[str, TeamStats] = {}
        self.times_metricas: Dict[str, Dict] = {}  # Dados de partidas reais
        self.league_averages: Dict[str, float] = {}
        
        self._carregar_metricas_times()
        self._calcular_stats_times()
        self._calcular_forcas()
    
    def _load_json(self, path: str) -> List[Dict]:
        p = Path(path)
        if not p.exists():
            return []
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _carregar_metricas_times(self):
        """Carrega métricas de partidas reais do times.json."""
        for time_data in self.times_data:
            nome = time_data.get('nome')
            if nome:
                self.times_metricas[nome] = {
                    'gols_marcados_media': time_data.get('gols_marcados_media', 0),
                    'gols_sofridos_media': time_data.get('gols_sofridos_media', 0),
                    'forma_multiplicador': time_data.get('forma_multiplicador', 1.0),
                    'metricas_5': time_data.get('metricas_5', {}),
                    'metricas_10': time_data.get('metricas_10', {}),
                    'metricas_20': time_data.get('metricas_20', {}),
                    # Escanteios
                    'escanteios_media': time_data.get('escanteios_media', 0),
                    'escanteios_casa_media': time_data.get('escanteios_casa_media', 0),
                    'escanteios_fora_media': time_data.get('escanteios_fora_media', 0),
                    'chutes_media': time_data.get('chutes_media', 0),
                }
    
    def _calcular_stats_times(self):
        """Agrega estatísticas por time a partir dos jogadores."""
        from collections import defaultdict
        
        stats_por_time = defaultdict(lambda: {
            'jogadores': 0,
            'partidas': 0,
            'gols': 0,
            'assistencias': 0,
            'chutes': 0,
            'chutes_gol': 0,
            'faltas': 0,
            'desarmes': 0,
        })
        
        for j in self.jogadores:
            time = j.get('time')
            if not time:
                continue
            
            stats_por_time[time]['jogadores'] += 1
            stats_por_time[time]['partidas'] += j.get('partidas', 0)
            stats_por_time[time]['gols'] += j.get('gols', 0)
            stats_por_time[time]['assistencias'] += j.get('assistencias', 0)
            stats_por_time[time]['chutes'] += j.get('chutes', 0)
            stats_por_time[time]['chutes_gol'] += j.get('chutes_no_gol', 0)
            stats_por_time[time]['faltas'] += j.get('faltas_cometidas', 0)
            stats_por_time[time]['desarmes'] += j.get('desarmes', 0)
        
        for nome, s in stats_por_time.items():
            ts = TeamStats(
                nome=nome,
                total_jogadores=s['jogadores'],
                total_partidas=s['partidas'],
                total_gols=s['gols'],
                total_assistencias=s['assistencias'],
                total_chutes=s['chutes'],
                total_chutes_gol=s['chutes_gol'],
                total_faltas=s['faltas'],
                total_desarmes=s['desarmes'],
            )
            # Estimar partidas do time (média de partidas por jogador ativo)
            jogadores_ativos = [j for j in self.jogadores if j.get('time') == nome and j.get('partidas', 0) > 0]
            if jogadores_ativos:
                partidas_estimadas = max(j.get('partidas', 0) for j in jogadores_ativos)
            else:
                partidas_estimadas = 20  # default
            ts.calcular_medias(partidas_estimadas)
            
            # Carregar dados de escanteios do times_metricas
            metricas = self.times_metricas.get(nome, {})
            ts.escanteios_media = metricas.get('escanteios_media', 0)
            ts.escanteios_casa_media = metricas.get('escanteios_casa_media', 0)
            ts.escanteios_fora_media = metricas.get('escanteios_fora_media', 0)
            
            self.times_stats[nome] = ts
        
        # Calcular médias da liga
        self.league_averages = calcular_league_averages(list(self.times_stats.values()))
        
        # Adicionar média de escanteios da liga
        escanteios_list = [ts.escanteios_media for ts in self.times_stats.values() if ts.escanteios_media > 0]
        self.league_averages['avg_corners_per_team'] = sum(escanteios_list) / len(escanteios_list) if escanteios_list else 5.0
    
    def _calcular_forcas(self):
        """Calcula attack strength e defense weakness para cada time usando dados reais."""
        avg_goals = self.league_averages.get('avg_goals_per_match', 1.3)
        
        # Calcular média de gols sofridos da liga
        gols_sofridos_list = [m.get('gols_sofridos_media', 0) for m in self.times_metricas.values() if m.get('gols_sofridos_media', 0) > 0]
        avg_goals_conceded = sum(gols_sofridos_list) / len(gols_sofridos_list) if gols_sofridos_list else avg_goals
        
        for nome, ts in self.times_stats.items():
            ts.attack_strength = calcular_attack_strength(ts, avg_goals)
            
            # Usar gols sofridos reais se disponível
            metricas = self.times_metricas.get(nome, {})
            gols_sofridos = metricas.get('gols_sofridos_media', 0)
            if gols_sofridos > 0:
                ts.defense_weakness = gols_sofridos / avg_goals_conceded
            else:
                ts.defense_weakness = 1.0  # Default neutro
        
        # Salvar média de gols sofridos da liga
        self.league_averages['avg_goals_conceded'] = avg_goals_conceded
    
    def get_forma_multiplicador(self, nome: str) -> float:
        """Retorna o multiplicador de forma baseado nas últimas partidas."""
        metricas = self.times_metricas.get(nome, {})
        return metricas.get('forma_multiplicador', 1.0)
    
    def get_metricas_recentes(self, nome: str, janela: int = 5) -> Dict:
        """Retorna métricas das últimas N partidas."""
        metricas = self.times_metricas.get(nome, {})
        if janela == 5:
            return metricas.get('metricas_5', {})
        elif janela == 10:
            return metricas.get('metricas_10', {})
        else:
            return metricas.get('metricas_20', {})
    
    def get_team_stats(self, nome: str) -> Optional[TeamStats]:
        """Retorna estatísticas de um time."""
        return self.times_stats.get(nome)
    
    def prever_partida(
        self, 
        home_team: str, 
        away_team: str,
        home_advantage: float = HOME_ADVANTAGE,
        usar_forma: bool = True
    ) -> Optional[MatchPrediction]:
        """
        Gera previsão completa para uma partida.
        
        Args:
            home_team: Nome do time mandante
            away_team: Nome do time visitante
            home_advantage: Multiplicador de vantagem em casa (default 1.08)
            usar_forma: Se True, aplica multiplicador de forma recente
        """
        home = self.times_stats.get(home_team)
        away = self.times_stats.get(away_team)
        
        if not home or not away:
            return None
        
        # Obter multiplicadores de forma
        forma_home = self.get_forma_multiplicador(home_team) if usar_forma else 1.0
        forma_away = self.get_forma_multiplicador(away_team) if usar_forma else 1.0
        
        # Estimar lambdas base
        lambda_home_base, lambda_away_base = estimar_lambda_gols(
            home, away, 
            self.league_averages['avg_goals_per_match'],
            home_advantage
        )
        
        # Aplicar multiplicador de forma
        # Time em boa forma → aumenta ataque, time em má forma → diminui
        lambda_home = lambda_home_base * forma_home
        lambda_away = lambda_away_base * forma_away
        
        lambda_total_goals = lambda_home + lambda_away
        
        lambda_shots = estimar_lambda_chutes(
            home, away,
            self.league_averages['avg_shots_per_match'],
            home_advantage
        )
        
        # Escanteios - usar dados reais por time (casa/fora)
        # Time da casa usa média em casa, visitante usa média fora
        lambda_home_corners = home.escanteios_casa_media if home.escanteios_casa_media > 0 else home.escanteios_media
        lambda_away_corners = away.escanteios_fora_media if away.escanteios_fora_media > 0 else away.escanteios_media
        
        # Se não tiver dados, usar estimativa
        if lambda_home_corners == 0:
            lambda_home_corners = self.league_averages.get('avg_corners_per_team', 5.0)
        if lambda_away_corners == 0:
            lambda_away_corners = self.league_averages.get('avg_corners_per_team', 5.0)
        
        lambda_corners = lambda_home_corners + lambda_away_corners
        
        lambda_fouls = estimar_lambda_faltas(
            home, away,
            self.league_averages['avg_fouls_per_match']
        )
        
        # Criar previsão
        pred = MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            lambda_home_goals=lambda_home,
            lambda_away_goals=lambda_away,
            lambda_total_goals=lambda_total_goals,
            lambda_total_shots=lambda_shots,
            lambda_total_corners=lambda_corners,
            lambda_total_fouls=lambda_fouls,
            lambda_home_corners=lambda_home_corners,
            lambda_away_corners=lambda_away_corners,
        )
        
        # Calcular probabilidades Over/Under gols
        pred.prob_over_05_goals = prob_over(lambda_total_goals, 0.5)
        pred.prob_over_15_goals = prob_over(lambda_total_goals, 1.5)
        pred.prob_over_25_goals = prob_over(lambda_total_goals, 2.5)
        pred.prob_over_35_goals = prob_over(lambda_total_goals, 3.5)
        
        # Calcular probabilidades Over/Under escanteios
        pred.prob_over_85_corners = prob_over(lambda_corners, 8.5)
        pred.prob_over_95_corners = prob_over(lambda_corners, 9.5)
        pred.prob_over_105_corners = prob_over(lambda_corners, 10.5)
        pred.prob_over_115_corners = prob_over(lambda_corners, 11.5)
        
        # BTTS
        pred.prob_btts = calcular_prob_btts(lambda_home, lambda_away)
        
        # Odds justas
        pred.odds_over_25 = prob_to_odds(pred.prob_over_25_goals)
        pred.odds_under_25 = prob_to_odds(1 - pred.prob_over_25_goals)
        
        return pred
    
    def ranking_escanteios(self) -> List[Tuple[str, float, float, float]]:
        """
        Retorna ranking de times por média de escanteios.
        Lista de tuplas (nome, escanteios_media, casa, fora).
        """
        ranking = []
        for nome, ts in self.times_stats.items():
            if ts.escanteios_media > 0:
                ranking.append((nome, ts.escanteios_media, ts.escanteios_casa_media, ts.escanteios_fora_media))
        
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    def ranking_times(self) -> List[Tuple[str, float, float]]:
        """
        Retorna ranking de times por força ofensiva.
        Lista de tuplas (nome, attack_strength, gols_por_partida).
        """
        ranking = []
        for nome, ts in self.times_stats.items():
            ranking.append((nome, ts.attack_strength, ts.gols_por_partida))
        
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    def imprimir_analise_partida(self, home: str, away: str):
        """Imprime análise completa de uma partida."""
        pred = self.prever_partida(home, away)
        if not pred:
            print(f"❌ Times não encontrados: {home} ou {away}")
            return
        
        print(f"\n{'='*60}")
        print(f"⚽ ANÁLISE: {home} vs {away}")
        print(f"{'='*60}")
        
        print(f"\n📊 LAMBDAS ESTIMADOS")
        print(f"  λ Gols {home}: {pred.lambda_home_goals:.2f}")
        print(f"  λ Gols {away}: {pred.lambda_away_goals:.2f}")
        print(f"  λ Total Gols: {pred.lambda_total_goals:.2f}")
        print(f"  λ Total Chutes: {pred.lambda_total_shots:.2f}")
        print(f"  λ Total Escanteios: {pred.lambda_total_corners:.2f}")
        print(f"  λ Total Faltas: {pred.lambda_total_fouls:.2f}")
        
        print(f"\n🎯 PROBABILIDADES GOLS")
        print(f"  Over 0.5: {pred.prob_over_05_goals*100:.1f}% (odd {prob_to_odds(pred.prob_over_05_goals):.2f})")
        print(f"  Over 1.5: {pred.prob_over_15_goals*100:.1f}% (odd {prob_to_odds(pred.prob_over_15_goals):.2f})")
        print(f"  Over 2.5: {pred.prob_over_25_goals*100:.1f}% (odd {prob_to_odds(pred.prob_over_25_goals):.2f})")
        print(f"  Over 3.5: {pred.prob_over_35_goals*100:.1f}% (odd {prob_to_odds(pred.prob_over_35_goals):.2f})")
        print(f"  BTTS: {pred.prob_btts*100:.1f}% (odd {prob_to_odds(pred.prob_btts):.2f})")
        
        # 1X2
        probs_1x2 = calcular_1x2(pred.lambda_home_goals, pred.lambda_away_goals)
        print(f"\n🏆 RESULTADO (1X2)")
        print(f"  Vitória {home}: {probs_1x2['home']*100:.1f}% (odd {prob_to_odds(probs_1x2['home']):.2f})")
        print(f"  Empate: {probs_1x2['draw']*100:.1f}% (odd {prob_to_odds(probs_1x2['draw']):.2f})")
        print(f"  Vitória {away}: {probs_1x2['away']*100:.1f}% (odd {prob_to_odds(probs_1x2['away']):.2f})")
        
        # Escanteios
        print(f"\n🚩 ESCANTEIOS")
        print(f"  λ {home}: {pred.lambda_home_corners:.1f} | λ {away}: {pred.lambda_away_corners:.1f}")
        print(f"  λ Total: {pred.lambda_total_corners:.1f}")
        print(f"  Over 8.5: {pred.prob_over_85_corners*100:.1f}% (odd {prob_to_odds(pred.prob_over_85_corners):.2f})")
        print(f"  Over 9.5: {pred.prob_over_95_corners*100:.1f}% (odd {prob_to_odds(pred.prob_over_95_corners):.2f})")
        print(f"  Over 10.5: {pred.prob_over_105_corners*100:.1f}% (odd {prob_to_odds(pred.prob_over_105_corners):.2f})")
        print(f"  Over 11.5: {pred.prob_over_115_corners*100:.1f}% (odd {prob_to_odds(pred.prob_over_115_corners):.2f})")
        
        # Top placares
        placares = calcular_resultado_exato(pred.lambda_home_goals, pred.lambda_away_goals)
        top_placares = sorted(placares.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n📋 TOP 5 PLACARES MAIS PROVÁVEIS")
        for placar, prob in top_placares:
            print(f"  {placar}: {prob*100:.1f}% (odd {prob_to_odds(prob):.2f})")


# ==================== MAIN PARA TESTES ====================

if __name__ == '__main__':
    print("🔄 Carregando dados e calculando forças...")
    analyzer = PoissonAnalyzer()
    
    print(f"\n📊 MÉDIAS DA LIGA")
    for k, v in analyzer.league_averages.items():
        print(f"  {k}: {v:.2f}")
    
    print(f"\n🏆 RANKING DE TIMES (Attack Strength)")
    for i, (nome, strength, gols) in enumerate(analyzer.ranking_times()[:10], 1):
        print(f"  {i}. {nome}: {strength:.2f} (⚽ {gols:.2f}/jogo)")
    
    print(f"\n🚩 RANKING DE ESCANTEIOS")
    for i, (nome, media, casa, fora) in enumerate(analyzer.ranking_escanteios()[:10], 1):
        print(f"  {i}. {nome}: {media:.1f} (Casa: {casa:.1f} | Fora: {fora:.1f})")
    
    # Exemplo de análise
    analyzer.imprimir_analise_partida("Flamengo", "Palmeiras")
    analyzer.imprimir_analise_partida("Corinthians", "São Paulo")
