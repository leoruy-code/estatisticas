"""
Modelo de Jogadores - Issues 9-11 do Plano de Implementação

Implementa:
- Issue 9: Índices por jogador (off_index, cross_index, foul_index)
- Issue 10: Agregação de índices da escalação
- Issue 11: Ajuste de λ baseado na escalação

Fórmulas baseadas no documento oque_eu_quero.md
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np


@dataclass
class PlayerIndices:
    """Índices calculados para um jogador."""
    nome: str
    time: str
    posicao: str
    
    # Índice Ofensivo (impacto em gols)
    off_index: float = 0.0
    
    # Índice de Cruzamentos/Bola Parada (impacto em escanteios)
    cross_index: float = 0.0
    
    # Índice de Faltas/Disciplina (impacto em cartões)
    foul_index: float = 0.0
    
    # Estatísticas base
    gols_por_90: float = 0.0
    xg_por_90: float = 0.0
    finalizacoes_por_90: float = 0.0
    passes_chave_por_90: float = 0.0
    escanteios_cobrados_por_90: float = 0.0
    cruzamentos_por_90: float = 0.0
    faltas_cometidas_por_90: float = 0.0
    cartoes_por_90: float = 0.0


@dataclass
class LineupRatios:
    """Ratios calculados para uma escalação."""
    off_ratio: float = 1.0      # Impacto ofensivo da escalação
    cross_ratio: float = 1.0    # Impacto em escanteios
    foul_ratio: float = 1.0     # Impacto em faltas/cartões
    
    # Detalhes
    off_index_lineup: float = 0.0
    off_index_team_avg: float = 0.0
    cross_index_lineup: float = 0.0
    cross_index_team_avg: float = 0.0
    foul_index_lineup: float = 0.0
    foul_index_team_avg: float = 0.0


@dataclass
class AdjustedLambdas:
    """Lambdas ajustados pela escalação."""
    lambda_goals: float
    lambda_corners: float
    lambda_cards: float
    lambda_fouls: float
    
    # Ajustes aplicados
    off_adjustment: float = 1.0
    cross_adjustment: float = 1.0
    foul_adjustment: float = 1.0


class PlayerModel:
    """
    Modelo de impacto de jogadores nas previsões.
    
    Implementa as Issues 9-11 do plano de implementação.
    """
    
    # Pesos para cálculo dos índices (podem ser ajustados)
    OFF_WEIGHTS = {
        'gols_por_90': 0.35,
        'xg_por_90': 0.25,
        'finalizacoes_por_90': 0.20,
        'passes_chave_por_90': 0.20
    }
    
    CROSS_WEIGHTS = {
        'escanteios_cobrados_por_90': 0.50,
        'cruzamentos_por_90': 0.50
    }
    
    FOUL_WEIGHTS = {
        'faltas_cometidas_por_90': 0.40,
        'cartoes_por_90': 0.60
    }
    
    # Limites para clipping dos ratios
    RATIO_MIN = 0.70
    RATIO_MAX = 1.30
    
    def __init__(self, jogadores_path: str = 'data/jogadores.json'):
        self.jogadores_path = Path(jogadores_path)
        self.jogadores: List[dict] = []
        self.indices_por_time: Dict[str, List[PlayerIndices]] = {}
        self.medias_por_time: Dict[str, Dict[str, float]] = {}
        
        self._carregar_jogadores()
        self._calcular_todos_indices()
    
    def _carregar_jogadores(self):
        """Carrega jogadores do arquivo JSON."""
        if self.jogadores_path.exists():
            with open(self.jogadores_path, 'r', encoding='utf-8') as f:
                self.jogadores = json.load(f)
        else:
            self.jogadores = []
    
    def _normalizar_por_90(self, valor: float, partidas: int) -> float:
        """Normaliza estatística para por 90 minutos."""
        if partidas <= 0:
            return 0.0
        return valor / partidas
    
    def _calcular_indice_jogador(self, jogador: dict) -> PlayerIndices:
        """
        Calcula os índices para um jogador individual (Issue 9).
        
        Fórmulas:
        - off_index = w1*gols_90 + w2*xg_90 + w3*finalizacoes_90 + w4*passes_chave_90
        - cross_index = w5*escanteios_cobrados_90 + w6*cruzamentos_90
        - foul_index = w7*faltas_cometidas_90 + w8*cartoes_90
        """
        partidas = max(jogador.get('partidas', 1), 1)
        
        # Estatísticas por 90 minutos
        gols_por_90 = self._normalizar_por_90(jogador.get('gols', 0), partidas)
        xg_por_90 = self._normalizar_por_90(jogador.get('gols_esperados', 0), partidas)
        finalizacoes_por_90 = self._normalizar_por_90(jogador.get('chutes', 0), partidas)
        passes_chave_por_90 = self._normalizar_por_90(jogador.get('passes_decisivos', 0), partidas)
        escanteios_cobrados_por_90 = self._normalizar_por_90(jogador.get('escanteios_cobrados', 0), partidas)
        cruzamentos_por_90 = self._normalizar_por_90(jogador.get('cruzamentos_certos', 0), partidas)
        faltas_cometidas_por_90 = self._normalizar_por_90(jogador.get('faltas_cometidas', 0), partidas)
        cartoes_por_90 = self._normalizar_por_90(
            jogador.get('cartoes_amarelos', 0) + jogador.get('cartoes_vermelhos', 0) * 2,
            partidas
        )
        
        # Calcular índice ofensivo
        off_index = (
            self.OFF_WEIGHTS['gols_por_90'] * gols_por_90 +
            self.OFF_WEIGHTS['xg_por_90'] * xg_por_90 +
            self.OFF_WEIGHTS['finalizacoes_por_90'] * (finalizacoes_por_90 / 10) +  # Normalizar escala
            self.OFF_WEIGHTS['passes_chave_por_90'] * passes_chave_por_90
        )
        
        # Calcular índice de cruzamentos
        cross_index = (
            self.CROSS_WEIGHTS['escanteios_cobrados_por_90'] * escanteios_cobrados_por_90 +
            self.CROSS_WEIGHTS['cruzamentos_por_90'] * (cruzamentos_por_90 / 5)  # Normalizar escala
        )
        
        # Calcular índice de faltas
        foul_index = (
            self.FOUL_WEIGHTS['faltas_cometidas_por_90'] * (faltas_cometidas_por_90 / 3) +  # Normalizar
            self.FOUL_WEIGHTS['cartoes_por_90'] * cartoes_por_90 * 5  # Amplificar impacto de cartões
        )
        
        return PlayerIndices(
            nome=jogador.get('nome', ''),
            time=jogador.get('time', ''),
            posicao=jogador.get('posicao', ''),
            off_index=off_index,
            cross_index=cross_index,
            foul_index=foul_index,
            gols_por_90=gols_por_90,
            xg_por_90=xg_por_90,
            finalizacoes_por_90=finalizacoes_por_90,
            passes_chave_por_90=passes_chave_por_90,
            escanteios_cobrados_por_90=escanteios_cobrados_por_90,
            cruzamentos_por_90=cruzamentos_por_90,
            faltas_cometidas_por_90=faltas_cometidas_por_90,
            cartoes_por_90=cartoes_por_90
        )
    
    def _calcular_todos_indices(self):
        """Calcula índices para todos os jogadores e agrupa por time."""
        self.indices_por_time = {}
        
        for jogador in self.jogadores:
            time = jogador.get('time', '')
            if not time:
                continue
            
            indices = self._calcular_indice_jogador(jogador)
            
            if time not in self.indices_por_time:
                self.indices_por_time[time] = []
            self.indices_por_time[time].append(indices)
        
        # Calcular médias por time
        for time, jogadores_indices in self.indices_por_time.items():
            if jogadores_indices:
                self.medias_por_time[time] = {
                    'off_index_avg': np.mean([j.off_index for j in jogadores_indices]),
                    'cross_index_avg': np.mean([j.cross_index for j in jogadores_indices]),
                    'foul_index_avg': np.mean([j.foul_index for j in jogadores_indices])
                }
    
    def get_player_indices(self, nome: str) -> Optional[PlayerIndices]:
        """Retorna os índices de um jogador específico."""
        for jogadores_time in self.indices_por_time.values():
            for indices in jogadores_time:
                if indices.nome == nome:
                    return indices
        return None
    
    def get_team_indices(self, time: str) -> List[PlayerIndices]:
        """Retorna índices de todos os jogadores de um time."""
        return self.indices_por_time.get(time, [])
    
    def get_team_averages(self, time: str) -> Dict[str, float]:
        """Retorna médias dos índices do time."""
        return self.medias_por_time.get(time, {
            'off_index_avg': 0.0,
            'cross_index_avg': 0.0,
            'foul_index_avg': 0.0
        })
    
    def calcular_lineup_ratios(
        self, 
        time: str, 
        escalacao: List[str]
    ) -> LineupRatios:
        """
        Calcula os ratios de impacto de uma escalação (Issue 10).
        
        Args:
            time: Nome do time
            escalacao: Lista de nomes dos 11 jogadores titulares
        
        Returns:
            LineupRatios com off_ratio, cross_ratio, foul_ratio
        """
        # Buscar índices dos jogadores na escalação
        indices_escalacao = []
        for nome_jogador in escalacao:
            indices = self.get_player_indices(nome_jogador)
            if indices:
                indices_escalacao.append(indices)
        
        if not indices_escalacao:
            return LineupRatios()  # Retorna ratios neutros (1.0)
        
        # Calcular soma dos índices da escalação
        off_index_lineup = sum(j.off_index for j in indices_escalacao)
        cross_index_lineup = sum(j.cross_index for j in indices_escalacao)
        foul_index_lineup = sum(j.foul_index for j in indices_escalacao)
        
        # Buscar médias do time completo
        medias = self.get_team_averages(time)
        n_jogadores = len(self.get_team_indices(time))
        
        if n_jogadores == 0:
            return LineupRatios()
        
        # Índice médio esperado para 11 jogadores
        off_index_team_avg = medias.get('off_index_avg', 0) * 11
        cross_index_team_avg = medias.get('cross_index_avg', 0) * 11
        foul_index_team_avg = medias.get('foul_index_avg', 0) * 11
        
        # Calcular ratios (com proteção contra divisão por zero)
        off_ratio = off_index_lineup / off_index_team_avg if off_index_team_avg > 0 else 1.0
        cross_ratio = cross_index_lineup / cross_index_team_avg if cross_index_team_avg > 0 else 1.0
        foul_ratio = foul_index_lineup / foul_index_team_avg if foul_index_team_avg > 0 else 1.0
        
        # Aplicar clipping para evitar ajustes extremos
        off_ratio = np.clip(off_ratio, self.RATIO_MIN, self.RATIO_MAX)
        cross_ratio = np.clip(cross_ratio, self.RATIO_MIN, self.RATIO_MAX)
        foul_ratio = np.clip(foul_ratio, self.RATIO_MIN, self.RATIO_MAX)
        
        return LineupRatios(
            off_ratio=off_ratio,
            cross_ratio=cross_ratio,
            foul_ratio=foul_ratio,
            off_index_lineup=off_index_lineup,
            off_index_team_avg=off_index_team_avg,
            cross_index_lineup=cross_index_lineup,
            cross_index_team_avg=cross_index_team_avg,
            foul_index_lineup=foul_index_lineup,
            foul_index_team_avg=foul_index_team_avg
        )
    
    def ajustar_lambdas(
        self,
        lambda_goals: float,
        lambda_corners: float,
        lambda_cards: float,
        lambda_fouls: float,
        ratios: LineupRatios
    ) -> AdjustedLambdas:
        """
        Ajusta os lambdas baseado nos ratios da escalação (Issue 11).
        
        Args:
            lambda_goals: λ base para gols
            lambda_corners: λ base para escanteios
            lambda_cards: λ base para cartões
            lambda_fouls: λ base para faltas
            ratios: Ratios calculados da escalação
        
        Returns:
            AdjustedLambdas com valores ajustados
        """
        return AdjustedLambdas(
            lambda_goals=lambda_goals * ratios.off_ratio,
            lambda_corners=lambda_corners * ratios.cross_ratio,
            lambda_cards=lambda_cards * ratios.foul_ratio,
            lambda_fouls=lambda_fouls * ratios.foul_ratio,
            off_adjustment=ratios.off_ratio,
            cross_adjustment=ratios.cross_ratio,
            foul_adjustment=ratios.foul_ratio
        )
    
    def prever_com_escalacao(
        self,
        home_team: str,
        away_team: str,
        escalacao_home: List[str],
        escalacao_away: List[str],
        lambdas_base: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Método completo que ajusta todos os lambdas baseado nas escalações.
        
        Args:
            home_team: Nome do time da casa
            away_team: Nome do time visitante
            escalacao_home: Lista de 11 jogadores do time da casa
            escalacao_away: Lista de 11 jogadores do time visitante
            lambdas_base: Dicionário com lambdas base calculados pelo PoissonAnalyzer
        
        Returns:
            Dicionário com lambdas ajustados
        """
        # Calcular ratios para cada time
        ratios_home = self.calcular_lineup_ratios(home_team, escalacao_home)
        ratios_away = self.calcular_lineup_ratios(away_team, escalacao_away)
        
        # Ajustar lambdas
        return {
            'gols_home': lambdas_base.get('gols_home', 1.3) * ratios_home.off_ratio,
            'gols_away': lambdas_base.get('gols_away', 1.0) * ratios_away.off_ratio,
            'escanteios_home': lambdas_base.get('escanteios_home', 5.0) * ratios_home.cross_ratio,
            'escanteios_away': lambdas_base.get('escanteios_away', 4.5) * ratios_away.cross_ratio,
            'cartoes_home': lambdas_base.get('cartoes_home', 2.0) * ratios_home.foul_ratio,
            'cartoes_away': lambdas_base.get('cartoes_away', 2.0) * ratios_away.foul_ratio,
            'faltas_home': lambdas_base.get('faltas_home', 12.0) * ratios_home.foul_ratio,
            'faltas_away': lambdas_base.get('faltas_away', 12.0) * ratios_away.foul_ratio,
            
            # Manter outros lambdas
            'chutes_home': lambdas_base.get('chutes_home', 12.0),
            'chutes_away': lambdas_base.get('chutes_away', 11.0),
            'chutes_gol_home': lambdas_base.get('chutes_gol_home', 4.5),
            'chutes_gol_away': lambdas_base.get('chutes_gol_away', 4.0),
            
            # Metadados
            '_home_ratios': {
                'off': ratios_home.off_ratio,
                'cross': ratios_home.cross_ratio,
                'foul': ratios_home.foul_ratio
            },
            '_away_ratios': {
                'off': ratios_away.off_ratio,
                'cross': ratios_away.cross_ratio,
                'foul': ratios_away.foul_ratio
            }
        }
    
    def get_top_offensive_players(self, time: str, n: int = 5) -> List[PlayerIndices]:
        """Retorna os jogadores mais ofensivos de um time."""
        indices = self.get_team_indices(time)
        return sorted(indices, key=lambda x: x.off_index, reverse=True)[:n]
    
    def get_top_crossing_players(self, time: str, n: int = 5) -> List[PlayerIndices]:
        """Retorna os jogadores com maior índice de cruzamento."""
        indices = self.get_team_indices(time)
        return sorted(indices, key=lambda x: x.cross_index, reverse=True)[:n]
    
    def get_most_aggressive_players(self, time: str, n: int = 5) -> List[PlayerIndices]:
        """Retorna os jogadores mais faltosos/agressivos."""
        indices = self.get_team_indices(time)
        return sorted(indices, key=lambda x: x.foul_index, reverse=True)[:n]


# ==================== TESTES ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testando PlayerModel (Issues 9-11)")
    print("=" * 60)
    
    model = PlayerModel()
    
    # Listar times disponíveis
    print(f"\n📋 Times disponíveis: {list(model.indices_por_time.keys())}")
    
    # Testar com Flamengo
    if "Flamengo" in model.indices_por_time:
        print("\n🔴⚫ Flamengo - Top 5 Ofensivos:")
        for i, player in enumerate(model.get_top_offensive_players("Flamengo", 5), 1):
            print(f"  {i}. {player.nome}: off_index={player.off_index:.3f}, gols/90={player.gols_por_90:.2f}")
        
        print("\n🔴⚫ Flamengo - Top 5 Cruzadores:")
        for i, player in enumerate(model.get_top_crossing_players("Flamengo", 5), 1):
            print(f"  {i}. {player.nome}: cross_index={player.cross_index:.3f}")
        
        print("\n🔴⚫ Flamengo - Top 5 Mais Faltosos:")
        for i, player in enumerate(model.get_most_aggressive_players("Flamengo", 5), 1):
            print(f"  {i}. {player.nome}: foul_index={player.foul_index:.3f}, cartoes/90={player.cartoes_por_90:.2f}")
        
        # Simular escalação
        print("\n📋 Simulando escalação (primeiros 11 jogadores):")
        jogadores_flamengo = [j.nome for j in model.get_team_indices("Flamengo")[:11]]
        print(f"  Escalação: {jogadores_flamengo[:5]}...")
        
        ratios = model.calcular_lineup_ratios("Flamengo", jogadores_flamengo)
        print(f"\n📊 Ratios da Escalação:")
        print(f"  off_ratio: {ratios.off_ratio:.3f} (impacto em gols)")
        print(f"  cross_ratio: {ratios.cross_ratio:.3f} (impacto em escanteios)")
        print(f"  foul_ratio: {ratios.foul_ratio:.3f} (impacto em cartões)")
        
        # Testar ajuste de lambdas
        print("\n🎯 Testando ajuste de lambdas:")
        lambdas_base = {
            'gols_home': 1.5,
            'escanteios_home': 6.0,
            'cartoes_home': 2.0,
            'faltas_home': 12.0
        }
        
        ajustados = model.ajustar_lambdas(
            lambda_goals=lambdas_base['gols_home'],
            lambda_corners=lambdas_base['escanteios_home'],
            lambda_cards=lambdas_base['cartoes_home'],
            lambda_fouls=lambdas_base['faltas_home'],
            ratios=ratios
        )
        
        print(f"  λ Gols: {lambdas_base['gols_home']:.2f} → {ajustados.lambda_goals:.2f} (x{ajustados.off_adjustment:.2f})")
        print(f"  λ Escanteios: {lambdas_base['escanteios_home']:.1f} → {ajustados.lambda_corners:.1f} (x{ajustados.cross_adjustment:.2f})")
        print(f"  λ Cartões: {lambdas_base['cartoes_home']:.1f} → {ajustados.lambda_cards:.1f} (x{ajustados.foul_adjustment:.2f})")
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
