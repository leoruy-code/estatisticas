#!/usr/bin/env python3
"""
Atualização completa e limpa do Brasileirão 2025
Remove jogadores antigos e busca apenas elencos atuais
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from atualizar_sofascore import atualizar_estatisticas_brasileirao, TIMES_BRASILEIRAO_IDS

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

def limpar_e_atualizar_completo():
    print("\n🔄 ATUALIZAÇÃO COMPLETA - BRASILEIRÃO 2025")
    print("=" * 70)
    print("⚠️  Esta operação irá:")
    print("   1. Limpar todos os jogadores antigos do Brasileirão")
    print("   2. Buscar elencos atualizados de todos os times")
    print("   3. Atualizar estatísticas de cada jogador")
    print("=" * 70)
    print()
    
    # Carregar jogadores atuais
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores_atuais = json.load(f)
    
    print(f"📊 Jogadores antes da limpeza: {len(jogadores_atuais)}")
    
    # Remover apenas jogadores do Brasileirão (manter outros times como Al-Nassr, etc)
    times_brasileirao = list(TIMES_BRASILEIRAO_IDS.keys())
    jogadores_outras_ligas = [j for j in jogadores_atuais if j.get('time') not in times_brasileirao]
    
    print(f"🌍 Jogadores de outras ligas (preservados): {len(jogadores_outras_ligas)}")
    print()
    
    # Salvar backup temporário
    backup_path = os.path.join(data_dir, 'jogadores_backup.json')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_atuais, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup criado: {backup_path}")
    print()
    
    # Resetar arquivo com apenas jogadores de outras ligas
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores_outras_ligas, f, ensure_ascii=False, indent=2)
    
    print("🚀 INICIANDO ATUALIZAÇÃO COMPLETA DOS 20 TIMES...")
    print("⏱️  Tempo estimado: 30-40 minutos")
    print("=" * 70)
    print()
    
    # Atualizar todos os times
    try:
        atualizar_estatisticas_brasileirao(atualizar_existentes=True)
        print()
        print("=" * 70)
        print("🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        
        # Verificar resultado
        with open(jogadores_path, 'r', encoding='utf-8') as f:
            jogadores_finais = json.load(f)
        
        jogadores_brasileirao = [j for j in jogadores_finais if j.get('time') in times_brasileirao]
        
        print()
        print("📊 RESULTADO FINAL:")
        print(f"   Total de jogadores: {len(jogadores_finais)}")
        print(f"   Jogadores do Brasileirão: {len(jogadores_brasileirao)}")
        print(f"   Outras ligas: {len(jogadores_finais) - len(jogadores_brasileirao)}")
        
        # Estatísticas por time
        print()
        print("📋 JOGADORES POR TIME:")
        for time in sorted(times_brasileirao):
            jogs_time = [j for j in jogadores_brasileirao if j.get('time') == time]
            com_stats = sum(1 for j in jogs_time if j.get('partidas', 0) > 0)
            print(f"   {time:25} {len(jogs_time):3} jogadores ({com_stats:3} com stats)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Atualização interrompida!")
        print("💡 Dados parciais foram salvos")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("💡 Restaurando backup...")
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        with open(jogadores_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print("✅ Backup restaurado!")

if __name__ == "__main__":
    limpar_e_atualizar_completo()
