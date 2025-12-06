"""
Configuração centralizada dos times do Brasileirão.
IDs do SofaScore (corrigidos e validados).

Usar este arquivo como fonte única de verdade para todos os scrapers.
"""

# IDs corretos do SofaScore - Brasileirão 2025
TIMES_BRASILEIRAO = {
    'Flamengo': 5981,
    'Palmeiras': 1963,
    'Botafogo': 1958,
    'São Paulo': 1981,
    'Corinthians': 1957,
    'Atlético-MG': 1977,
    'Grêmio': 5926,
    'Fluminense': 1961,
    'Cruzeiro': 1954,
    'Vasco': 1974,
    'Internacional': 1966,
    'Bahia': 1955,
    'RB Bragantino': 1999,
    'Athletico-PR': 1936,
    'Fortaleza': 1965,
    'Juventude': 1980,
    'Vitória': 1962,
    'Cuiabá': 35023,
    'Atlético-GO': 7315,
    'Criciúma': 1956
}

# ID do torneio Brasileirão no SofaScore
BRASILEIRAO_TOURNAMENT_ID = 325

# Temporada 2025
BRASILEIRAO_SEASON_2025 = 58766

# Mapeamento reverso (ID -> Nome)
TIMES_BY_ID = {v: k for k, v in TIMES_BRASILEIRAO.items()}


def get_team_name(team_id: int) -> str:
    """Retorna nome do time pelo ID."""
    return TIMES_BY_ID.get(team_id, f"Time #{team_id}")


def is_brasileirao_team(team_id: int) -> bool:
    """Verifica se o ID é de um time do Brasileirão."""
    return team_id in TIMES_BY_ID
