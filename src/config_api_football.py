# Configuração da API-Football
# Crie suas contas gratuitas em: https://www.api-football.com/
# Pegue as API Keys em: https://dashboard.api-football.com/

# Cole suas 5 API Keys abaixo (uma por linha)
API_KEYS = [
    "19609ed05eeecb540e2617416fb398da",
    "30d90214e6abd5b8abc0e7ccbdb06735",
    "509c3d34d5f37c5182b3467bd1004178",
    "4ff22ed4d8d1ba5b1ad751fa02c69da5",
    "7e5a860fe0d76444cf9384a4ecdcbce5",
]

# Configurações
BASE_URL = "https://v3.football.api-sports.io"
BRASILEIRAO_LEAGUE_ID = 71  # ID da Série A
SEASON = 2025  # Temporada 2025 disponível!

# Mapeamento de IDs dos times (será atualizado automaticamente)
TIMES_IDS = {}

# Controle de rotação das chaves
_current_key_index = 0

def get_next_key():
    """Retorna a próxima API key em rotação"""
    global _current_key_index
    key = API_KEYS[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    return key
