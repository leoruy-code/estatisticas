import sys, json, time
from typing import Dict, Any, List
import requests

sys.path.insert(0, 'src')
from config_api_football import get_next_key, BASE_URL
from brasileirao_ids_2025 import BRASILEIRAO_SERIE_A_2025_TEAM_IDS

SEASON = 2025
OUTPUT_JOGADORES = 'data/jogadores.json'
OUTPUT_TIMES = 'data/times.json'

def fetch_players_with_stats(team_id: int, season: int) -> List[Dict[str, Any]]:
    players: List[Dict[str, Any]] = []
    page = 1
    while True:
        headers = {'x-apisports-key': get_next_key()}
        params = {'team': team_id, 'season': season, 'page': page}
        url = f"{BASE_URL}/players"
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()
        resp = data.get('response', [])
        if not resp:
            break
        for item in resp:
            player = item.get('player', {})
            stats_list = item.get('statistics', [])
            stats = stats_list[0] if stats_list else {}
            s_team = stats.get('team', {})
            s_games = stats.get('games', {})
            s_goals = stats.get('goals', {})
            s_shots = stats.get('shots', {})
            s_passing = stats.get('passes', {})
            s_dribbles = stats.get('dribbles', {})
            s_duels = stats.get('duels', {})
            s_defending = stats.get('tackles', {})
            s_cards = stats.get('cards', {})
            s_goalkeeping = stats.get('goals', {})

            players.append({
                'nome': player.get('name'),
                'apelido': player.get('firstname'),
                'sobrenome': player.get('lastname'),
                'idade': player.get('age'),
                'nacionalidade': player.get('nationality'),
                'altura': player.get('height'),
                'peso': player.get('weight'),
                'numero_camisa': player.get('number'),
                'foto_url': player.get('photo'),
                'time': s_team.get('name'),
                'time_id': s_team.get('id', team_id),
                'season': season,
                'partidas': s_games.get('appearences') or 0,
                'minutos': s_games.get('minutes') or 0,
                'posicao': s_games.get('position'),
                'titular': s_games.get('lineups') or 0,
                'rating': float(s_games.get('rating') or 0),
                'gols': s_goals.get('total') or 0,
                'assistencias': s_goals.get('assists') or 0,
                'chutes_total': s_shots.get('total') or 0,
                'chutes_no_gol': s_shots.get('on') or 0,
                'passes_total': s_passing.get('total') or 0,
                'passes_chave': s_passing.get('key') or 0,
                'precisao_passes': s_passing.get('accuracy'),
                'dribles_sucesso': s_dribbles.get('success') or 0,
                'dribles_tentados': s_dribbles.get('attempts') or 0,
                'duelos_ganhos': s_duels.get('won') or 0,
                'duelos_total': s_duels.get('total') or 0,
                'desarmes': s_defending.get('total') or 0,
                'intercepcoes': s_defending.get('interceptions') or 0,
                'bloqueios': s_defending.get('blocks') or 0,
                'cartoes_amarelos': s_cards.get('yellow') or 0,
                'cartoes_vermelhos': s_cards.get('red') or 0,
                'goleiro_defesas': stats.get('goalkeeper', {}).get('saves'),
                'gols_sofridos': stats.get('goals', {}).get('against', {}).get('total'),
                'clean_sheets': stats.get('goals', {}).get('conceded', 0),
            })
        page += 1
        time.sleep(0.3)
    return players

def build_times_structure(team_map: Dict[str, int]) -> List[Dict[str, Any]]:
    times = []
    for name, tid in team_map.items():
        times.append({'id': tid, 'nome': name, 'season': SEASON, 'jogadores': []})
    return times

def main():
    team_map = BRASILEIRAO_SERIE_A_2025_TEAM_IDS
    times = build_times_structure(team_map)
    all_players: List[Dict[str, Any]] = []

    for t in times:
        tid = t['id']
        name = t['nome']
        print(f"Coletando {name} (id {tid})...")
        ps = fetch_players_with_stats(tid, SEASON)
        t['jogadores'] = [p['nome'] for p in ps if p.get('nome')]
        all_players.extend(ps)
        print(f" -> {len(ps)} jogadores")

    # Filtrar apenas season=2025
    all_players_2025 = [p for p in all_players if p.get('season') == SEASON]

    with open(OUTPUT_JOGADORES, 'w', encoding='utf-8') as f:
        json.dump(all_players_2025, f, ensure_ascii=False, indent=2)
    with open(OUTPUT_TIMES, 'w', encoding='utf-8') as f:
        json.dump(times, f, ensure_ascii=False, indent=2)

    print(f"Salvo {len(all_players_2025)} jogadores em {OUTPUT_JOGADORES}")
    print(f"Salvo {len(times)} times em {OUTPUT_TIMES}")

if __name__ == '__main__':
    main()
