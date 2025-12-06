#!/usr/bin/env python3
"""
Script para atualizar todos os times do Brasileirão 2025
"""

import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from atualizar_sofascore import atualizar_estatisticas_brasileirao

if __name__ == "__main__":
    print("\n🚀 Iniciando atualização completa do Brasileirão 2025...")
    print("⏱️  Tempo estimado: 30-40 minutos")
    print("💡 Você pode interromper com Ctrl+C a qualquer momento\n")
    
    try:
        atualizar_estatisticas_brasileirao()
    except KeyboardInterrupt:
        print("\n\n⚠️  Atualização interrompida pelo usuário")
        print("✅ Dados já processados foram salvos!")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        sys.exit(1)
