"""
Busca estatísticas de jogadores via SofaScore API.
Atualiza jogadores.json com stats da temporada 2025.
"""
import json
import time
import random
import requests
from pathlib import Path

BASE_URL = "https://api.sofascore.com/api/v1"
MIN_DELAY = 1.0
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


def buscar_stats_jogador(player_id: int) -> dict:
    """
    Busca estatísticas agregadas do jogador via endpoint de estatísticas.
    Tenta múltiplos endpoints para maximizar cobertura.
    """
    stats = {}
    
    # Endpoint 1: Estatísticas gerais do jogador (última temporada)
    _delay()
    url = f"{BASE_URL}/player/{player_id}/unique-tournament/325/season/58766/statistics/overall"
    try:
        r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            stats_data = data.get('statistics', {})
            stats.update(extrair_stats(stats_data))
    except Exception as e:
        pass
    
    # Endpoint 2: Estatísticas da temporada atual (Brasileirão 2025 - season 72034)
    if not stats:
        _delay()
        url = f"{BASE_URL}/player/{player_id}/unique-tournament/325/season/72034/statistics/overall"
        try:
            r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                stats_data = data.get('statistics', {})
                stats.update(extrair_stats(stats_data))
        except Exception as e:
            pass
    
    # Endpoint 3: Estatísticas agregadas de todas as competições
    if not stats:
        _delay()
        url = f"{BASE_URL}/player/{player_id}/statistics/seasons"
        try:
            r = requests.get(url, headers=_headers(), timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                # Pegar a temporada mais recente
                seasons = data.get('uniqueTournamentSeasons', [])
                for tournament in seasons:
                    for season in tournament.get('seasons', []):
                        if season.get('year') == '24/25' or season.get('year') == '2025':
                            season_id = season.get('id')
                            tournament_id = tournament.get('uniqueTournament', {}).get('id')
                            if season_id and tournament_id:
                                _delay()
                                url2 = f"{BASE_URL}/player/{player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall"
                                r2 = requests.get(url2, headers=_headers(), timeout=TIMEOUT)
                                if r2.status_code == 200:
                                    stats_data = r2.json().get('statistics', {})
                                    stats.update(extrair_stats(stats_data))
                                    if stats.get('partidas', 0) > 0:
                                        return stats
        except Exception as e:
            pass
    
    return stats


def extrair_stats(data: dict) -> dict:
    """Extrai estatísticas relevantes do JSON retornado pela API."""
    return {
        'partidas': data.get('appearances', 0) or data.get('matches', 0) or 0,
        'minutos_jogados': data.get('minutesPlayed', 0) or 0,
        'gols': data.get('goals', 0) or 0,
        'assistencias': data.get('assists', 0) or data.get('goalAssist', 0) or 0,
        'gols_esperados': data.get('expectedGoals', 0) or 0,
        'assistencias_esperadas': data.get('expectedAssists', 0) or 0,
        'chutes': data.get('totalShots', 0) or data.get('shotsTotal', 0) or 0,
        'chutes_no_gol': data.get('shotsOnTarget', 0) or data.get('onTargetScoringAttempt', 0) or 0,
        'grandes_chances_criadas': data.get('bigChancesCreated', 0) or 0,
        'grandes_chances_perdidas': data.get('bigChancesMissed', 0) or 0,
        'total_passes': data.get('totalPasses', 0) or data.get('accuratePass', 0) or 0,
        'passes_certos': data.get('accuratePasses', 0) or data.get('accuratePass', 0) or 0,
        'passes_decisivos': data.get('keyPasses', 0) or 0,
        'passes_longos_certos': data.get('accurateLongBalls', 0) or 0,
        'cruzamentos_certos': data.get('accurateCrosses', 0) or 0,
        'desarmes': data.get('tackles', 0) or data.get('totalTackle', 0) or 0,
        'interceptacoes': data.get('interceptions', 0) or 0,
        'duelos_ganhos': data.get('groundDuelsWon', 0) or data.get('duelWon', 0) or 0,
        'duelos_totais': data.get('groundDuels', 0) or data.get('totalDuels', 0) or 0,
        'duelos_aereos_ganhos': data.get('aerialDuelsWon', 0) or data.get('aerialWon', 0) or 0,
        'dribles_certos': data.get('successfulDribbles', 0) or 0,
        'faltas_cometidas': data.get('fouls', 0) or data.get('foulCommit', 0) or 0,
        'faltas_sofridas': data.get('wasFouled', 0) or 0,
        'cartoes_amarelos': data.get('yellowCards', 0) or 0,
        'cartoes_vermelhos': data.get('redCards', 0) or 0,
        'impedimentos': data.get('offsides', 0) or 0,
        'penaltis_marcados': data.get('penaltyGoals', 0) or data.get('penaltyScored', 0) or 0,
        'defesas': data.get('saves', 0) or 0,
        'rating': data.get('rating', 0) or 0,
    }


def main():
    # Carregar jogadores
    jogadores_path = Path('data/jogadores.json')
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    total = len(jogadores)
    atualizados = 0
    sem_stats = 0
    
    print(f"🔍 Buscando estatísticas para {total} jogadores...")
    print("=" * 60)
    
    for i, jogador in enumerate(jogadores, 1):
        player_id = jogador.get('sofascore_id')
        nome = jogador.get('nome', 'N/A')
        time = jogador.get('time', 'N/A')
        
        if not player_id:
            print(f"[{i}/{total}] ⚠️  {nome} ({time}) - sem sofascore_id")
            sem_stats += 1
            continue
        
        print(f"[{i}/{total}] 🔄 {nome} ({time})...", end=" ", flush=True)
        
        stats = buscar_stats_jogador(player_id)
        
        if stats and stats.get('partidas', 0) > 0:
            jogador.update(stats)
            atualizados += 1
            print(f"✅ {stats.get('partidas', 0)} partidas, {stats.get('gols', 0)} gols")
        else:
            print("❌ sem stats")
            sem_stats += 1
        
        # Salvar a cada 10 jogadores
        if i % 10 == 0:
            with open(jogadores_path, 'w', encoding='utf-8') as f:
                json.dump(jogadores, f, ensure_ascii=False, indent=2)
            print(f"   💾 Salvos {i} jogadores...")
    
    # Salvar final
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"🎉 Concluído!")
    print(f"   ✅ Atualizados: {atualizados}")
    print(f"   ❌ Sem stats: {sem_stats}")
    print(f"   📊 Total: {total}")


if __name__ == '__main__':
    main()
