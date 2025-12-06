"""
Sistema completo de scraping do SofaScore para jogadores do Brasileirão
Busca estatísticas detalhadas e atualizadas dos jogadores

AVISO: Uso educacional apenas. Não comercializar.
"""

import requests
import json
import time
import os
from datetime import datetime

# Diretórios
data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')
times_path = os.path.join(data_dir, 'times.json')
cache_path = os.path.join(data_dir, 'cache_sofascore.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Origin': 'https://www.sofascore.com',
    'Referer': 'https://www.sofascore.com/',
}

# IDs dos times do Brasileirão no SofaScore
TIMES_BRASILEIRAO_IDS = {
    'Flamengo': 5981,
    'Palmeiras': 1963,
    'Corinthians': 1957,
    'São Paulo': 1981,
    'Grêmio': 5926,
    'Internacional': 1966,
    'Fluminense': 1961,
    'Atlético Mineiro': 1977,
    'Cruzeiro': 1954,
    'Botafogo': 1958,
    'Vasco da Gama': 1974,
    'Santos': 1968,
    'Athletico Paranaense': 1959,
    'Bahia': 1955,
    'Fortaleza': 2020,
    'Bragantino': 1999,
    'Cuiabá': 21982,
    'Juventude': 1980,
    'Vitória': 1962,
    'Atlético Goianiense': 2001,
}

# ID da temporada 2025 do Brasileirão
SEASON_ID = 72034  # Brasileirão 2025
TOURNAMENT_ID = 325  # Brasileirão Série A

def buscar_elenco_time(time_nome, time_id):
    """Busca o elenco completo de um time"""
    try:
        url = f"https://api.sofascore.com/api/v1/team/{time_id}/players"
        
        print(f"🔍 Buscando elenco: {time_nome}...", end=" ")
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            jogadores = []
            
            if 'players' in data:
                for item in data['players']:
                    player = item.get('player', {})
                    
                    # URL da foto do jogador no SofaScore
                    player_id = player.get('id')
                    foto_url = f"https://api.sofascore.com/api/v1/player/{player_id}/image" if player_id else None
                    
                    jogador = {
                        'id': player_id,
                        'nome': player.get('name', 'Desconhecido'),
                        'time': time_nome,
                        'posicao': traduzir_posicao(player.get('position', '')),
                        'foto_url': foto_url,
                    }
                    jogadores.append(jogador)
                
                print(f"✅ {len(jogadores)} jogadores")
                return jogadores
        
        print(f"❌ Erro {response.status_code}")
        return []
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return []

def buscar_estatisticas_jogador(player_id, player_name):
    """Busca estatísticas detalhadas de um jogador"""
    try:
        # Endpoint de estatísticas do jogador por temporada e torneio
        url = f"https://api.sofascore.com/api/v1/player/{player_id}/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/statistics/overall"
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extrair estatísticas
            stats = data.get('statistics', {})
            
            if not stats:
                return None
            
            # Extrair TODAS as estatísticas disponíveis no SofaScore
            # Capturar também a URL da foto do jogador
            player_info = data.get('player', {})
            player_id = player_info.get('id')
            foto_url = f"https://api.sofascore.com/api/v1/player/{player_id}/image" if player_id else None
            
            return {
                # Foto
                'foto_url': foto_url,
                # Básicas
                'gols': stats.get('goals', 0) or 0,
                'assistencias': stats.get('assists', 0) or 0,
                'partidas': stats.get('appearances', 0) or 0,
                'minutos_jogados': stats.get('minutesPlayed', 0) or 0,
                # Cartões
                'cartoes_amarelos': stats.get('yellowCards', 0) or 0,
                'cartoes_vermelhos': stats.get('redCards', 0) or 0,
                # Faltas
                'faltas_cometidas': stats.get('fouls', 0) or 0,
                'faltas_sofridas': stats.get('wasFouled', 0) or 0,
                # Finalização
                'chutes': stats.get('totalShots', 0) or 0,
                'chutes_no_gol': stats.get('shotsOnTarget', 0) or 0,
                'grandes_chances_perdidas': stats.get('bigChanceMissed', 0) or 0,
                'grandes_chances_criadas': stats.get('bigChanceCreated', 0) or 0,
                'gols_esperados': stats.get('expectedGoals', 0.0) or 0.0,
                'conversao_gols': stats.get('goalConversionPercentage', 0.0) or 0.0,
                # Defesa
                'desarmes': stats.get('tackles', 0) or 0,
                'interceptacoes': stats.get('interceptions', 0.0) or 0.0,
                'defesas': stats.get('saves', 0) or 0,
                'gols_sofridos': stats.get('goalsConceded', 0) or 0,
                # Passes
                'passes_certos': stats.get('accuratePasses', 0.0) or 0.0,
                'total_passes': stats.get('totalPasses', 0) or 0,
                'passes_decisivos': stats.get('keyPasses', 0) or 0,
                'assistencias_esperadas': stats.get('expectedAssists', 0.0) or 0.0,
                'passes_longos_certos': stats.get('accurateLongBalls', 0.0) or 0.0,
                'cruzamentos_certos': stats.get('accurateCrosses', 0.0) or 0.0,
                # Dribles e duelos
                'dribles_certos': stats.get('successfulDribbles', 0.0) or 0.0,
                'total_dribles': stats.get('totalDribbles', 0) or 0,
                'duelos_ganhos': stats.get('duelsWon', 0) or 0,
                'duelos_totais': stats.get('duelsTotal', 0) or 0,
                'duelos_aereos_ganhos': stats.get('aerialDuelsWon', 0) or 0,
                'duelos_terrestres_ganhos': stats.get('groundDuelsWon', 0) or 0,
                # Posse e erros
                'posse_perdida': stats.get('possessionLost', 0) or 0,
                'erros_finalizacao': stats.get('errorLeadToShot', 0) or 0,
                'erros_gol': stats.get('errorLeadToGoal', 0) or 0,
                'impedimentos': stats.get('offsides', 0) or 0,
                # Pênaltis
                'penaltis_marcados': stats.get('penaltyGoals', 0) or 0,
                'penaltis_sofridos': stats.get('penaltyWon', 0) or 0,
                'penaltis_cometidos': stats.get('penaltyConceded', 0) or 0,
                # Performance
                'rating': stats.get('rating', 0.0) or 0.0,
            }
        
        return None
        
    except Exception as e:
        return None

def traduzir_posicao(posicao):
    """Traduz posição do inglês para português"""
    traducoes = {
        'G': 'Goleiro',
        'D': 'Zagueiro',
        'M': 'Meia',
        'F': 'Atacante',
        'Goalkeeper': 'Goleiro',
        'Defender': 'Zagueiro',
        'Midfielder': 'Meia',
        'Forward': 'Atacante',
    }
    return traducoes.get(posicao, posicao or 'Desconhecida')

def carregar_jogadores_existentes():
    """Carrega jogadores já cadastrados"""
    if os.path.exists(jogadores_path):
        with open(jogadores_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def salvar_jogadores(jogadores):
    """Salva jogadores no arquivo JSON"""
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=2)

def atualizar_estatisticas_brasileirao(times_selecionados=None, atualizar_existentes=True):
    """
    Atualiza estatísticas dos jogadores do Brasileirão
    
    Args:
        times_selecionados: Lista de nomes de times ou None para todos
        atualizar_existentes: Se True, atualiza jogadores já cadastrados
    """
    
    print("⚽ ATUALIZADOR DE ESTATÍSTICAS - SOFASCORE")
    print("=" * 70)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🏆 Temporada: Brasileirão 2025")
    print("=" * 70)
    print()
    
    # Determinar quais times processar
    times_processar = times_selecionados if times_selecionados else list(TIMES_BRASILEIRAO_IDS.keys())
    
    jogadores_existentes = carregar_jogadores_existentes()
    jogadores_dict = {f"{j['nome']}_{j['time']}": j for j in jogadores_existentes}
    
    total_times = len(times_processar)
    total_jogadores_processados = 0
    total_jogadores_atualizados = 0
    total_jogadores_novos = 0
    
    for idx, time_nome in enumerate(times_processar, 1):
        if time_nome not in TIMES_BRASILEIRAO_IDS:
            print(f"⚠️  Time '{time_nome}' não encontrado no SofaScore")
            continue
        
        print(f"\n[{idx}/{total_times}] {time_nome}")
        print("-" * 70)
        
        time_id = TIMES_BRASILEIRAO_IDS[time_nome]
        
        # Buscar elenco
        jogadores_time = buscar_elenco_time(time_nome, time_id)
        time.sleep(1)  # Delay entre requisições
        
        if not jogadores_time:
            continue
        
        # Buscar estatísticas de cada jogador
        for jog_idx, jogador in enumerate(jogadores_time, 1):
            player_id = jogador.get('id')
            player_name = jogador['nome']
            
            print(f"   [{jog_idx}/{len(jogadores_time)}] {player_name}...", end=" ")
            
            # Buscar estatísticas
            stats = buscar_estatisticas_jogador(player_id, player_name)
            
            if stats:
                jogador.update(stats)
                print(f"✅ {stats['gols']}G {stats['assistencias']}A {stats['partidas']}J")
            else:
                # Adicionar estatísticas zeradas mas manter foto_url
                foto_url = jogador.get('foto_url')
                jogador.update({
                    'foto_url': foto_url,
                    'gols': 0, 'assistencias': 0, 'cartoes_amarelos': 0,
                    'cartoes_vermelhos': 0, 'faltas_cometidas': 0,
                    'faltas_sofridas': 0, 'chutes': 0, 'chutes_no_gol': 0,
                    'desarmes': 0, 'partidas': 0, 'minutos_jogados': 0,
                    'rating': 0.0
                })
                print("⚪ Sem dados")
            
            # Atualizar ou adicionar jogador
            chave = f"{player_name}_{time_nome}"
            if chave in jogadores_dict:
                if atualizar_existentes:
                    jogadores_dict[chave].update(jogador)
                    total_jogadores_atualizados += 1
            else:
                jogadores_dict[chave] = jogador
                total_jogadores_novos += 1
            
            total_jogadores_processados += 1
            
            # Delay entre jogadores
            time.sleep(0.5)
    
    # Salvar todos os jogadores
    todos_jogadores = list(jogadores_dict.values())
    salvar_jogadores(todos_jogadores)
    
    # Resumo
    print("\n" + "=" * 70)
    print("🎉 ATUALIZAÇÃO CONCLUÍDA!")
    print("=" * 70)
    print(f"✅ Jogadores processados: {total_jogadores_processados}")
    print(f"🆕 Jogadores novos: {total_jogadores_novos}")
    print(f"♻️  Jogadores atualizados: {total_jogadores_atualizados}")
    print(f"📊 Total no sistema: {len(todos_jogadores)}")
    print("=" * 70)

def menu_interativo():
    """Menu para escolher quais times atualizar"""
    print("\n📋 OPÇÕES DE ATUALIZAÇÃO:")
    print("1. Atualizar TODOS os times do Brasileirão")
    print("2. Atualizar apenas alguns times específicos")
    print("3. Atualizar apenas 1 time (teste rápido)")
    
    escolha = input("\nEscolha uma opção (1-3): ").strip()
    
    if escolha == "1":
        atualizar_estatisticas_brasileirao()
    
    elif escolha == "2":
        print("\nTimes disponíveis:")
        times_list = list(TIMES_BRASILEIRAO_IDS.keys())
        for i, time in enumerate(times_list, 1):
            print(f"{i}. {time}")
        
        indices = input("\nDigite os números dos times (separados por vírgula): ")
        indices_list = [int(i.strip())-1 for i in indices.split(',') if i.strip().isdigit()]
        times_selecionados = [times_list[i] for i in indices_list if 0 <= i < len(times_list)]
        
        if times_selecionados:
            atualizar_estatisticas_brasileirao(times_selecionados)
        else:
            print("❌ Nenhum time válido selecionado")
    
    elif escolha == "3":
        print("\nTimes disponíveis:")
        times_list = list(TIMES_BRASILEIRAO_IDS.keys())
        for i, time in enumerate(times_list[:5], 1):
            print(f"{i}. {time}")
        
        idx = input("\nEscolha um time (1-5): ").strip()
        if idx.isdigit() and 1 <= int(idx) <= 5:
            time_selecionado = [times_list[int(idx)-1]]
            atualizar_estatisticas_brasileirao(time_selecionado)
        else:
            print("❌ Opção inválida")
    
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    try:
        menu_interativo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
