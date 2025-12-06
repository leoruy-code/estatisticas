#!/usr/bin/env python3
"""
Atualizador incremental - time por time com delay
Para evitar bloqueios do SofaScore
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from atualizar_sofascore import buscar_elenco_time, buscar_estatisticas_jogador, TIMES_BRASILEIRAO_IDS

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

def atualizar_time_especifico(nome_time, delay=2):
    """Atualiza um time específico com controle de rate limit"""
    
    print(f"\n🔄 ATUALIZANDO: {nome_time}")
    print("=" * 70)
    
    # Carregar jogadores atuais
    if os.path.exists(jogadores_path):
        with open(jogadores_path, 'r', encoding='utf-8') as f:
            jogadores = json.load(f)
    else:
        jogadores = []
    
    # Remover jogadores antigos deste time
    jogadores_outros_times = [j for j in jogadores if j.get('time') != nome_time]
    antes = len(jogadores)
    
    print(f"📊 Jogadores antes: {len(jogadores)}")
    print(f"🗑️  Removendo jogadores antigos do {nome_time}...")
    
    # Buscar elenco atualizado
    time_id = TIMES_BRASILEIRAO_IDS.get(nome_time)
    if not time_id:
        print(f"❌ Time não encontrado: {nome_time}")
        return
    
    print(f"🔍 Buscando elenco atualizado... ", end='', flush=True)
    elenco = buscar_elenco_time(nome_time, time_id)
    
    if not elenco:
        print(f"❌ Falha ao buscar elenco")
        return
    
    print(f"✅ {len(elenco)} jogadores encontrados")
    print()
    
    novos_jogadores = []
    com_stats = 0
    sem_stats = 0
    
    for idx, jogador_info in enumerate(elenco, 1):
        nome = jogador_info['nome']
        player_id = jogador_info['id']
        
        print(f"   [{idx}/{len(elenco)}] {nome:30} ", end='', flush=True)
        
        # Buscar estatísticas
        stats = buscar_estatisticas_jogador(player_id)
        time.sleep(delay)  # Delay entre requisições
        
        if stats and stats.get('partidas', 0) > 0:
            jogador_completo = {
                'nome': nome,
                'time': nome_time,
                'id': player_id,
                'foto_url': f"https://api.sofascore.com/api/v1/player/{player_id}/image",
                **stats
            }
            novos_jogadores.append(jogador_completo)
            com_stats += 1
            print(f"✅ {stats.get('partidas', 0):2}J {stats.get('gols', 0):2}G {stats.get('assistencias', 0):2}A")
        else:
            # Adicionar mesmo sem stats para manter elenco completo
            jogador_completo = {
                'nome': nome,
                'time': nome_time,
                'id': player_id,
                'foto_url': f"https://api.sofascore.com/api/v1/player/{player_id}/image"
            }
            novos_jogadores.append(jogador_completo)
            sem_stats += 1
            print("⚪ Sem dados")
    
    # Combinar: outros times + novos jogadores deste time
    jogadores_final = jogadores_outros_times + novos_jogadores
    
    # Salvar
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_final, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 70)
    print(f"✅ {nome_time} ATUALIZADO!")
    print(f"   🆕 Novos jogadores: {len(novos_jogadores)}")
    print(f"   📊 Com estatísticas: {com_stats}")
    print(f"   ⚪ Sem estatísticas: {sem_stats}")
    print(f"   📈 Total no sistema: {len(jogadores_final)}")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python atualizar_time.py <nome_do_time> [delay]")
        print("\nTimes disponíveis:")
        for time in sorted(TIMES_BRASILEIRAO_IDS.keys()):
            print(f"   - {time}")
        sys.exit(1)
    
    nome_time = sys.argv[1]
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    atualizar_time_especifico(nome_time, delay)
