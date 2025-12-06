"""
Busca dados de partidas dos times via SofaScore.
Coleta: resultados, gols marcados/sofridos, estatísticas por jogo.
Usado para calcular Defense Weakness real e forma recente (rolling windows).
"""
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from config_times import TIMES_BRASILEIRAO, BRASILEIRAO_TOURNAMENT_ID

BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 1.5
MAX_DELAY = 2.5
TIMEOUT = 25

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json',
        'Origin': 'https://www.sofascore.com',
        'Referer': 'https://www.sofascore.com/',
    }


def _delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def buscar_ultimas_partidas(team_id: int, n_partidas: int = 20) -> List[Dict]:
    """
    Busca as últimas N partidas de um time do Brasileirão.
    Retorna lista com: adversário, gols_pro, gols_contra, casa/fora, resultado.
    
    Filtros aplicados:
    - Apenas tournament.uniqueTournament.id == BRASILEIRAO_TOURNAMENT_ID (325)
    - Apenas status.type == "finished"
    - Limita a n_partidas APÓS aplicar os filtros
    """
    _delay()
    url = f"{BASE_URL}/team/{team_id}/events/last/0"
    
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            print(f"⚠️  team/{team_id}/events: status {r.status_code}")
            return []
        
        data = r.json()
        all_events = data.get('events', [])
        
        # 🎯 FILTRAR: Apenas Brasileirão e partidas finalizadas
        events_brasileirao = [
            ev for ev in all_events
            if ev.get('tournament', {}).get('uniqueTournament', {}).get('id') == BRASILEIRAO_TOURNAMENT_ID
            and ev.get('status', {}).get('type') == 'finished'
        ]
        
        # Limitar DEPOIS do filtro
        events = events_brasileirao[:n_partidas]
        
        partidas = []
        for ev in events:
            home_team = ev.get('homeTeam', {})
            away_team = ev.get('awayTeam', {})
            home_score = ev.get('homeScore', {}).get('current')
            away_score = ev.get('awayScore', {}).get('current')
            
            # 🎯 TRATAMENTO: None vs 0
            # Se score é None, ignorar partida (dados incompletos)
            if home_score is None or away_score is None:
                continue
            
            is_home = home_team.get('id') == team_id
            
            if is_home:
                gols_pro = home_score
                gols_contra = away_score
                adversario = away_team.get('name', 'N/A')
            else:
                gols_pro = away_score
                gols_contra = home_score
                adversario = home_team.get('name', 'N/A')
            
            # Determinar resultado
            if gols_pro > gols_contra:
                resultado = 'V'
            elif gols_pro < gols_contra:
                resultado = 'D'
            else:
                resultado = 'E'
            
            partidas.append({
                'adversario': adversario,
                'gols_pro': gols_pro,
                'gols_contra': gols_contra,
                'casa_fora': 'casa' if is_home else 'fora',
                'resultado': resultado,
                'data': ev.get('startTimestamp', 0),
                'torneio': ev.get('tournament', {}).get('name', ''),
            })
        
        return partidas
    
    except Exception as e:
        print(f"❌ Erro ao buscar partidas: {e}")
        return []


def buscar_estatisticas_partida(event_id: int) -> Dict:
    """Busca estatísticas detalhadas de uma partida específica."""
    _delay()
    url = f"{BASE_URL}/event/{event_id}/statistics"
    
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code != 200:
            return {}
        
        data = r.json()
        stats = {}
        
        for group in data.get('statistics', []):
            for stat in group.get('groups', []):
                for item in stat.get('statisticsItems', []):
                    name = item.get('name', '')
                    home_val = item.get('home', 0)
                    away_val = item.get('away', 0)
                    stats[f"{name}_home"] = home_val
                    stats[f"{name}_away"] = away_val
        
        return stats
    
    except Exception as e:
        return {}


def calcular_metricas_time(partidas: List[Dict], janela: int = None) -> Dict:
    """
    Calcula métricas agregadas de um time baseado nas partidas.
    
    Args:
        partidas: Lista de partidas
        janela: Número de partidas a considerar (None = todas)
    
    Returns:
        Dict com métricas: gols_marcados_media, gols_sofridos_media, forma, etc.
    """
    if janela:
        partidas = partidas[:janela]
    
    if not partidas:
        return {
            'gols_marcados_media': 0,
            'gols_sofridos_media': 0,
            'vitorias': 0,
            'empates': 0,
            'derrotas': 0,
            'forma_pontos': 0,
            'forma_percent': 0,
            'n_partidas': 0,
        }
    
    n = len(partidas)
    gols_marcados = sum(p['gols_pro'] for p in partidas)
    gols_sofridos = sum(p['gols_contra'] for p in partidas)
    vitorias = sum(1 for p in partidas if p['resultado'] == 'V')
    empates = sum(1 for p in partidas if p['resultado'] == 'E')
    derrotas = sum(1 for p in partidas if p['resultado'] == 'D')
    
    pontos = vitorias * 3 + empates
    max_pontos = n * 3
    
    return {
        'gols_marcados_media': gols_marcados / n,
        'gols_sofridos_media': gols_sofridos / n,
        'vitorias': vitorias,
        'empates': empates,
        'derrotas': derrotas,
        'forma_pontos': pontos,
        'forma_percent': pontos / max_pontos if max_pontos > 0 else 0,
        'n_partidas': n,
    }


def calcular_forma_multiplicador(metricas_recentes: Dict, metricas_temporada: Dict) -> float:
    """
    Calcula multiplicador de forma baseado na comparação entre forma recente e temporada.
    
    Fórmula: 1 + 0.2 * (zscore_recente_vs_temporada), clipped entre 0.8 e 1.2
    """
    if metricas_temporada['gols_marcados_media'] == 0:
        return 1.0
    
    # Comparar gols marcados recentes vs temporada
    ratio = metricas_recentes['gols_marcados_media'] / metricas_temporada['gols_marcados_media']
    
    # Ajustar para multiplicador centrado em 1
    mult = 1 + 0.3 * (ratio - 1)
    
    # Clipar entre 0.8 e 1.2
    return max(0.8, min(1.2, mult))


def main():
    """Busca partidas de todos os times e salva dados."""
    
    # Carregar times existentes
    times_path = Path('data/times.json')
    with open(times_path, 'r', encoding='utf-8') as f:
        times = json.load(f)
    
    # Criar dict por nome para atualização
    times_dict = {t['nome']: t for t in times}
    
    print("🔄 Buscando partidas dos times...")
    print("=" * 60)
    
    for nome, team_id in TIMES_BRASILEIRAO.items():
        print(f"\n⚽ {nome} (ID {team_id})...")
        
        # Buscar últimas 20 partidas
        partidas = buscar_ultimas_partidas(team_id, 20)
        
        if not partidas:
            print(f"   ⚠️  Sem partidas encontradas")
            continue
        
        # Calcular métricas para diferentes janelas
        metricas_5 = calcular_metricas_time(partidas, 5)
        metricas_10 = calcular_metricas_time(partidas, 10)
        metricas_20 = calcular_metricas_time(partidas, 20)
        
        # Calcular multiplicador de forma
        forma_mult = calcular_forma_multiplicador(metricas_5, metricas_20)
        
        print(f"   📊 Últimas 5: {metricas_5['vitorias']}V {metricas_5['empates']}E {metricas_5['derrotas']}D | Gols: {metricas_5['gols_marcados_media']:.1f} ⚽ / {metricas_5['gols_sofridos_media']:.1f} 🥅")
        print(f"   📊 Últimas 10: {metricas_10['vitorias']}V {metricas_10['empates']}E {metricas_10['derrotas']}D | Gols: {metricas_10['gols_marcados_media']:.1f} ⚽ / {metricas_10['gols_sofridos_media']:.1f} 🥅")
        print(f"   📈 Forma multiplicador: {forma_mult:.2f}")
        
        # Atualizar time com novos dados
        if nome in times_dict:
            times_dict[nome]['partidas'] = partidas
            times_dict[nome]['metricas_5'] = metricas_5
            times_dict[nome]['metricas_10'] = metricas_10
            times_dict[nome]['metricas_20'] = metricas_20
            times_dict[nome]['forma_multiplicador'] = forma_mult
            times_dict[nome]['gols_sofridos_media'] = metricas_20['gols_sofridos_media']
            times_dict[nome]['gols_marcados_media'] = metricas_20['gols_marcados_media']
        else:
            # Time novo
            times_dict[nome] = {
                'nome': nome,
                'id': team_id,
                'partidas': partidas,
                'metricas_5': metricas_5,
                'metricas_10': metricas_10,
                'metricas_20': metricas_20,
                'forma_multiplicador': forma_mult,
                'gols_sofridos_media': metricas_20['gols_sofridos_media'],
                'gols_marcados_media': metricas_20['gols_marcados_media'],
            }
    
    # Salvar times atualizados
    times_atualizados = list(times_dict.values())
    with open(times_path, 'w', encoding='utf-8') as f:
        json.dump(times_atualizados, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("🎉 Concluído!")
    print(f"   💾 Times atualizados: {len(times_atualizados)}")
    print(f"   📊 Arquivo: data/times.json")


if __name__ == '__main__':
    main()
