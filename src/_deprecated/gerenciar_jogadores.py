#!/usr/bin/env python3
"""
Ferramenta para gerenciar jogadores manualmente
Remove jogadores que saíram dos times
"""

import json
import os
import sys

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

def listar_jogadores_time(nome_time):
    """Lista jogadores de um time"""
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    jogadores_time = sorted([j for j in jogadores if j.get('time') == nome_time], 
                           key=lambda x: x.get('nome'))
    
    print(f"\n📋 {nome_time}: {len(jogadores_time)} jogadores")
    print("=" * 70)
    
    for idx, j in enumerate(jogadores_time, 1):
        stats = ""
        if j.get('partidas', 0) > 0:
            stats = f"{j.get('partidas', 0):2}J {j.get('gols', 0):2}G {j.get('assistencias', 0):2}A"
        else:
            stats = "⚪ Sem stats"
        
        foto = "📷" if j.get('foto_url') else "  "
        print(f"   [{idx:3}] {foto} {j['nome']:35} {stats}")
    
    return jogadores_time

def remover_jogador(nome_time, nome_jogador):
    """Remove um jogador específico"""
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    antes = len(jogadores)
    jogadores_filtrados = [j for j in jogadores 
                          if not (j.get('time') == nome_time and j.get('nome') == nome_jogador)]
    
    if len(jogadores_filtrados) == antes:
        print(f"❌ Jogador não encontrado: {nome_jogador} ({nome_time})")
        return False
    
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_filtrados, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Removido: {nome_jogador} ({nome_time})")
    print(f"📊 Jogadores: {antes} → {len(jogadores_filtrados)}")
    return True

def remover_varios_jogadores(nome_time, nomes_jogadores):
    """Remove vários jogadores de uma vez"""
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    antes = len(jogadores)
    removidos = []
    
    jogadores_filtrados = []
    for j in jogadores:
        if j.get('time') == nome_time and j.get('nome') in nomes_jogadores:
            removidos.append(j['nome'])
        else:
            jogadores_filtrados.append(j)
    
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_filtrados, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Removidos {len(removidos)} jogadores do {nome_time}:")
    for nome in removidos:
        print(f"   - {nome}")
    
    print(f"\n📊 Total: {antes} → {len(jogadores_filtrados)}")
    return removidos

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python gerenciar_jogadores.py listar <time>")
        print("  python gerenciar_jogadores.py remover <time> <nome_jogador>")
        print("  python gerenciar_jogadores.py remover-varios <time> 'Nome1' 'Nome2' 'Nome3'")
        sys.exit(1)
    
    comando = sys.argv[1]
    
    if comando == "listar":
        if len(sys.argv) < 3:
            print("❌ Informe o nome do time")
            sys.exit(1)
        listar_jogadores_time(sys.argv[2])
    
    elif comando == "remover":
        if len(sys.argv) < 4:
            print("❌ Informe o time e o nome do jogador")
            sys.exit(1)
        remover_jogador(sys.argv[2], sys.argv[3])
    
    elif comando == "remover-varios":
        if len(sys.argv) < 4:
            print("❌ Informe o time e os nomes dos jogadores")
            sys.exit(1)
        remover_varios_jogadores(sys.argv[2], sys.argv[3:])
    
    else:
        print(f"❌ Comando desconhecido: {comando}")
        sys.exit(1)
