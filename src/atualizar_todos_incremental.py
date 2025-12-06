#!/usr/bin/env python3
"""
Atualiza todos os times do Brasileirão de forma incremental
Com delays e verificações para evitar rate limit
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from atualizar_time import atualizar_time_especifico
from atualizar_sofascore import TIMES_BRASILEIRAO_IDS

def atualizar_todos_incremental():
    times = sorted(TIMES_BRASILEIRAO_IDS.keys())
    
    print("\n🏆 ATUALIZAÇÃO INCREMENTAL - BRASILEIRÃO 2025")
    print("=" * 70)
    print(f"📋 {len(times)} times para atualizar")
    print("⏱️  Delay entre jogadores: 2s")
    print("⏱️  Delay entre times: 5s")
    print("⏱️  Tempo estimado: 30-40 minutos")
    print("=" * 70)
    
    sucesso = 0
    falhas = 0
    
    for idx, time in enumerate(times, 1):
        print(f"\n\n📍 PROGRESSO: {idx}/{len(times)}")
        
        try:
            atualizar_time_especifico(time, delay=2)
            sucesso += 1
            
            if idx < len(times):
                print(f"\n⏳ Aguardando 5 segundos antes do próximo time...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Atualização interrompida pelo usuário!")
            print(f"✅ Times atualizados: {sucesso}")
            print(f"⏭️  Times restantes: {len(times) - idx}")
            break
        except Exception as e:
            print(f"\n❌ Erro ao atualizar {time}: {e}")
            falhas += 1
            print("⏭️  Continuando para o próximo time...")
            time.sleep(3)
    
    print("\n\n")
    print("=" * 70)
    print("🏁 ATUALIZAÇÃO FINALIZADA")
    print("=" * 70)
    print(f"✅ Times atualizados com sucesso: {sucesso}")
    print(f"❌ Times com falha: {falhas}")
    print("=" * 70)

if __name__ == "__main__":
    atualizar_todos_incremental()
