"""
Busca dados de escanteios dos times via SofaScore.
Coleta estatísticas de escanteios por partida e calcula médias.
"""
import json
import time
import random
import requests
from pathlib import Path
from typing import Dict, List

BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 1.5
MAX_DELAY = 2.5
TIMEOUT = 25

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# IDs dos times do Brasileirão (CORRIGIDOS)
TIMES_BRASILEIRAO = {
    'Flamengo': 5981,
    'Palmeiras': 1963,
    'Botafogo': 1958,
    'São Paulo': 1981,
    'Corinthians': 1957,  # Corrigido
    'Atlético-MG': 1977,
    'Grêmio': 5926,
    'Fluminense': 1961,   # Corrigido
    'Cruzeiro': 1954,
    'Vasco': 1974,        # Corrigido
    'Internacional': 1966,
    'Bahia': 1955,        # Corrigido
    'RB Bragantino': 1999,
    'Athletico-PR': 1936, # Corrigido
    'Fortaleza': 1965,    # Corrigido
    'Juventude': 1980,    # Corrigido
    'Vitória': 1962,      # Corrigido
    'Cuiabá': 35023,      # Corrigido
    'Atlético-GO': 7315,  # Corrigido
    'Criciúma': 1956      # Corrigido
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


def buscar_estatisticas_time(team_id: int) -> Dict:
    """
    Busca estatísticas agregadas do time na temporada.
    Inclui escanteios, chutes, posse, etc.
    """
    _delay()
    url = f"{BASE_URL}/team/{team_id}/unique-tournament/325/season/58766/statistics/overall"
    
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            print(f"⚠️  Estatísticas time {team_id}: status {r.status_code}")
            return {}
        
        data = r.json()
        stats = data.get('statistics', {})
        
        return stats
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return {}


def buscar_estatisticas_partida(event_id: int, team_id: int, is_home: bool) -> Dict:
    """
    Busca estatísticas de uma partida específica.
    Retorna escanteios do time especificado.
    """
    _delay()
    url = f"{BASE_URL}/event/{event_id}/statistics"
    
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            return {}
        
        data = r.json()
        
        escanteios = 0
        chutes = 0
        posse = 50
        
        for period in data.get('statistics', []):
            if period.get('period') == 'ALL':
                for group in period.get('groups', []):
                    for item in group.get('statisticsItems', []):
                        name = item.get('name', '').lower()
                        if 'corner' in name:
                            val = item.get('home', 0) if is_home else item.get('away', 0)
                            escanteios = int(val) if str(val).isdigit() else 0
                        elif 'total shots' in name:
                            val = item.get('home', 0) if is_home else item.get('away', 0)
                            chutes = int(val) if str(val).isdigit() else 0
                        elif 'possession' in name:
                            val = item.get('home', 50) if is_home else item.get('away', 50)
                            try:
                                posse = float(str(val).replace('%', ''))
                            except:
                                posse = 50
        
        return {
            'escanteios': escanteios,
            'chutes': chutes,
            'posse': posse
        }
    
    except Exception as e:
        return {}


def buscar_ultimas_partidas_com_stats(team_id: int, n_partidas: int = 10) -> List[Dict]:
    """
    Busca últimas partidas de um time com estatísticas detalhadas.
    """
    _delay()
    url = f"{BASE_URL}/team/{team_id}/events/last/0"
    
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        
        data = r.json()
        events = data.get('events', [])[:n_partidas]
        
        partidas = []
        for ev in events:
            event_id = ev.get('id')
            home_team = ev.get('homeTeam', {})
            away_team = ev.get('awayTeam', {})
            is_home = home_team.get('id') == team_id
            
            # Buscar estatísticas da partida
            stats = buscar_estatisticas_partida(event_id, team_id, is_home)
            
            partidas.append({
                'event_id': event_id,
                'adversario': away_team.get('name') if is_home else home_team.get('name'),
                'casa_fora': 'casa' if is_home else 'fora',
                'escanteios': stats.get('escanteios', 0),
                'chutes': stats.get('chutes', 0),
                'posse': stats.get('posse', 50),
            })
            
            print(f"      📊 {partidas[-1]['adversario']}: {stats.get('escanteios', 0)} escanteios")
        
        return partidas
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def main():
    """Busca escanteios de todos os times e salva dados."""
    
    # Carregar times existentes
    times_path = Path('data/times.json')
    with open(times_path, 'r', encoding='utf-8') as f:
        times = json.load(f)
    
    times_dict = {t['nome']: t for t in times}
    
    print("🔄 Buscando estatísticas de escanteios...")
    print("=" * 60)
    
    for nome, team_id in TIMES_BRASILEIRAO.items():
        print(f"\n🚩 {nome} (ID {team_id})...")
        
        # Buscar últimas 10 partidas com stats
        partidas = buscar_ultimas_partidas_com_stats(team_id, 10)
        
        if not partidas:
            print(f"   ⚠️  Sem dados encontrados")
            continue
        
        # Calcular médias
        escanteios_list = [p['escanteios'] for p in partidas if p['escanteios'] > 0]
        chutes_list = [p['chutes'] for p in partidas if p['chutes'] > 0]
        
        escanteios_media = sum(escanteios_list) / len(escanteios_list) if escanteios_list else 0
        chutes_media = sum(chutes_list) / len(chutes_list) if chutes_list else 0
        
        # Separar casa/fora
        escanteios_casa = [p['escanteios'] for p in partidas if p['casa_fora'] == 'casa' and p['escanteios'] > 0]
        escanteios_fora = [p['escanteios'] for p in partidas if p['casa_fora'] == 'fora' and p['escanteios'] > 0]
        
        escanteios_casa_media = sum(escanteios_casa) / len(escanteios_casa) if escanteios_casa else 0
        escanteios_fora_media = sum(escanteios_fora) / len(escanteios_fora) if escanteios_fora else 0
        
        print(f"   📊 Média escanteios: {escanteios_media:.1f} (Casa: {escanteios_casa_media:.1f} | Fora: {escanteios_fora_media:.1f})")
        print(f"   👟 Média chutes: {chutes_media:.1f}")
        
        # Atualizar time
        if nome in times_dict:
            times_dict[nome]['escanteios_media'] = round(escanteios_media, 2)
            times_dict[nome]['escanteios_casa_media'] = round(escanteios_casa_media, 2)
            times_dict[nome]['escanteios_fora_media'] = round(escanteios_fora_media, 2)
            times_dict[nome]['chutes_media'] = round(chutes_media, 2)
            times_dict[nome]['partidas_stats'] = partidas
    
    # Salvar
    times_atualizados = list(times_dict.values())
    with open(times_path, 'w', encoding='utf-8') as f:
        json.dump(times_atualizados, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("🎉 Concluído!")
    print(f"   💾 Times atualizados: {len(times_atualizados)}")


if __name__ == '__main__':
    main()
