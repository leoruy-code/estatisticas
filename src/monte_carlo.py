"""
Motor de Simulação Monte Carlo para Previsões de Apostas.

Gera intervalos de confiança (mínimo/máximo) para todas as estatísticas.
Foca nos mercados mais usados:
- Resultado (1X2 / Dupla Chance)
- Gols (Over/Under)
- Escanteios
- Cartões
- Chutes / Chutes ao Gol
- Marcadores prováveis
- Jogadores com chance de cartão amarelo
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter
import json
from pathlib import Path


@dataclass
class PlayerPrediction:
    """Previsão para um jogador específico."""
    nome: str
    time: str
    probabilidade: float = 0.0
    posicao: str = ""
    
    # Gols
    prob_marcar: float = 0.0
    gols_esperados: float = 0.0
    
    # Cartões
    prob_cartao_amarelo: float = 0.0
    cartoes_esperados: float = 0.0
    
    # Chutes
    chutes_esperados: float = 0.0
    chutes_gol_esperados: float = 0.0


@dataclass
class MatchSimulation:
    """Resultado completo de uma simulação de partida."""
    home_team: str
    away_team: str
    n_simulations: int
    
    # ========== RESULTADO 1X2 ==========
    prob_home_win: float = 0.0
    prob_draw: float = 0.0
    prob_away_win: float = 0.0
    
    # Dupla Chance
    prob_home_or_draw: float = 0.0  # 1X
    prob_away_or_draw: float = 0.0  # X2
    prob_home_or_away: float = 0.0  # 12
    
    # ========== GOLS ==========
    gols_home_media: float = 0.0
    gols_home_min: float = 0.0
    gols_home_max: float = 0.0
    
    gols_away_media: float = 0.0
    gols_away_min: float = 0.0
    gols_away_max: float = 0.0
    
    gols_total_media: float = 0.0
    gols_total_min: float = 0.0
    gols_total_max: float = 0.0
    
    # Probabilidades Over/Under Gols
    prob_over_05: float = 0.0
    prob_over_15: float = 0.0
    prob_over_25: float = 0.0
    prob_over_35: float = 0.0
    prob_over_45: float = 0.0
    
    prob_btts: float = 0.0
    
    # ========== ESCANTEIOS ==========
    escanteios_home_media: float = 0.0
    escanteios_home_min: float = 0.0
    escanteios_home_max: float = 0.0
    
    escanteios_away_media: float = 0.0
    escanteios_away_min: float = 0.0
    escanteios_away_max: float = 0.0
    
    escanteios_total_media: float = 0.0
    escanteios_total_min: float = 0.0
    escanteios_total_max: float = 0.0
    
    # Probabilidades Over/Under Escanteios
    prob_over_75_corners: float = 0.0
    prob_over_85_corners: float = 0.0
    prob_over_95_corners: float = 0.0
    prob_over_105_corners: float = 0.0
    prob_over_115_corners: float = 0.0
    
    # ========== CARTÕES ==========
    cartoes_home_media: float = 0.0
    cartoes_home_min: float = 0.0
    cartoes_home_max: float = 0.0
    
    cartoes_away_media: float = 0.0
    cartoes_away_min: float = 0.0
    cartoes_away_max: float = 0.0
    
    cartoes_total_media: float = 0.0
    cartoes_total_min: float = 0.0
    cartoes_total_max: float = 0.0
    
    # Probabilidades Over/Under Cartões
    prob_over_25_cards: float = 0.0
    prob_over_35_cards: float = 0.0
    prob_over_45_cards: float = 0.0
    prob_over_55_cards: float = 0.0
    
    # ========== CHUTES ==========
    chutes_home_media: float = 0.0
    chutes_home_min: float = 0.0
    chutes_home_max: float = 0.0
    
    chutes_away_media: float = 0.0
    chutes_away_min: float = 0.0
    chutes_away_max: float = 0.0
    
    chutes_total_media: float = 0.0
    chutes_total_min: float = 0.0
    chutes_total_max: float = 0.0
    
    # Chutes ao Gol
    chutes_gol_home_media: float = 0.0
    chutes_gol_away_media: float = 0.0
    chutes_gol_total_media: float = 0.0
    chutes_gol_total_min: float = 0.0
    chutes_gol_total_max: float = 0.0
    
    # ========== FALTAS ==========
    faltas_total_media: float = 0.0
    faltas_total_min: float = 0.0
    faltas_total_max: float = 0.0
    
    # ========== JOGADORES ==========
    marcadores_provaveis: List[PlayerPrediction] = field(default_factory=list)
    jogadores_cartao_provavel: List[PlayerPrediction] = field(default_factory=list)
    
    # ========== PLACARES MAIS PROVÁVEIS ==========
    placares_provaveis: List[Tuple[str, float]] = field(default_factory=list)


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para previsões de partidas.
    
    Gera distribuições completas com intervalos de confiança.
    """
    
    def __init__(
        self, 
        jogadores_path: str = 'data/jogadores.json',
        times_path: str = 'data/times.json',
        n_simulations: int = 50000,
        confidence_level: float = 0.90  # 90% intervalo de confiança
    ):
        self.n_simulations = n_simulations
        self.confidence_level = confidence_level
        self.alpha = (1 - confidence_level) / 2  # Para percentis
        
        self.jogadores = self._load_json(jogadores_path)
        self.times_data = self._load_json(times_path)
        
        # Indexar jogadores por time
        self.jogadores_por_time: Dict[str, List[dict]] = {}
        for j in self.jogadores:
            time = j.get('time', '')
            if time:
                if time not in self.jogadores_por_time:
                    self.jogadores_por_time[time] = []
                self.jogadores_por_time[time].append(j)
        
        # Indexar dados de times
        self.times_stats: Dict[str, dict] = {}
        for t in self.times_data:
            nome = t.get('nome', '')
            if nome:
                self.times_stats[nome] = t
        
        # Médias da liga (calculadas)
        self._calcular_medias_liga()
    
    def _load_json(self, path: str) -> List[dict]:
        p = Path(path)
        if not p.exists():
            return []
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _calcular_medias_liga(self):
        """Calcula médias da liga para normalização."""
        times_com_dados = [t for t in self.times_data if t.get('gols_marcados_media', 0) > 0]
        n = len(times_com_dados) if times_com_dados else 1
        
        self.liga_avg_gols = sum(t.get('gols_marcados_media', 0) for t in times_com_dados) / n if n > 0 else 1.3
        self.liga_avg_escanteios = sum(t.get('escanteios_media', 0) for t in times_com_dados) / n if n > 0 else 5.0
        
        # Médias de jogadores
        jogadores_com_partidas = [j for j in self.jogadores if j.get('partidas', 0) > 5]
        n_j = len(jogadores_com_partidas) if jogadores_com_partidas else 1
        
        self.liga_avg_faltas_jogador = sum(
            j.get('faltas_cometidas', 0) / max(j.get('partidas', 1), 1) 
            for j in jogadores_com_partidas
        ) / n_j if n_j > 0 else 1.5
        
        self.liga_avg_cartoes_jogador = sum(
            j.get('cartoes_amarelos', 0) / max(j.get('partidas', 1), 1)
            for j in jogadores_com_partidas
        ) / n_j if n_j > 0 else 0.15
    
    def _sample_event(self, lambda_val: float, variance_factor: float = 1.0) -> int:
        """
        Amostra um evento usando Poisson ou Negative Binomial.
        
        Args:
            lambda_val: Valor esperado (média)
            variance_factor: Fator de overdispersion (> 1 para NegBin)
        """
        if lambda_val <= 0:
            return 0
        
        if variance_factor <= 1.2:
            # Usar Poisson
            return np.random.poisson(lambda_val)
        else:
            # Usar Negative Binomial
            var = lambda_val * variance_factor
            p = lambda_val / var
            n = (lambda_val ** 2) / (var - lambda_val)
            if n <= 0 or p <= 0 or p >= 1:
                return np.random.poisson(lambda_val)
            return np.random.negative_binomial(n, p)
    
    def simular_com_lambdas(
        self,
        home_team: str,
        away_team: str,
        lambdas: Dict[str, float],
        home_players: List[dict] = None,
        away_players: List[dict] = None,
        confidence_level: float = None
    ) -> MatchSimulation:
        """
        Simula uma partida usando lambdas pré-calculados.
        
        Útil quando os lambdas já foram calculados pelo PoissonAnalyzer.
        
        Args:
            home_team: Nome do time da casa
            away_team: Nome do time visitante
            lambdas: Dicionário com os lambdas pré-calculados
            home_players: Lista de jogadores do time da casa
            away_players: Lista de jogadores do time visitante
            confidence_level: Nível de confiança (ex: 0.90 para 90%)
        """
        if confidence_level is None:
            confidence_level = self.confidence_level
        
        alpha = (1 - confidence_level) / 2
        
        # Arrays para armazenar resultados
        gols_home = np.zeros(self.n_simulations, dtype=int)
        gols_away = np.zeros(self.n_simulations, dtype=int)
        escanteios_home = np.zeros(self.n_simulations, dtype=int)
        escanteios_away = np.zeros(self.n_simulations, dtype=int)
        cartoes_home = np.zeros(self.n_simulations, dtype=int)
        cartoes_away = np.zeros(self.n_simulations, dtype=int)
        chutes_home = np.zeros(self.n_simulations, dtype=int)
        chutes_away = np.zeros(self.n_simulations, dtype=int)
        chutes_gol_home = np.zeros(self.n_simulations, dtype=int)
        chutes_gol_away = np.zeros(self.n_simulations, dtype=int)
        faltas_home = np.zeros(self.n_simulations, dtype=int)
        faltas_away = np.zeros(self.n_simulations, dtype=int)
        
        # Rodar simulações
        for i in range(self.n_simulations):
            gols_home[i] = self._sample_event(lambdas.get('gols_home', 1.3), 1.0)
            gols_away[i] = self._sample_event(lambdas.get('gols_away', 1.0), 1.0)
            escanteios_home[i] = self._sample_event(lambdas.get('escanteios_home', 5.0), 1.5)
            escanteios_away[i] = self._sample_event(lambdas.get('escanteios_away', 4.5), 1.5)
            cartoes_home[i] = self._sample_event(lambdas.get('cartoes_home', 2.0), 1.3)
            cartoes_away[i] = self._sample_event(lambdas.get('cartoes_away', 2.0), 1.3)
            chutes_home[i] = self._sample_event(lambdas.get('chutes_home', 12.0), 1.2)
            chutes_away[i] = self._sample_event(lambdas.get('chutes_away', 11.0), 1.2)
            chutes_gol_home[i] = self._sample_event(lambdas.get('chutes_gol_home', 4.5), 1.2)
            chutes_gol_away[i] = self._sample_event(lambdas.get('chutes_gol_away', 4.0), 1.2)
            faltas_home[i] = self._sample_event(lambdas.get('faltas_home', 12.0), 1.2)
            faltas_away[i] = self._sample_event(lambdas.get('faltas_away', 12.0), 1.2)
        
        # Calcular totais
        gols_total = gols_home + gols_away
        escanteios_total = escanteios_home + escanteios_away
        cartoes_total = cartoes_home + cartoes_away
        chutes_total = chutes_home + chutes_away
        chutes_gol_total = chutes_gol_home + chutes_gol_away
        faltas_total = faltas_home + faltas_away
        
        # Percentis
        lower_pct = alpha * 100
        upper_pct = (1 - alpha) * 100
        
        result = MatchSimulation(
            home_team=home_team,
            away_team=away_team,
            n_simulations=self.n_simulations,
            
            # Resultado 1X2
            prob_home_win=np.mean(gols_home > gols_away),
            prob_draw=np.mean(gols_home == gols_away),
            prob_away_win=np.mean(gols_home < gols_away),
            
            # Dupla Chance
            prob_home_or_draw=np.mean(gols_home >= gols_away),
            prob_away_or_draw=np.mean(gols_home <= gols_away),
            prob_home_or_away=np.mean(gols_home != gols_away),
            
            # Gols
            gols_home_media=np.mean(gols_home),
            gols_home_min=np.percentile(gols_home, lower_pct),
            gols_home_max=np.percentile(gols_home, upper_pct),
            
            gols_away_media=np.mean(gols_away),
            gols_away_min=np.percentile(gols_away, lower_pct),
            gols_away_max=np.percentile(gols_away, upper_pct),
            
            gols_total_media=np.mean(gols_total),
            gols_total_min=np.percentile(gols_total, lower_pct),
            gols_total_max=np.percentile(gols_total, upper_pct),
            
            prob_over_05=np.mean(gols_total > 0),
            prob_over_15=np.mean(gols_total > 1),
            prob_over_25=np.mean(gols_total > 2),
            prob_over_35=np.mean(gols_total > 3),
            prob_over_45=np.mean(gols_total > 4),
            prob_btts=np.mean((gols_home > 0) & (gols_away > 0)),
            
            # Escanteios
            escanteios_home_media=np.mean(escanteios_home),
            escanteios_home_min=np.percentile(escanteios_home, lower_pct),
            escanteios_home_max=np.percentile(escanteios_home, upper_pct),
            
            escanteios_away_media=np.mean(escanteios_away),
            escanteios_away_min=np.percentile(escanteios_away, lower_pct),
            escanteios_away_max=np.percentile(escanteios_away, upper_pct),
            
            escanteios_total_media=np.mean(escanteios_total),
            escanteios_total_min=np.percentile(escanteios_total, lower_pct),
            escanteios_total_max=np.percentile(escanteios_total, upper_pct),
            
            prob_over_75_corners=np.mean(escanteios_total > 7),
            prob_over_85_corners=np.mean(escanteios_total > 8),
            prob_over_95_corners=np.mean(escanteios_total > 9),
            prob_over_105_corners=np.mean(escanteios_total > 10),
            prob_over_115_corners=np.mean(escanteios_total > 11),
            
            # Cartões
            cartoes_home_media=np.mean(cartoes_home),
            cartoes_home_min=np.percentile(cartoes_home, lower_pct),
            cartoes_home_max=np.percentile(cartoes_home, upper_pct),
            
            cartoes_away_media=np.mean(cartoes_away),
            cartoes_away_min=np.percentile(cartoes_away, lower_pct),
            cartoes_away_max=np.percentile(cartoes_away, upper_pct),
            
            cartoes_total_media=np.mean(cartoes_total),
            cartoes_total_min=np.percentile(cartoes_total, lower_pct),
            cartoes_total_max=np.percentile(cartoes_total, upper_pct),
            
            prob_over_25_cards=np.mean(cartoes_total > 2),
            prob_over_35_cards=np.mean(cartoes_total > 3),
            prob_over_45_cards=np.mean(cartoes_total > 4),
            prob_over_55_cards=np.mean(cartoes_total > 5),
            
            # Chutes
            chutes_home_media=np.mean(chutes_home),
            chutes_home_min=np.percentile(chutes_home, lower_pct),
            chutes_home_max=np.percentile(chutes_home, upper_pct),
            
            chutes_away_media=np.mean(chutes_away),
            chutes_away_min=np.percentile(chutes_away, lower_pct),
            chutes_away_max=np.percentile(chutes_away, upper_pct),
            
            chutes_total_media=np.mean(chutes_total),
            chutes_total_min=np.percentile(chutes_total, lower_pct),
            chutes_total_max=np.percentile(chutes_total, upper_pct),
            
            chutes_gol_home_media=np.mean(chutes_gol_home),
            chutes_gol_away_media=np.mean(chutes_gol_away),
            chutes_gol_total_media=np.mean(chutes_gol_total),
            chutes_gol_total_min=np.percentile(chutes_gol_total, lower_pct),
            chutes_gol_total_max=np.percentile(chutes_gol_total, upper_pct),
            
            # Faltas
            faltas_total_media=np.mean(faltas_total),
            faltas_total_min=np.percentile(faltas_total, lower_pct),
            faltas_total_max=np.percentile(faltas_total, upper_pct),
        )
        
        # Placares mais prováveis
        placar_counter = Counter(zip(gols_home, gols_away))
        top_placares = placar_counter.most_common(10)
        result.placares_provaveis = [
            (f"{h}-{a}", count / self.n_simulations)
            for (h, a), count in top_placares
        ]
        
        # Prováveis marcadores
        if home_players or away_players:
            result.marcadores_provaveis = self._calcular_marcadores_provaveis_com_jogadores(
                home_players or [], away_players or [], lambdas
            )
            result.jogadores_cartao_provavel = self._calcular_cartoes_provaveis_com_jogadores(
                home_players or [], away_players or []
            )
        
        return result
    
    def _calcular_marcadores_provaveis_com_jogadores(
        self, 
        home_players: List[dict], 
        away_players: List[dict],
        lambdas: Dict[str, float]
    ) -> List[PlayerPrediction]:
        """Calcula marcadores prováveis baseado nos jogadores fornecidos."""
        marcadores = []
        
        # Calcular probabilidade total de gols
        lambda_home = lambdas.get('gols_home', 1.3)
        lambda_away = lambdas.get('gols_away', 1.0)
        
        # Para cada jogador, calcular probabilidade de marcar
        for player in home_players + away_players:
            is_home = player in home_players
            lambda_time = lambda_home if is_home else lambda_away
            
            # Índice ofensivo do jogador
            partidas = max(player.get('partidas', 1), 1)
            gols = player.get('gols', 0)
            xg = player.get('gols_esperados', 0)
            chutes = player.get('chutes', 0)
            
            gols_por_90 = gols / partidas
            xg_por_90 = xg / partidas
            chutes_por_90 = chutes / partidas
            
            # Peso do jogador na equipe
            off_index = 0.5 * gols_por_90 + 0.3 * xg_por_90 + 0.2 * (chutes_por_90 / 10)
            
            # Probabilidade baseada no lambda do time e índice do jogador
            # P(jogador marca) ≈ 1 - e^(-λ * off_index)
            prob_marcar = 1 - np.exp(-lambda_time * off_index)
            prob_marcar = min(prob_marcar, 0.6)  # Cap em 60%
            
            if prob_marcar > 0.05:  # Só incluir se > 5%
                team_name = player.get('time', 'Unknown')
                marcadores.append(PlayerPrediction(
                    nome=player.get('nome', 'Unknown'),
                    time=team_name,
                    probabilidade=prob_marcar
                ))
        
        # Ordenar por probabilidade
        marcadores.sort(key=lambda x: x.probabilidade, reverse=True)
        return marcadores[:10]
    
    def _calcular_cartoes_provaveis_com_jogadores(
        self,
        home_players: List[dict],
        away_players: List[dict]
    ) -> List[PlayerPrediction]:
        """Calcula jogadores mais prováveis de receber cartão amarelo."""
        jogadores_cartao = []
        
        for player in home_players + away_players:
            partidas = max(player.get('partidas', 1), 1)
            amarelos = player.get('cartoes_amarelos', 0)
            faltas = player.get('faltas_cometidas', 0)
            
            amarelos_por_90 = amarelos / partidas
            faltas_por_90 = faltas / partidas
            
            # Índice de disciplina
            disc_index = 0.6 * amarelos_por_90 + 0.4 * (faltas_por_90 / 10)
            
            # Probabilidade de cartão
            prob_cartao = 1 - np.exp(-2 * disc_index)
            prob_cartao = min(prob_cartao, 0.5)  # Cap em 50%
            
            if prob_cartao > 0.1:  # Só incluir se > 10%
                jogadores_cartao.append(PlayerPrediction(
                    nome=player.get('nome', 'Unknown'),
                    time=player.get('time', 'Unknown'),
                    probabilidade=prob_cartao
                ))
        
        jogadores_cartao.sort(key=lambda x: x.probabilidade, reverse=True)
        return jogadores_cartao[:10]
    
    def simular_partida(
        self, 
        home_team: str, 
        away_team: str,
        escalacao_home: List[str] = None,
        escalacao_away: List[str] = None
    ) -> MatchSimulation:
        """
        Simula uma partida completa com Monte Carlo.
        
        Args:
            home_team: Nome do time da casa
            away_team: Nome do time visitante
            escalacao_home: Lista de nomes dos jogadores titulares (opcional)
            escalacao_away: Lista de nomes dos jogadores titulares (opcional)
        
        Returns:
            MatchSimulation com todos os intervalos de confiança
        """
        home_stats = self.times_stats.get(home_team, {})
        away_stats = self.times_stats.get(away_team, {})
        
        # Calcular lambdas base
        lambdas = self._calcular_lambdas(home_stats, away_stats)
        
        # Ajustar por escalação se fornecida
        if escalacao_home:
            lambdas = self._ajustar_por_escalacao(lambdas, escalacao_home, 'home')
        if escalacao_away:
            lambdas = self._ajustar_por_escalacao(lambdas, escalacao_away, 'away')
        
        # Arrays para armazenar resultados
        gols_home = np.zeros(self.n_simulations, dtype=int)
        gols_away = np.zeros(self.n_simulations, dtype=int)
        escanteios_home = np.zeros(self.n_simulations, dtype=int)
        escanteios_away = np.zeros(self.n_simulations, dtype=int)
        cartoes_home = np.zeros(self.n_simulations, dtype=int)
        cartoes_away = np.zeros(self.n_simulations, dtype=int)
        chutes_home = np.zeros(self.n_simulations, dtype=int)
        chutes_away = np.zeros(self.n_simulations, dtype=int)
        chutes_gol_home = np.zeros(self.n_simulations, dtype=int)
        chutes_gol_away = np.zeros(self.n_simulations, dtype=int)
        faltas_home = np.zeros(self.n_simulations, dtype=int)
        faltas_away = np.zeros(self.n_simulations, dtype=int)
        
        # Rodar simulações
        for i in range(self.n_simulations):
            gols_home[i] = self._sample_event(lambdas['gols_home'], 1.0)
            gols_away[i] = self._sample_event(lambdas['gols_away'], 1.0)
            escanteios_home[i] = self._sample_event(lambdas['escanteios_home'], 1.5)
            escanteios_away[i] = self._sample_event(lambdas['escanteios_away'], 1.5)
            cartoes_home[i] = self._sample_event(lambdas['cartoes_home'], 1.3)
            cartoes_away[i] = self._sample_event(lambdas['cartoes_away'], 1.3)
            chutes_home[i] = self._sample_event(lambdas['chutes_home'], 1.2)
            chutes_away[i] = self._sample_event(lambdas['chutes_away'], 1.2)
            chutes_gol_home[i] = self._sample_event(lambdas['chutes_gol_home'], 1.2)
            chutes_gol_away[i] = self._sample_event(lambdas['chutes_gol_away'], 1.2)
            faltas_home[i] = self._sample_event(lambdas['faltas_home'], 1.2)
            faltas_away[i] = self._sample_event(lambdas['faltas_away'], 1.2)
        
        # Calcular totais
        gols_total = gols_home + gols_away
        escanteios_total = escanteios_home + escanteios_away
        cartoes_total = cartoes_home + cartoes_away
        chutes_total = chutes_home + chutes_away
        chutes_gol_total = chutes_gol_home + chutes_gol_away
        faltas_total = faltas_home + faltas_away
        
        # Percentis para intervalo de confiança
        lower_pct = self.alpha * 100
        upper_pct = (1 - self.alpha) * 100
        
        # Criar resultado
        result = MatchSimulation(
            home_team=home_team,
            away_team=away_team,
            n_simulations=self.n_simulations,
            
            # Resultado 1X2
            prob_home_win=np.mean(gols_home > gols_away),
            prob_draw=np.mean(gols_home == gols_away),
            prob_away_win=np.mean(gols_home < gols_away),
            
            # Dupla Chance
            prob_home_or_draw=np.mean(gols_home >= gols_away),
            prob_away_or_draw=np.mean(gols_home <= gols_away),
            prob_home_or_away=np.mean(gols_home != gols_away),
            
            # Gols
            gols_home_media=np.mean(gols_home),
            gols_home_min=np.percentile(gols_home, lower_pct),
            gols_home_max=np.percentile(gols_home, upper_pct),
            
            gols_away_media=np.mean(gols_away),
            gols_away_min=np.percentile(gols_away, lower_pct),
            gols_away_max=np.percentile(gols_away, upper_pct),
            
            gols_total_media=np.mean(gols_total),
            gols_total_min=np.percentile(gols_total, lower_pct),
            gols_total_max=np.percentile(gols_total, upper_pct),
            
            prob_over_05=np.mean(gols_total > 0),
            prob_over_15=np.mean(gols_total > 1),
            prob_over_25=np.mean(gols_total > 2),
            prob_over_35=np.mean(gols_total > 3),
            prob_over_45=np.mean(gols_total > 4),
            prob_btts=np.mean((gols_home > 0) & (gols_away > 0)),
            
            # Escanteios
            escanteios_home_media=np.mean(escanteios_home),
            escanteios_home_min=np.percentile(escanteios_home, lower_pct),
            escanteios_home_max=np.percentile(escanteios_home, upper_pct),
            
            escanteios_away_media=np.mean(escanteios_away),
            escanteios_away_min=np.percentile(escanteios_away, lower_pct),
            escanteios_away_max=np.percentile(escanteios_away, upper_pct),
            
            escanteios_total_media=np.mean(escanteios_total),
            escanteios_total_min=np.percentile(escanteios_total, lower_pct),
            escanteios_total_max=np.percentile(escanteios_total, upper_pct),
            
            prob_over_75_corners=np.mean(escanteios_total > 7),
            prob_over_85_corners=np.mean(escanteios_total > 8),
            prob_over_95_corners=np.mean(escanteios_total > 9),
            prob_over_105_corners=np.mean(escanteios_total > 10),
            prob_over_115_corners=np.mean(escanteios_total > 11),
            
            # Cartões
            cartoes_home_media=np.mean(cartoes_home),
            cartoes_home_min=np.percentile(cartoes_home, lower_pct),
            cartoes_home_max=np.percentile(cartoes_home, upper_pct),
            
            cartoes_away_media=np.mean(cartoes_away),
            cartoes_away_min=np.percentile(cartoes_away, lower_pct),
            cartoes_away_max=np.percentile(cartoes_away, upper_pct),
            
            cartoes_total_media=np.mean(cartoes_total),
            cartoes_total_min=np.percentile(cartoes_total, lower_pct),
            cartoes_total_max=np.percentile(cartoes_total, upper_pct),
            
            prob_over_25_cards=np.mean(cartoes_total > 2),
            prob_over_35_cards=np.mean(cartoes_total > 3),
            prob_over_45_cards=np.mean(cartoes_total > 4),
            prob_over_55_cards=np.mean(cartoes_total > 5),
            
            # Chutes
            chutes_home_media=np.mean(chutes_home),
            chutes_home_min=np.percentile(chutes_home, lower_pct),
            chutes_home_max=np.percentile(chutes_home, upper_pct),
            
            chutes_away_media=np.mean(chutes_away),
            chutes_away_min=np.percentile(chutes_away, lower_pct),
            chutes_away_max=np.percentile(chutes_away, upper_pct),
            
            chutes_total_media=np.mean(chutes_total),
            chutes_total_min=np.percentile(chutes_total, lower_pct),
            chutes_total_max=np.percentile(chutes_total, upper_pct),
            
            chutes_gol_home_media=np.mean(chutes_gol_home),
            chutes_gol_away_media=np.mean(chutes_gol_away),
            chutes_gol_total_media=np.mean(chutes_gol_total),
            chutes_gol_total_min=np.percentile(chutes_gol_total, lower_pct),
            chutes_gol_total_max=np.percentile(chutes_gol_total, upper_pct),
            
            # Faltas
            faltas_total_media=np.mean(faltas_total),
            faltas_total_min=np.percentile(faltas_total, lower_pct),
            faltas_total_max=np.percentile(faltas_total, upper_pct),
        )
        
        # Calcular placares mais prováveis
        placar_counter = Counter(zip(gols_home, gols_away))
        top_placares = placar_counter.most_common(10)
        result.placares_provaveis = [
            (f"{h}-{a}", count / self.n_simulations)
            for (h, a), count in top_placares
        ]
        
        # Calcular prováveis marcadores
        result.marcadores_provaveis = self._calcular_marcadores_provaveis(
            home_team, away_team, lambdas
        )
        
        # Calcular jogadores com chance de cartão
        result.jogadores_cartao_provavel = self._calcular_jogadores_cartao(
            home_team, away_team
        )
        
        return result
    
    def _calcular_lambdas(self, home_stats: dict, away_stats: dict) -> Dict[str, float]:
        """Calcula os lambdas base para a simulação."""
        HOME_ADVANTAGE = 1.08
        
        # Forma
        forma_home = home_stats.get('forma_multiplicador', 1.0)
        forma_away = away_stats.get('forma_multiplicador', 1.0)
        
        # Gols
        gols_home_base = home_stats.get('gols_marcados_media', self.liga_avg_gols)
        gols_away_base = away_stats.get('gols_marcados_media', self.liga_avg_gols)
        gols_sofridos_home = home_stats.get('gols_sofridos_media', self.liga_avg_gols)
        gols_sofridos_away = away_stats.get('gols_sofridos_media', self.liga_avg_gols)
        
        # Attack/Defense strength
        attack_home = gols_home_base / self.liga_avg_gols if self.liga_avg_gols > 0 else 1.0
        attack_away = gols_away_base / self.liga_avg_gols if self.liga_avg_gols > 0 else 1.0
        defense_home = gols_sofridos_home / self.liga_avg_gols if self.liga_avg_gols > 0 else 1.0
        defense_away = gols_sofridos_away / self.liga_avg_gols if self.liga_avg_gols > 0 else 1.0
        
        lambda_gols_home = self.liga_avg_gols * attack_home * defense_away * HOME_ADVANTAGE * forma_home
        lambda_gols_away = self.liga_avg_gols * attack_away * defense_home * forma_away
        
        # Escanteios (usando dados reais se disponível)
        escanteios_home = home_stats.get('escanteios_casa_media', 0) or home_stats.get('escanteios_media', 5.0)
        escanteios_away = away_stats.get('escanteios_fora_media', 0) or away_stats.get('escanteios_media', 5.0)
        
        # Chutes (estimativa baseada em força ofensiva)
        chutes_home = home_stats.get('chutes_media', 12.0) * HOME_ADVANTAGE * forma_home
        chutes_away = away_stats.get('chutes_media', 12.0) * forma_away
        
        # Chutes ao gol (~35% dos chutes em média)
        chutes_gol_home = chutes_home * 0.35
        chutes_gol_away = chutes_away * 0.35
        
        # Cartões (baseado em jogadores)
        cartoes_home = self._estimar_cartoes_time(home_stats.get('nome', ''))
        cartoes_away = self._estimar_cartoes_time(away_stats.get('nome', ''))
        
        # Faltas
        faltas_home = self._estimar_faltas_time(home_stats.get('nome', ''))
        faltas_away = self._estimar_faltas_time(away_stats.get('nome', ''))
        
        return {
            'gols_home': lambda_gols_home,
            'gols_away': lambda_gols_away,
            'escanteios_home': escanteios_home,
            'escanteios_away': escanteios_away,
            'cartoes_home': cartoes_home,
            'cartoes_away': cartoes_away,
            'chutes_home': chutes_home,
            'chutes_away': chutes_away,
            'chutes_gol_home': chutes_gol_home,
            'chutes_gol_away': chutes_gol_away,
            'faltas_home': faltas_home,
            'faltas_away': faltas_away,
        }
    
    def _estimar_cartoes_time(self, nome_time: str) -> float:
        """Estima cartões esperados baseado nos jogadores do time."""
        jogadores = self.jogadores_por_time.get(nome_time, [])
        if not jogadores:
            return 2.0  # Default
        
        total_cartoes = 0
        total_partidas = 0
        
        for j in jogadores:
            partidas = j.get('partidas', 0)
            if partidas > 0:
                total_cartoes += j.get('cartoes_amarelos', 0)
                total_partidas += partidas
        
        if total_partidas > 0:
            # Média de cartões por partida (considerando ~14 jogadores jogam por partida em média)
            return (total_cartoes / total_partidas) * 11
        
        return 2.0
    
    def _estimar_faltas_time(self, nome_time: str) -> float:
        """Estima faltas esperadas baseado nos jogadores do time."""
        jogadores = self.jogadores_por_time.get(nome_time, [])
        if not jogadores:
            return 12.0  # Default
        
        total_faltas = 0
        total_partidas = 0
        
        for j in jogadores:
            partidas = j.get('partidas', 0)
            if partidas > 0:
                total_faltas += j.get('faltas_cometidas', 0)
                total_partidas += partidas
        
        if total_partidas > 0:
            return (total_faltas / total_partidas) * 11
        
        return 12.0
    
    def _ajustar_por_escalacao(self, lambdas: dict, escalacao: List[str], side: str) -> dict:
        """Ajusta lambdas baseado na escalação específica."""
        # TODO: Implementar ajuste fino baseado nos jogadores escalados
        # Por enquanto, retorna lambdas sem ajuste
        return lambdas
    
    def _calcular_marcadores_provaveis(
        self, 
        home_team: str, 
        away_team: str,
        lambdas: dict
    ) -> List[PlayerPrediction]:
        """Calcula os jogadores mais prováveis de marcar."""
        marcadores = []
        
        for time in [home_team, away_team]:
            jogadores = self.jogadores_por_time.get(time, [])
            lambda_gols = lambdas['gols_home'] if time == home_team else lambdas['gols_away']
            
            # Filtrar jogadores com potencial ofensivo
            atacantes = [
                j for j in jogadores 
                if j.get('partidas', 0) > 3 and j.get('gols', 0) >= 0
            ]
            
            # Calcular probabilidade de cada jogador marcar
            total_gols_time = sum(j.get('gols', 0) for j in atacantes) or 1
            
            for j in atacantes:
                gols = j.get('gols', 0)
                partidas = max(j.get('partidas', 1), 1)
                gols_por_jogo = gols / partidas
                
                # Share de gols do jogador no time
                share_gols = gols / total_gols_time if total_gols_time > 0 else 0
                
                # Prob de marcar = lambda do time * share do jogador * fator de ajuste
                prob_marcar = min(lambda_gols * share_gols * 0.8, 0.99)
                
                if prob_marcar > 0.05:  # Só incluir se > 5%
                    marcadores.append(PlayerPrediction(
                        nome=j.get('nome', ''),
                        time=time,
                        posicao=j.get('posicao', ''),
                        prob_marcar=prob_marcar,
                        gols_esperados=gols_por_jogo,
                    ))
        
        # Ordenar por probabilidade
        marcadores.sort(key=lambda x: x.prob_marcar, reverse=True)
        return marcadores[:10]  # Top 10
    
    def _calcular_jogadores_cartao(
        self, 
        home_team: str, 
        away_team: str
    ) -> List[PlayerPrediction]:
        """Calcula jogadores com maior chance de receber cartão amarelo."""
        jogadores_cartao = []
        
        for time in [home_team, away_team]:
            jogadores = self.jogadores_por_time.get(time, [])
            
            for j in jogadores:
                partidas = j.get('partidas', 0)
                if partidas < 3:
                    continue
                
                cartoes = j.get('cartoes_amarelos', 0)
                faltas = j.get('faltas_cometidas', 0)
                
                # Taxa de cartões por jogo
                taxa_cartoes = cartoes / partidas
                taxa_faltas = faltas / partidas
                
                # Probabilidade estimada (baseada em taxa histórica + faltas)
                # Jogadores que fazem muitas faltas têm mais chance de cartão
                prob_cartao = min(taxa_cartoes + (taxa_faltas * 0.05), 0.80)
                
                if prob_cartao > 0.10:  # Só incluir se > 10%
                    jogadores_cartao.append(PlayerPrediction(
                        nome=j.get('nome', ''),
                        time=time,
                        posicao=j.get('posicao', ''),
                        prob_cartao_amarelo=prob_cartao,
                        cartoes_esperados=taxa_cartoes,
                    ))
        
        # Ordenar por probabilidade
        jogadores_cartao.sort(key=lambda x: x.prob_cartao_amarelo, reverse=True)
        return jogadores_cartao[:10]  # Top 10


def imprimir_simulacao(sim: MatchSimulation):
    """Imprime resultado da simulação de forma formatada."""
    print(f"\n{'='*70}")
    print(f"⚽ SIMULAÇÃO: {sim.home_team} vs {sim.away_team}")
    print(f"📊 {sim.n_simulations:,} simulações | Intervalo de Confiança: 90%")
    print(f"{'='*70}")
    
    print(f"\n🏆 RESULTADO (1X2)")
    print(f"   Vitória {sim.home_team}: {sim.prob_home_win*100:.1f}%")
    print(f"   Empate: {sim.prob_draw*100:.1f}%")
    print(f"   Vitória {sim.away_team}: {sim.prob_away_win*100:.1f}%")
    print(f"\n   Dupla Chance:")
    print(f"   1X (Casa/Empate): {sim.prob_home_or_draw*100:.1f}%")
    print(f"   X2 (Fora/Empate): {sim.prob_away_or_draw*100:.1f}%")
    print(f"   12 (Sem Empate): {sim.prob_home_or_away*100:.1f}%")
    
    print(f"\n⚽ GOLS")
    print(f"   {sim.home_team}: {sim.gols_home_media:.1f} (min: {sim.gols_home_min:.0f}, max: {sim.gols_home_max:.0f})")
    print(f"   {sim.away_team}: {sim.gols_away_media:.1f} (min: {sim.gols_away_min:.0f}, max: {sim.gols_away_max:.0f})")
    print(f"   Total: {sim.gols_total_media:.1f} (min: {sim.gols_total_min:.0f}, max: {sim.gols_total_max:.0f})")
    print(f"\n   Over/Under Gols:")
    print(f"   Over 0.5: {sim.prob_over_05*100:.1f}% | Over 1.5: {sim.prob_over_15*100:.1f}%")
    print(f"   Over 2.5: {sim.prob_over_25*100:.1f}% | Over 3.5: {sim.prob_over_35*100:.1f}%")
    print(f"   BTTS: {sim.prob_btts*100:.1f}%")
    
    print(f"\n🚩 ESCANTEIOS")
    print(f"   {sim.home_team}: {sim.escanteios_home_media:.1f} (min: {sim.escanteios_home_min:.0f}, max: {sim.escanteios_home_max:.0f})")
    print(f"   {sim.away_team}: {sim.escanteios_away_media:.1f} (min: {sim.escanteios_away_min:.0f}, max: {sim.escanteios_away_max:.0f})")
    print(f"   Total: {sim.escanteios_total_media:.1f} (min: {sim.escanteios_total_min:.0f}, max: {sim.escanteios_total_max:.0f})")
    print(f"\n   Over/Under Escanteios:")
    print(f"   Over 7.5: {sim.prob_over_75_corners*100:.1f}% | Over 8.5: {sim.prob_over_85_corners*100:.1f}%")
    print(f"   Over 9.5: {sim.prob_over_95_corners*100:.1f}% | Over 10.5: {sim.prob_over_105_corners*100:.1f}%")
    
    print(f"\n🟨 CARTÕES")
    print(f"   {sim.home_team}: {sim.cartoes_home_media:.1f} (min: {sim.cartoes_home_min:.0f}, max: {sim.cartoes_home_max:.0f})")
    print(f"   {sim.away_team}: {sim.cartoes_away_media:.1f} (min: {sim.cartoes_away_min:.0f}, max: {sim.cartoes_away_max:.0f})")
    print(f"   Total: {sim.cartoes_total_media:.1f} (min: {sim.cartoes_total_min:.0f}, max: {sim.cartoes_total_max:.0f})")
    print(f"\n   Over/Under Cartões:")
    print(f"   Over 2.5: {sim.prob_over_25_cards*100:.1f}% | Over 3.5: {sim.prob_over_35_cards*100:.1f}%")
    print(f"   Over 4.5: {sim.prob_over_45_cards*100:.1f}% | Over 5.5: {sim.prob_over_55_cards*100:.1f}%")
    
    print(f"\n👟 CHUTES")
    print(f"   {sim.home_team}: {sim.chutes_home_media:.1f} (min: {sim.chutes_home_min:.0f}, max: {sim.chutes_home_max:.0f})")
    print(f"   {sim.away_team}: {sim.chutes_away_media:.1f} (min: {sim.chutes_away_min:.0f}, max: {sim.chutes_away_max:.0f})")
    print(f"   Total: {sim.chutes_total_media:.1f} (min: {sim.chutes_total_min:.0f}, max: {sim.chutes_total_max:.0f})")
    print(f"\n   Chutes ao Gol:")
    print(f"   Total: {sim.chutes_gol_total_media:.1f} (min: {sim.chutes_gol_total_min:.0f}, max: {sim.chutes_gol_total_max:.0f})")
    
    print(f"\n📋 TOP 5 PLACARES MAIS PROVÁVEIS")
    for placar, prob in sim.placares_provaveis[:5]:
        print(f"   {placar}: {prob*100:.1f}%")
    
    if sim.marcadores_provaveis:
        print(f"\n⚽ PROVÁVEIS MARCADORES")
        for m in sim.marcadores_provaveis[:5]:
            print(f"   {m.nome} ({m.time}): {m.prob_marcar*100:.1f}%")
    
    if sim.jogadores_cartao_provavel:
        print(f"\n🟨 PROVÁVEIS CARTÕES AMARELOS")
        for j in sim.jogadores_cartao_provavel[:5]:
            print(f"   {j.nome} ({j.time}): {j.prob_cartao_amarelo*100:.1f}%")
    
    print(f"\n{'='*70}")


if __name__ == '__main__':
    # Teste
    simulator = MonteCarloSimulator(
        jogadores_path='data/jogadores.json',
        times_path='data/times.json',
        n_simulations=50000
    )
    
    resultado = simulator.simular_partida('Flamengo', 'Palmeiras')
    imprimir_simulacao(resultado)
