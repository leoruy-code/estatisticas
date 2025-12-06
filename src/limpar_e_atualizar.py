#!/usr/bin/env python3
"""
Remove jogadores duplicados/antigos e mantém apenas os do Brasileirão 2025
"""

import json
import os

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

# Times do Brasileirão 2025
TIMES_BRASILEIRAO = [
    'Flamengo', 'Palmeiras', 'Corinthians', 'São Paulo', 'Grêmio',
    'Internacional', 'Fluminense', 'Atlético Mineiro', 'Cruzeiro',
    'Botafogo', 'Vasco da Gama', 'Santos', 'Athletico Paranaense',
    'Bahia', 'Fortaleza', 'Bragantino', 'Cuiabá', 'Juventude',
    'Vitória', 'Atlético Goianiense'
]

def limpar_jogadores():
    print("🧹 LIMPANDO JOGADORES ANTIGOS/DUPLICADOS")
    print("=" * 70)
    
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    print(f"Total antes: {len(jogadores)}")
    
    # Manter apenas jogadores do Brasileirão 2025
    jogadores_limpos = [j for j in jogadores if j.get('time') in TIMES_BRASILEIRAO]
    
    # Remover duplicados (manter o mais recente - com mais campos)
    jogadores_unicos = {}
    for jog in jogadores_limpos:
        chave = f"{jog['nome']}_{jog['time']}"
        if chave not in jogadores_unicos or len(jog) > len(jogadores_unicos[chave]):
            jogadores_unicos[chave] = jog
    
    jogadores_finais = list(jogadores_unicos.values())
    
    print(f"Total depois: {len(jogadores_finais)}")
    print(f"Removidos: {len(jogadores) - len(jogadores_finais)}")
    
    # Salvar
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_finais, f, ensure_ascii=False, indent=2)
    
    print("✅ Limpeza concluída!")
    
    return len(jogadores_finais)

if __name__ == "__main__":
    limpar_jogadores()
