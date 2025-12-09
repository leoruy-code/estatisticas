"""
ETAPA 6 - Contexto da Partida

Ajustes baseados em fatores externos:
- Mando de campo
- Força relativa (diferença de ranking)
- Tipo de competição
- Importância do jogo
- Árbitro (opcional)
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class TipoCompeticao(Enum):
    """Tipos de competição com características diferentes."""
    PONTOS_CORRIDOS = "pontos_corridos"  # Brasileirão
    MATA_MATA = "mata_mata"               # Copa do Brasil, Libertadores
    GRUPO = "grupo"                       # Fase de grupos
    AMISTOSO = "amistoso"


class ImportanciaJogo(Enum):
    """Importância do jogo para os times."""
    NORMAL = 1.0
    ALTA = 1.1      # Clássico, briga por título
    DECISIVO = 1.2  # Jogo que decide título/rebaixamento
    BAIXA = 0.9     # Time já classificado/rebaixado


@dataclass
class MatchContext:
    """Contexto completo de uma partida."""
    
    # Básico
    mandante_id: int
    visitante_id: int
    league_id: int
    
    # Contexto
    competicao: TipoCompeticao = TipoCompeticao.PONTOS_CORRIDOS
    importancia: ImportanciaJogo = ImportanciaJogo.NORMAL
    
    # Diferença de ranking (positivo = mandante melhor)
    diferenca_ranking: float = 0.0
    
    # Escalação (IDs dos jogadores, se disponível)
    escalacao_mandante: Optional[list] = None
    escalacao_visitante: Optional[list] = None
    
    # Árbitro (pode influenciar cartões)
    arbitro_id: Optional[int] = None
    
    def get_fator_competicao(self) -> dict:
        """
        Retorna fatores de ajuste baseado no tipo de competição.
        
        Mata-mata: mais fechado, menos gols, mais cartões
        Pontos corridos: mais aberto
        """
        fatores = {
            TipoCompeticao.PONTOS_CORRIDOS: {
                'gols': 1.0,
                'cartoes': 1.0,
                'escanteios': 1.0
            },
            TipoCompeticao.MATA_MATA: {
                'gols': 0.90,      # Jogos mais travados
                'cartoes': 1.15,   # Mais cartões
                'escanteios': 1.05
            },
            TipoCompeticao.GRUPO: {
                'gols': 0.95,
                'cartoes': 1.05,
                'escanteios': 1.0
            },
            TipoCompeticao.AMISTOSO: {
                'gols': 1.1,       # Mais aberto
                'cartoes': 0.8,   # Menos cartões
                'escanteios': 1.0
            }
        }
        return fatores.get(self.competicao, fatores[TipoCompeticao.PONTOS_CORRIDOS])
    
    def get_fator_importancia(self) -> float:
        """Retorna multiplicador baseado na importância."""
        return self.importancia.value
    
    def get_fator_ranking(self) -> dict:
        """
        Ajuste baseado na diferença de ranking.
        
        Se mandante muito melhor: espera mais gols dele, menos do visitante
        """
        # diferenca_ranking positivo = mandante melhor
        # Vamos usar uma função sigmoid suave
        import math
        
        # Fator varia de 0.8 a 1.2
        fator_mandante = 1.0 + 0.1 * math.tanh(self.diferenca_ranking / 10)
        fator_visitante = 1.0 - 0.1 * math.tanh(self.diferenca_ranking / 10)
        
        return {
            'mandante': fator_mandante,
            'visitante': fator_visitante
        }
    
    def has_lineup(self) -> bool:
        """Verifica se há escalação disponível."""
        return (
            self.escalacao_mandante is not None and 
            self.escalacao_visitante is not None and
            len(self.escalacao_mandante) >= 11 and
            len(self.escalacao_visitante) >= 11
        )


class ContextAdjuster:
    """Aplica ajustes de contexto aos parâmetros."""
    
    def adjust_parameters(self, params: dict, context: MatchContext) -> dict:
        """
        Ajusta λ, μ, κ baseado no contexto.
        
        Args:
            params: Dict com lambda_mandante, lambda_visitante, etc.
            context: Contexto da partida
            
        Returns:
            Dict ajustado
        """
        # Fatores de competição
        f_comp = context.get_fator_competicao()
        
        # Fatores de ranking
        f_rank = context.get_fator_ranking()
        
        # Fator de importância (afeta principalmente cartões)
        f_imp = context.get_fator_importancia()
        
        # Aplicar ajustes
        adjusted = {
            'lambda_mandante': (
                params['lambda_mandante'] * 
                f_comp['gols'] * 
                f_rank['mandante']
            ),
            'lambda_visitante': (
                params['lambda_visitante'] * 
                f_comp['gols'] * 
                f_rank['visitante']
            ),
            'mu_mandante': (
                params['mu_mandante'] * 
                f_comp['cartoes'] * 
                f_imp
            ),
            'mu_visitante': (
                params['mu_visitante'] * 
                f_comp['cartoes'] * 
                f_imp
            ),
            'kappa_mandante': (
                params['kappa_mandante'] * 
                f_comp['escanteios']
            ),
            'kappa_visitante': (
                params['kappa_visitante'] * 
                f_comp['escanteios']
            )
        }
        
        return adjusted
