import json
from typing import List, Dict

class Jogador:
    def __init__(self, nome: str, time: str, 
                 # Informações básicas
                 foto_url: str = None,
                 # Estatísticas básicas
                 gols: int = 0, assistencias: int = 0, partidas: int = 0, minutos_jogados: int = 0,
                 # Cartões e disciplina
                 cartoes_amarelos: int = 0, cartoes_vermelhos: int = 0, 
                 # Faltas
                 faltas_cometidas: int = 0, faltas_sofridas: int = 0,
                 # Chutes e finalização
                 chutes: int = 0, chutes_no_gol: int = 0, grandes_chances_perdidas: int = 0,
                 grandes_chances_criadas: int = 0, gols_esperados: float = 0.0, conversao_gols: float = 0.0,
                 # Defesa
                 desarmes: int = 0, interceptacoes: float = 0.0, defesas: int = 0, gols_sofridos: int = 0,
                 # Passes
                 passes_certos: float = 0.0, total_passes: int = 0, passes_decisivos: int = 0,
                 assistencias_esperadas: float = 0.0, passes_longos_certos: float = 0.0,
                 cruzamentos_certos: float = 0.0,
                 # Dribles e duelos  
                 dribles_certos: float = 0.0, total_dribles: int = 0, duelos_ganhos: int = 0,
                 duelos_totais: int = 0, duelos_aereos_ganhos: int = 0, duelos_terrestres_ganhos: int = 0,
                 # Posse e erros
                 posse_perdida: int = 0, erros_finalizacao: int = 0, erros_gol: int = 0,
                 impedimentos: int = 0,
                 # Penaltis
                 penaltis_marcados: int = 0, penaltis_sofridos: int = 0, penaltis_cometidos: int = 0,
                 # Performance
                 rating: float = 0.0):
        self.nome = nome
        self.time = time
        self.foto_url = foto_url
        # Básicas
        self.gols = gols
        self.assistencias = assistencias
        self.partidas = partidas
        self.minutos_jogados = minutos_jogados
        # Cartões
        self.cartoes_amarelos = cartoes_amarelos
        self.cartoes_vermelhos = cartoes_vermelhos
        # Faltas
        self.faltas_cometidas = faltas_cometidas
        self.faltas_sofridas = faltas_sofridas
        # Finalização
        self.chutes = chutes
        self.chutes_no_gol = chutes_no_gol
        self.grandes_chances_perdidas = grandes_chances_perdidas
        self.grandes_chances_criadas = grandes_chances_criadas
        self.gols_esperados = gols_esperados
        self.conversao_gols = conversao_gols
        # Defesa
        self.desarmes = desarmes
        self.interceptacoes = interceptacoes
        self.defesas = defesas
        self.gols_sofridos = gols_sofridos
        # Passes
        self.passes_certos = passes_certos
        self.total_passes = total_passes
        self.passes_decisivos = passes_decisivos
        self.assistencias_esperadas = assistencias_esperadas
        self.passes_longos_certos = passes_longos_certos
        self.cruzamentos_certos = cruzamentos_certos
        # Dribles e duelos
        self.dribles_certos = dribles_certos
        self.total_dribles = total_dribles
        self.duelos_ganhos = duelos_ganhos
        self.duelos_totais = duelos_totais
        self.duelos_aereos_ganhos = duelos_aereos_ganhos
        self.duelos_terrestres_ganhos = duelos_terrestres_ganhos
        # Posse e erros
        self.posse_perdida = posse_perdida
        self.erros_finalizacao = erros_finalizacao
        self.erros_gol = erros_gol
        self.impedimentos = impedimentos
        # Pênaltis
        self.penaltis_marcados = penaltis_marcados
        self.penaltis_sofridos = penaltis_sofridos
        self.penaltis_cometidos = penaltis_cometidos
        # Performance
        self.rating = rating

    def to_dict(self) -> Dict:
        return self.__dict__

class Time:
    def __init__(self, nome: str, jogadores: List[Jogador] = None):
        self.nome = nome
        self.jogadores = jogadores if jogadores else []

    def to_dict(self) -> Dict:
        return {
            'nome': self.nome,
            'jogadores': [j.to_dict() for j in self.jogadores]
        }

class Partida:
    def __init__(self, time_a: Time, time_b: Time, escala_a: List[str], escala_b: List[str]):
        self.time_a = time_a
        self.time_b = time_b
        self.escala_a = escala_a  # nomes dos jogadores escalados
        self.escala_b = escala_b

    def to_dict(self) -> Dict:
        return {
            'time_a': self.time_a.to_dict(),
            'time_b': self.time_b.to_dict(),
            'escala_a': self.escala_a,
            'escala_b': self.escala_b
        }

# Funções utilitárias para salvar/carregar JSON
def salvar_json(obj, caminho):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)
