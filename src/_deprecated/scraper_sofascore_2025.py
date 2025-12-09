import json
import time
import random
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

HEADERS_POOL = [
    # Alguns user agents comuns
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

BASE_SOFA = "https://www.sofascore.com/pt/football/team"
OUTPUT_JOGADORES = "data/jogadores.json"
OUTPUT_TIMES = "data/times.json"

SESSION = requests.Session()
SESSION.timeout = 30


def get(url: str) -> requests.Response:
    headers = {"User-Agent": random.choice(HEADERS_POOL)}
    for attempt in range(3):
        try:
            resp = SESSION.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1.5 + attempt)
    return resp


def parse_team_players(team_slug: str, team_id: int) -> List[Dict[str, Any]]:
    url = f"{BASE_SOFA}/{team_slug}/{team_id}#tab:players"
    resp = get(url)
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")

    players: List[Dict[str, Any]] = []

    # Estruturas do Sofascore podem mudar; tentamos padrões comuns
    # Procurar cards de jogador
    cards = soup.select('[data-testid="player-card"]')
    for c in cards:
        name_el = c.select_one('[data-testid="player-name"]')
        pos_el = c.select_one('[data-testid="player-position"]')
        img_el = c.select_one('img')
        name = name_el.get_text(strip=True) if name_el else None
        pos = pos_el.get_text(strip=True) if pos_el else None
        foto = img_el.get('src') if img_el else None
        if name:
            players.append({
                'nome': name,
                'posicao': pos,
                'foto_url': foto,
                'season': 2025,
            })

    # Fallback: procurar links de profiles
    if not players:
        for a in soup.select('a[href*="/player/"]'):
            name = a.get_text(strip=True)
            if name and len(name) > 2:
                players.append({'nome': name, 'season': 2025})

    return players


def merge_save(team_name: str, team_id: int, players: List[Dict[str, Any]]):
    try:
        with open(OUTPUT_JOGADORES, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    except Exception:
        existing = []

    # remover jogadores antigos do mesmo time na mesma season
    existing = [j for j in existing if not (j.get('time') == team_name and j.get('season') == 2025)]

    for p in players:
        p['time'] = team_name
        p['time_id'] = team_id
        p.setdefault('partidas', 0)
        p.setdefault('gols', 0)
        p.setdefault('assistencias', 0)
        p.setdefault('rating', 0)

    existing.extend(players)

    with open(OUTPUT_JOGADORES, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    try:
        with open(OUTPUT_TIMES, 'r', encoding='utf-8') as f:
            times = json.load(f)
    except Exception:
        times = []

    # atualizar estrutura do time
    found = False
    for t in times:
        if t.get('id') == team_id:
            t['nome'] = team_name
            t['season'] = 2025
            t['jogadores'] = [p['nome'] for p in players if p.get('nome')]
            found = True
            break
    if not found:
        times.append({'id': team_id, 'nome': team_name, 'season': 2025, 'jogadores': [p['nome'] for p in players if p.get('nome')]})

    with open(OUTPUT_TIMES, 'w', encoding='utf-8') as f:
        json.dump(times, f, ensure_ascii=False, indent=2)


def run_single(team_name: str, team_slug: str, team_id: int):
    print(f"Coletando {team_name} do Sofascore...")
    players = parse_team_players(team_slug, team_id)
    print(f" -> {len(players)} jogadores")
    merge_save(team_name, team_id, players)


if __name__ == '__main__':
    # Piloto com Flamengo
    run_single('Flamengo', 'flamengo', 5981)
