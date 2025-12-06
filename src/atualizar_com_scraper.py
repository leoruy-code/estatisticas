"""
Script para atualizar base de dados usando scraper seguro
Busca estatísticas e fotos de jogadores do SofaScore
"""

import json
import os
from scraper_seguro import SafeScraper

# Mapeamento de times do Brasileirão no SofaScore
SOFASCORE_TEAMS = {
    'Flamengo': {'slug': 'flamengo', 'id': 5981},
    'Palmeiras': {'slug': 'palmeiras', 'id': 5957},
    'Botafogo': {'slug': 'botafogo', 'id': 1958},
    'São Paulo': {'slug': 'sao-paulo', 'id': 5947},
    'Corinthians': {'slug': 'corinthians', 'id': 5926},
    'Atlético-MG': {'slug': 'atletico-mineiro', 'id': 1947},
    'Grêmio': {'slug': 'gremio', 'id': 5933},
    'Fluminense': {'slug': 'fluminense', 'id': 5930},
    'Cruzeiro': {'slug': 'cruzeiro', 'id': 1963},
    'Vasco': {'slug': 'vasco-da-gama', 'id': 5998},
    'Internacional': {'slug': 'internacional', 'id': 5925},
    'Bahia': {'slug': 'bahia', 'id': 1943},
    'RB Bragantino': {'slug': 'red-bull-bragantino', 'id': 6002},
    'Athletico-PR': {'slug': 'atletico-paranaense', 'id': 1950},
    'Fortaleza': {'slug': 'fortaleza', 'id': 1973},
    'Juventude': {'slug': 'juventude', 'id': 1968},
    'Vitória': {'slug': 'vitoria', 'id': 1997},
    'Cuiabá': {'slug': 'cuiaba', 'id': 24264},
    'Atlético-GO': {'slug': 'atletico-goianiense', 'id': 1957},
    'Criciúma': {'slug': 'criciuma', 'id': 1964}
}


def atualizar_fotos_jogadores(times: list = None):
    """
    Atualiza foto_url dos jogadores usando SofaScore
    
    Args:
        times: Lista de times para atualizar. Se None, atualiza todos.
    """
    scraper = SafeScraper()
    
    # Carregar jogadores atuais
    jogadores_path = 'data/jogadores.json'
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        jogadores = json.load(f)
    
    if times is None:
        times = list(SOFASCORE_TEAMS.keys())
    
    print(f"🔍 Buscando fotos para {len(times)} time(s)...")
    print(f"📊 Total de jogadores: {len(jogadores)}")
    
    atualizados = 0
    
    for time_nome in times:
        if time_nome not in SOFASCORE_TEAMS:
            print(f"⚠️  Time '{time_nome}' não encontrado no mapeamento SofaScore")
            continue
        
        team_info = SOFASCORE_TEAMS[time_nome]
        print(f"\n🔍 Processando {time_nome}...")
        
        # Buscar jogadores do SofaScore
        sofascore_players = scraper.get_team_players_sofascore(
            team_info['slug'], 
            team_info['id']
        )
        
        print(f"   Encontrados {len(sofascore_players)} no SofaScore")
        
        # Mapear por nome (normalizado)
        sofascore_map = {
            normalize_name(p['nome']): p 
            for p in sofascore_players 
            if p.get('nome')
        }
        
        # Atualizar jogadores locais
        for jogador in jogadores:
            if jogador.get('time') != time_nome:
                continue
            
            nome_norm = normalize_name(jogador['nome'])
            if nome_norm in sofascore_map:
                sofascore_data = sofascore_map[nome_norm]
                
                # Atualizar foto se disponível
                if sofascore_data.get('foto_url') and not jogador.get('foto_url'):
                    jogador['foto_url'] = sofascore_data['foto_url']
                    jogador['sofascore_id'] = sofascore_data.get('sofascore_id')
                    print(f"   ✅ {jogador['nome']}: foto adicionada")
                    atualizados += 1
    
    # Salvar atualizações
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Processo concluído!")
    print(f"   Total de fotos adicionadas: {atualizados}")
    print(f"   Total de requests: {scraper.request_count}")
    
    return atualizados


def normalize_name(name: str) -> str:
    """Normaliza nome para matching"""
    import unicodedata
    # Remove acentos
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    # Lowercase e remove espaços extras
    return name.lower().strip()


def buscar_estatisticas_sofascore(time_nome: str, season: int = 2025):
    """
    Busca estatísticas detalhadas do SofaScore
    (Para implementar depois se necessário)
    """
    pass


if __name__ == '__main__':
    import sys
    
    # Uso: python src/atualizar_com_scraper.py [time1] [time2] ...
    # Sem argumentos: atualiza todos os times
    
    times = sys.argv[1:] if len(sys.argv) > 1 else None
    
    atualizar_fotos_jogadores(times)
