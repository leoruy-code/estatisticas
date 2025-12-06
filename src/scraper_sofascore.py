"""
Script para fazer web scraping do SofaScore e coletar estatísticas de jogadores
do Brasileirão 2025

AVISO: Web scraping pode violar os termos de serviço do SofaScore.
Use com responsabilidade e considere usar APIs oficiais quando disponível.
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import os

# Diretórios
data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}

# IDs dos times no SofaScore (exemplo - você precisa encontrar os IDs corretos)
TIMES_SOFASCORE = {
    'Flamengo': {'id': 5981, 'url': 'flamengo'},
    'Palmeiras': {'id': 5998, 'url': 'palmeiras'},
    'Corinthians': {'id': 5947, 'url': 'corinthians'},
    'São Paulo': {'id': 6000, 'url': 'sao-paulo'},
    # Adicione mais times conforme necessário
}

def buscar_estatisticas_time_sofascore(time_nome, time_info):
    """
    Busca estatísticas de um time no SofaScore
    
    NOTA: O SofaScore usa uma API GraphQL/JSON. O scraping direto do HTML
    é complicado pois os dados são carregados via JavaScript.
    
    Alternativa: O SofaScore tem uma API não-documentada que retorna JSON.
    """
    
    try:
        # URL da API não-oficial do SofaScore (pode mudar)
        api_url = f"https://api.sofascore.com/api/v1/team/{time_info['id']}/players"
        
        print(f"🔍 Buscando jogadores do {time_nome}...")
        
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            jogadores = []
            
            # A estrutura exata depende da resposta da API
            if 'players' in data:
                for player_data in data['players']:
                    player = player_data.get('player', {})
                    
                    jogador = {
                        'nome': player.get('name', 'Desconhecido'),
                        'time': time_nome,
                        'posicao': player.get('position', 'Desconhecida'),
                        'gols': 0,  # Precisa de endpoint específico de estatísticas
                        'assistencias': 0,
                        'cartoes_amarelos': 0,
                        'cartoes_vermelhos': 0,
                        'faltas_cometidas': 0,
                        'faltas_sofridas': 0,
                        'chutes': 0,
                        'chutes_no_gol': 0,
                        'desarmes': 0
                    }
                    
                    jogadores.append(jogador)
                
                print(f"   ✅ Encontrados {len(jogadores)} jogadores")
                return jogadores
            
        else:
            print(f"   ❌ Erro ao buscar dados: Status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"   ❌ Erro ao processar {time_nome}: {str(e)}")
        return []

def buscar_estatisticas_jogador_sofascore(player_id, season_id):
    """
    Busca estatísticas detalhadas de um jogador específico
    
    Args:
        player_id: ID do jogador no SofaScore
        season_id: ID da temporada (ex: 2025)
    """
    
    try:
        # URL da API de estatísticas do jogador
        stats_url = f"https://api.sofascore.com/api/v1/player/{player_id}/statistics/season/{season_id}"
        
        response = requests.get(stats_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extrair estatísticas relevantes
            stats = data.get('statistics', {})
            
            return {
                'gols': stats.get('goals', 0),
                'assistencias': stats.get('assists', 0),
                'cartoes_amarelos': stats.get('yellowCards', 0),
                'cartoes_vermelhos': stats.get('redCards', 0),
                'chutes': stats.get('totalShots', 0),
                'chutes_no_gol': stats.get('shotsOnTarget', 0),
                'desarmes': stats.get('tackles', 0),
            }
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  Erro ao buscar estatísticas: {str(e)}")
        return None

def exemplo_uso_alternativo():
    """
    MÉTODO ALTERNATIVO: Usar APIs públicas de futebol
    
    Recomendação: Use APIs oficiais como:
    1. API-Football (api-football.com) - Gratuita com limite
    2. Football-Data.org - API gratuita
    3. TheSportsDB - API gratuita
    """
    
    print("\n💡 RECOMENDAÇÃO:")
    print("=" * 60)
    print("Para dados confiáveis e legais, considere usar APIs oficiais:")
    print("")
    print("1. API-Football (https://www.api-football.com/)")
    print("   - 100 requisições/dia grátis")
    print("   - Dados completos de jogadores e estatísticas")
    print("")
    print("2. Football-Data.org (https://www.football-data.org/)")
    print("   - API gratuita para uso pessoal")
    print("   - Cobertura de vários campeonatos")
    print("")
    print("3. TheSportsDB (https://www.thesportsdb.com/)")
    print("   - API gratuita")
    print("   - Banco de dados extenso")
    print("=" * 60)

def main():
    """
    Função principal - demonstração de como seria o scraping
    
    AVISO IMPORTANTE:
    - Web scraping do SofaScore pode violar seus termos de uso
    - As APIs não são oficialmente documentadas e podem mudar
    - Taxa de requisições deve ser limitada para não sobrecarregar o servidor
    - Considere usar APIs oficiais de futebol
    """
    
    print("⚽ Web Scraping do SofaScore - DEMO")
    print("=" * 60)
    print("⚠️  AVISO: Este é apenas um exemplo educacional!")
    print("    O SofaScore pode bloquear scrapers ou mudar a API.")
    print("    Use APIs oficiais para aplicações em produção.")
    print("=" * 60)
    print()
    
    # Exemplo de busca para um time
    # NOTA: Você precisa encontrar os IDs corretos dos times
    
    todos_jogadores = []
    
    for time_nome, time_info in list(TIMES_SOFASCORE.items())[:2]:  # Testar apenas 2 times
        jogadores = buscar_estatisticas_time_sofascore(time_nome, time_info)
        todos_jogadores.extend(jogadores)
        
        # Delay entre requisições para não sobrecarregar
        time.sleep(2)
    
    print(f"\n📊 Total de jogadores encontrados: {len(todos_jogadores)}")
    
    # Mostrar alternativas
    exemplo_uso_alternativo()
    
    print("\n💡 Para implementar scraping real:")
    print("   1. Inspecione a rede do SofaScore (F12 -> Network)")
    print("   2. Encontre os endpoints da API usados")
    print("   3. Identifique os IDs dos times e competições")
    print("   4. Implemente com rate limiting e tratamento de erros")
    print("   5. Considere usar proxies se necessário")

if __name__ == "__main__":
    main()
