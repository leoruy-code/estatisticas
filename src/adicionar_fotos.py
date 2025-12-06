#!/usr/bin/env python3
"""
Adiciona foto_url aos jogadores que têm ID mas não têm foto
"""

import json
import os

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

def adicionar_fotos():
    print("📸 ADICIONANDO FOTOS AOS JOGADORES")
    print("=" * 70)
    
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    print(f"Total de jogadores: {len(jogadores)}")
    
    sem_foto = sum(1 for j in jogadores if not j.get('foto_url'))
    print(f"Jogadores sem foto: {sem_foto}")
    print()
    
    atualizados = 0
    
    for jogador in jogadores:
        # Se não tem foto mas tem ID do SofaScore
        if not jogador.get('foto_url') and jogador.get('id'):
            player_id = jogador['id']
            jogador['foto_url'] = f"https://api.sofascore.com/api/v1/player/{player_id}/image"
            atualizados += 1
    
    print(f"✅ Fotos adicionadas: {atualizados}")
    
    # Salvar
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=2)
    
    print("💾 Arquivo salvo!")
    print()
    
    # Verificar resultado
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    com_foto = sum(1 for j in jogadores if j.get('foto_url'))
    print(f"📊 RESULTADO FINAL:")
    print(f"   Total: {len(jogadores)}")
    print(f"   Com foto: {com_foto}")
    print(f"   Sem foto: {len(jogadores) - com_foto}")

if __name__ == "__main__":
    adicionar_fotos()
