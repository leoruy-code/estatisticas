"""
Reseta a base (data/jogadores.json, data/times.json) e importa elencos por time via SofaScore.
Sem estatísticas — apenas jogadores corretamente em seus respectivos times.
"""
import json
import time
import random
import requests
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 1.5
MAX_DELAY = 3.0
TIMEOUT = 25
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

TIMES_BRASILEIRAO = {
    'Flamengo': 5981,
    'Palmeiras': 5957,
    'Botafogo': 1958,
    'São Paulo': 1981,
    'Corinthians': 5926,
    'Atlético-MG': 1947,
    'Grêmio': 5933,
    'Fluminense': 5930,
    'Cruzeiro': 1963,
    'Vasco': 5998,
    'Internacional': 5925,
    'Bahia': 1943,
    'RB Bragantino': 1999,
    'Athletico-PR': 1950,
    'Fortaleza': 1973,
    'Juventude': 1968,
    'Vitória': 1997,
    'Cuiabá': 24264,
    'Atlético-GO': 1957,
    'Criciúma': 1964
}

# Slugs conhecidos para times (ajuda ao buscar via página HTML quando necessário)
TEAM_SLUGS = {
    'Flamengo': 'flamengo',
    'Palmeiras': 'palmeiras',
    'Botafogo': 'botafogo',
    'São Paulo': 'sao-paulo',
    'Corinthians': 'corinthians',
    'Atlético-MG': 'atletico-mineiro',
    'Grêmio': 'gremio',
    'Fluminense': 'fluminense',
    'Cruzeiro': 'cruzeiro',
    'Vasco': 'vasco-da-gama',
    'Internacional': 'internacional',
    'Bahia': 'bahia',
    'RB Bragantino': 'red-bull-bragantino',
    'Athletico-PR': 'atletico-paranaense',
    'Fortaleza': 'fortaleza',
    'Juventude': 'juventude',
    'Vitória': 'vitoria',
    'Cuiabá': 'cuiaba',
    'Atlético-GO': 'atletico-goianiense',
    'Criciúma': 'criciuma'
}


def _headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json',
        'Origin': 'https://www.sofascore.com',
        'Referer': 'https://www.sofascore.com/',
    }


def _delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def team_players(team_id: int) -> List[Dict]:
    """Busca elenco do time via /team/{id}/players"""
    _delay()
    url = f"{BASE_URL}/team/{team_id}/players"
    r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"⚠️  {team_id}: status {r.status_code}")
        return []
    data = r.json()
    players = []
    for p in data.get('players', []):
        player = p.get('player', {})
        players.append({
            'nome': player.get('name'),
            'numero_camisa': player.get('jerseyNumber'),
            'posicao': player.get('position'),
            'nacionalidade': player.get('country', {}).get('alpha3Code'),
            'altura': player.get('height'),
            'idade': _calc_age(player.get('dateOfBirthTimestamp')),
            'time': None,  # preenchido ao decidir o time
            'time_id': None,  # preenchido ao decidir o time
            'season': 2025,
            'foto_url': f"https://img.sofascore.com/api/v1/player/{player.get('id')}/image" if player.get('id') else None,
            'sofascore_id': player.get('id')
        })
    return players


def team_players_html(team_name: str, team_id: int) -> List[Dict]:
    """Fallback: extrai elenco via página HTML do time no SofaScore.
    Busca JSON embutido (initialData) e/ou cards da aba de jogadores.
    """
    _delay()
    # URL canônica de time no sofascore (aba jogadores)
    base_slug = TEAM_SLUGS.get(team_name, team_name.lower().replace(' ', '-'))
    url = f"https://www.sofascore.com/team/football/{base_slug}/{team_id}#tab:players"
    r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"   ⚠️  HTML {team_id}: status {r.status_code}")
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    players = []

    # Tentar encontrar script com initialData que contém elenco
    for script in soup.find_all('script'):
        txt = script.string or ''
        if 'initialData' in txt and 'players' in txt:
            try:
                import re, json as pyjson
                m = re.search(r"initialData\s*=\s*(\{.*?\})\s*;", txt, re.S)
                if m:
                    data = pyjson.loads(m.group(1))
                    team = data.get('teamPage', {})
                    p_list = team.get('players', []) or team.get('squad', [])
                    for p in p_list:
                        player = p.get('player', p)
                        pid = player.get('id')
                        players.append({
                            'nome': player.get('name'),
                            'numero_camisa': player.get('jerseyNumber'),
                            'posicao': player.get('position'),
                            'nacionalidade': (player.get('country') or {}).get('alpha3Code'),
                            'altura': player.get('height'),
                            'idade': _calc_age(player.get('dateOfBirthTimestamp')),
                            'time': None,
                            'time_id': None,
                            'season': 2025,
                            'foto_url': f"https://img.sofascore.com/api/v1/player/{pid}/image" if pid else None,
                            'sofascore_id': pid
                        })
                    if players:
                        return players
            except Exception:
                pass

    # Fallback: coletar links de jogadores na página
    for a in soup.select('a[href*="/player/"]'):
        href = a.get('href')
        name = a.get_text(strip=True)
        try:
            pid = int(href.rstrip('/').split('/')[-1])
        except Exception:
            pid = None
        players.append({
            'nome': name or None,
            'numero_camisa': None,
            'posicao': None,
            'nacionalidade': None,
            'altura': None,
            'idade': None,
            'time': None,
            'time_id': None,
            'season': 2025,
            'foto_url': f"https://img.sofascore.com/api/v1/player/{pid}/image" if pid else None,
            'sofascore_id': pid
        })
    return players


def search_team_id_by_name(name: str) -> int:
    """Busca o ID correto do time via /search/all?q=NAME"""
    _delay()
    url = f"{BASE_URL}/search/all"
    queries = [name, name.replace('FC', '').strip(), name.replace('São', 'Sao'), name.replace('RB ', 'Red Bull ')]
    for q in queries:
        r = requests.get(url, headers=_headers(), params={'q': q}, timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        data = r.json()
        for res in data.get('results', []):
            if res.get('type') == 'team':
                ent = res.get('entity', {})
                nm = str(ent.get('name', ''))
                if name.lower() in nm.lower() or q.lower() in nm.lower():
                    return ent.get('id', 0)
    return 0


def _calc_age(ts):
    if not ts:
        return None
    from datetime import datetime
    b = datetime.fromtimestamp(ts)
    t = datetime.now()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def reset_base():
    with open('data/jogadores.json', 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    with open('data/times.json', 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print('🧹 Base resetada: jogadores.json e times.json vazios')


def importar_times(target_times: List[str]):
    # carregar atuais
    try:
        with open('data/jogadores.json', 'r', encoding='utf-8') as f:
            jogadores = json.load(f)
    except:
        jogadores = []
    try:
        with open('data/times.json', 'r', encoding='utf-8') as f:
            times = json.load(f)
    except:
        times = []

    for nome in target_times:
        team_id = TIMES_BRASILEIRAO.get(nome)
        if not team_id:
            print(f"❌ Time não mapeado: {nome}")
            continue
        print(f"\n⚽ {nome} (ID {team_id}) — importando elenco...")
        elenco = team_players(team_id)
        # Fallback: tentar descobrir ID correto se 404 ou vazio
        if not elenco:
            new_id = search_team_id_by_name(nome)
            if new_id and new_id != team_id:
                print(f"   🔁 ID atualizado via busca: {team_id} → {new_id}")
                team_id = new_id
                elenco = team_players(team_id)
                # Atualizar mapeamento para próximos usos
                TIMES_BRASILEIRAO[nome] = team_id
        # Fallback HTML quando retorno é suspeito (muito baixo)
        if not elenco or len(elenco) < 15:
            print("   🔎 Tentando fallback via HTML...")
            html_elenco = team_players_html(nome, team_id)
            if len(html_elenco) > len(elenco):
                elenco = html_elenco
        
        if not elenco:
            print(f"   ⚠️  Sem jogadores retornados")
            continue

        # ajustar time nos jogadores
        for j in elenco:
            j['time'] = nome
            j['time_id'] = team_id
            # limpar stats
            j['partidas'] = 0
            j['gols'] = 0
            j['assistencias'] = 0
            j['rating'] = 0

        # atualizar jogadores.json (remove anteriores desse time)
        jogadores = [j for j in jogadores if j.get('time') != nome]
        jogadores.extend(elenco)

        # atualizar times.json (lista de nomes)
        times = [t for t in times if t.get('nome') != nome]
        times.append({
            'id': team_id,
            'nome': nome,
            'season': 2025,
            'jogadores': [j['nome'] for j in elenco]
        })

        print(f"   ✅ {len(elenco)} jogadores importados")

        # salvar a cada time
        with open('data/jogadores.json', 'w', encoding='utf-8') as f:
            json.dump(jogadores, f, ensure_ascii=False, indent=2)
        with open('data/times.json', 'w', encoding='utf-8') as f:
            json.dump(times, f, ensure_ascii=False, indent=2)
        print("   💾 Arquivos atualizados")

    print("\n🎉 Concluído!")
    print(f"   Total de jogadores: {len(jogadores)}")
    print(f"   Total de times: {len(times)}")


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if not args:
        print('Uso: python src/reset_e_importar_times.py [NOMES_DE_TIMES...]')
        print('Sem argumentos: importa todos os 20 times do Brasileirão.')
        reset_base()
        # importa todos os times mapeados
        importar_times(list(TIMES_BRASILEIRAO.keys()))
    else:
        reset_base()
        importar_times(args)
