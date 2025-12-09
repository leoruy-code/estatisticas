#!/usr/bin/env python3
"""
Script para sincronizar jogadores com seus times
Vincula os jogadores do jogadores.json aos times no times.json
"""

import json
import os

# Caminhos
data_dir = os.path.join(os.path.dirname(__file__), '../data')
times_path = os.path.join(data_dir, 'times.json')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

def sincronizar_times_jogadores():
    """Sincroniza jogadores com seus times"""
    
    print("🔄 SINCRONIZANDO JOGADORES COM TIMES")
    print("=" * 70)
    print()
    
    # Carregar dados
    with open(times_path, 'r', encoding='utf-8') as f:
        times = json.load(f)
    
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    print(f"📊 Dados carregados:")
    print(f"   Times: {len(times)}")
    print(f"   Jogadores: {len(jogadores)}")
    print()
    
    # Criar dicionário de jogadores por time
    jogadores_por_time = {}
    for jogador in jogadores:
        time_nome = jogador.get('time')
        if time_nome:
            if time_nome not in jogadores_por_time:
                jogadores_por_time[time_nome] = []
            jogadores_por_time[time_nome].append(jogador)
    
    # Atualizar cada time com seus jogadores
    times_atualizados = 0
    jogadores_vinculados = 0
    
    for time in times:
        nome_time = time.get('nome')
        if nome_time in jogadores_por_time:
            # Atualizar lista de jogadores do time
            time['jogadores'] = jogadores_por_time[nome_time]
            times_atualizados += 1
            jogadores_vinculados += len(jogadores_por_time[nome_time])
            print(f"✅ {nome_time}: {len(jogadores_por_time[nome_time])} jogadores vinculados")
        else:
            # Garantir que tem lista vazia
            time['jogadores'] = []
            print(f"⚪ {nome_time}: sem jogadores")
    
    # Salvar times atualizados
    with open(times_path, 'w', encoding='utf-8') as f:
        json.dump(times, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 70)
    print("🎉 SINCRONIZAÇÃO CONCLUÍDA!")
    print("=" * 70)
    print(f"✅ Times atualizados: {times_atualizados}")
    print(f"✅ Jogadores vinculados: {jogadores_vinculados}")
    print()

if __name__ == "__main__":
    sincronizar_times_jogadores()
