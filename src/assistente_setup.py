#!/usr/bin/env python3
"""
Assistente de Setup - API-Football
Guia interativo para configuração
"""

import os
import sys

def check_config():
    """Verifica se configuração está OK"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from config_api_football import API_KEYS
        
        keys_validas = [k for k in API_KEYS if k and k != "SUA_API_KEY_1_AQUI"]
        return len(keys_validas)
    except:
        return 0

def main():
    print("\n" + "=" * 80)
    print("🚀 ASSISTENTE DE SETUP - API-FOOTBALL")
    print("=" * 80)
    
    # Verificar configuração atual
    num_keys = check_config()
    
    if num_keys == 0:
        print("\n❌ NENHUMA API KEY CONFIGURADA")
        print("\n📋 SIGA ESTES PASSOS:")
        print()
        print("1️⃣  CRIAR CONTAS (10 min)")
        print("   • Acesse: https://www.api-football.com/")
        print("   • Clique em 'Sign Up' (canto superior direito)")
        print("   • Crie 5 contas com emails diferentes")
        print("   • Dica: use Gmail com +")
        print("     Exemplo: seu_email+api1@gmail.com")
        print("              seu_email+api2@gmail.com")
        print("              ... até +api5@gmail.com")
        print()
        
        print("2️⃣  COPIAR API KEYS (5 min)")
        print("   • Para cada conta criada:")
        print("     a) Faça login em: https://dashboard.api-football.com/")
        print("     b) Copie a API Key mostrada")
        print("     c) Cole em um bloco de notas temporário")
        print()
        
        print("3️⃣  CONFIGURAR SISTEMA (1 min)")
        print("   • Abra: src/config_api_football.py")
        print("   • Cole suas 5 API Keys no lugar de:")
        print("     'SUA_API_KEY_1_AQUI', etc")
        print("   • Salve o arquivo (Cmd+S)")
        print()
        
        print("4️⃣  TESTAR")
        print("   • Execute: python src/assistente_setup.py")
        print("   • Deve mostrar: ✅ X chaves configuradas")
        print()
        
    elif num_keys < 5:
        print(f"\n⚠️  {num_keys} API KEY(S) CONFIGURADA(S)")
        print(f"   Recomendado: 5 chaves = 500 requests/dia")
        print(f"   Faltam: {5 - num_keys} chaves")
        print()
        print("💡 Você pode usar com", num_keys, "chave(s), mas terá limite de:")
        print(f"   • {num_keys * 100} requests/dia")
        print()
        print("Para adicionar mais:")
        print("   1. Crie mais", 5 - num_keys, "conta(s) em: https://www.api-football.com/")
        print("   2. Copie as API Keys")
        print("   3. Adicione em: src/config_api_football.py")
        print()
        
        resposta = input("Continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            print("\n✅ OK! Configure mais chaves e volte aqui")
            return
    
    else:
        print(f"\n✅ {num_keys} API KEYS CONFIGURADAS!")
        print(f"   Limite diário: {num_keys * 100} requests")
        print()
    
    # Menu de ações
    print("=" * 80)
    print("O QUE VOCÊ QUER FAZER?")
    print("=" * 80)
    print()
    print("1️⃣  Testar conexão com API")
    print("2️⃣  Atualizar dados do Brasileirão")
    print("3️⃣  Ver guia completo")
    print("4️⃣  Sair")
    print()
    
    escolha = input("Escolha (1-4): ")
    
    if escolha == "1":
        print("\n▶️  Executando teste...")
        os.system("python src/testar_api_football.py")
        
    elif escolha == "2":
        print("\n⚠️  ATENÇÃO:")
        print(f"   • Vai usar ~40-60 requests (de {num_keys * 100} disponíveis)")
        print("   • Tempo estimado: 5-10 minutos")
        print("   • Vai atualizar TODOS os 20 times do Brasileirão")
        print()
        confirma = input("Continuar? (s/n): ")
        
        if confirma.lower() == 's':
            print("\n▶️  Iniciando atualização...")
            os.system("python src/atualizar_api_football.py")
            
            print("\n✅ Atualização completa!")
            print("\n💡 PRÓXIMOS PASSOS:")
            print("   1. Sincronizar: python src/sincronizar_times_jogadores.py")
            print("   2. Ver site: streamlit run src/frontend/app.py")
        
    elif escolha == "3":
        print("\n📖 Abrindo guia completo...")
        if os.path.exists("GUIA_SETUP_API_FOOTBALL.md"):
            os.system("cat GUIA_SETUP_API_FOOTBALL.md | less")
        else:
            print("❌ Arquivo não encontrado: GUIA_SETUP_API_FOOTBALL.md")
    
    else:
        print("\n👋 Até logo!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
