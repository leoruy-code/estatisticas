"""
Scraper seguro e eficiente para SofaScore
Implementa melhores práticas para evitar bloqueios
"""

import json
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

# Configurações de segurança
MIN_DELAY = 2  # segundos entre requests
MAX_DELAY = 5
MAX_RETRIES = 3
TIMEOUT = 30
REQUESTS_PER_MINUTE = 15  # Limite conservador

# Pool de User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class RateLimiter:
    """Controla taxa de requisições"""
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        now = time.time()
        # Remove requests antigas (mais de 1 minuto)
        self.requests = [r for r in self.requests if now - r < 60]
        
        if len(self.requests) >= self.requests_per_minute:
            # Aguardar até o request mais antigo sair da janela
            sleep_time = 60 - (now - self.requests[0]) + 1
            print(f"⏳ Rate limit: aguardando {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            self.requests = []
        
        self.requests.append(now)


class SafeScraper:
    """Scraper seguro com proteções anti-bloqueio"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(REQUESTS_PER_MINUTE)
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.request_count = 0
    
    def _get_cache_path(self, url: str) -> str:
        """Gera caminho de cache baseado na URL"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")
    
    def _load_cache(self, url: str) -> Optional[str]:
        """Carrega resposta do cache se disponível e recente (< 1 dia)"""
        cache_path = self._get_cache_path(url)
        if os.path.exists(cache_path):
            # Verificar idade do cache
            age = time.time() - os.path.getmtime(cache_path)
            if age < 86400:  # 24 horas
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📦 Cache hit: {url[:60]}...")
                    return data.get('content')
        return None
    
    def _save_cache(self, url: str, content: str):
        """Salva resposta no cache"""
        cache_path = self._get_cache_path(url)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'content': content
            }, f, ensure_ascii=False)
    
    def get(self, url: str, use_cache: bool = True) -> Optional[requests.Response]:
        """
        Faz request com proteções:
        - Rate limiting
        - User-Agent rotation
        - Retry com backoff
        - Cache
        - Delays aleatórios
        """
        # Tentar cache primeiro
        if use_cache:
            cached = self._load_cache(url)
            if cached:
                mock_response = requests.Response()
                mock_response._content = cached.encode('utf-8')
                mock_response.status_code = 200
                return mock_response
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Delay aleatório
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)
        
        # Tentar com retry
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = self.session.get(url, headers=headers, timeout=TIMEOUT)
                self.request_count += 1
                
                if response.status_code == 200:
                    print(f"✅ Request #{self.request_count}: {url[:60]}...")
                    # Salvar no cache
                    self._save_cache(url, response.text)
                    return response
                elif response.status_code == 429:
                    # Too Many Requests - aguardar mais
                    wait = (2 ** attempt) * 10
                    print(f"⚠️  Rate limit (429), aguardando {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"⚠️  Status {response.status_code}, tentativa {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                print(f"❌ Erro na tentativa {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def get_team_players_sofascore(self, team_slug: str, team_id: int) -> List[Dict[str, Any]]:
        """
        Busca jogadores de um time no SofaScore
        Usa API JSON direta ao invés de scraping HTML
        """
        # API-Football style - tentar endpoint JSON direto
        api_url = f"https://api.sofascore.com/api/v1/team/{team_id}/players"
        
        response = self.get(api_url)
        if response and response.status_code == 200:
            try:
                data = response.json()
                players = []
                
                for player_data in data.get('players', []):
                    player = player_data.get('player', {})
                    players.append({
                        'nome': player.get('name'),
                        'posicao': player.get('position'),
                        'numero_camisa': player.get('jerseyNumber'),
                        'nacionalidade': player.get('country', {}).get('alpha3Code'),
                        'idade': self._calculate_age(player.get('dateOfBirthTimestamp')),
                        'altura': f"{player.get('height')} cm" if player.get('height') else None,
                        'foto_url': f"https://api.sofascore.com/api/v1/player/{player.get('id')}/image",
                        'sofascore_id': player.get('id'),
                        'season': 2025
                    })
                
                return players
            except Exception as e:
                print(f"⚠️  Erro ao parsear JSON: {e}")
        
        # Fallback: scraping HTML se API falhar
        return self._scrape_team_page(team_slug, team_id)
    
    def _calculate_age(self, timestamp: Optional[int]) -> Optional[int]:
        """Calcula idade a partir de timestamp"""
        if timestamp:
            from datetime import datetime
            birth_date = datetime.fromtimestamp(timestamp)
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return None
    
    def _scrape_team_page(self, team_slug: str, team_id: int) -> List[Dict[str, Any]]:
        """Fallback: scraping da página HTML"""
        url = f"https://www.sofascore.com/pt/team/football/{team_slug}/{team_id}"
        
        response = self.get(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        players = []
        
        # Tentar extrair de scripts JSON embutidos
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Processar se houver dados de elenco
                # (implementação específica depende da estrutura)
            except:
                pass
        
        return players


def main():
    """Exemplo de uso"""
    scraper = SafeScraper()
    
    # Exemplo: buscar jogadores do Flamengo
    print("🔍 Buscando jogadores do Flamengo via SofaScore...")
    players = scraper.get_team_players_sofascore('flamengo', 5981)
    
    print(f"\n✅ Encontrados {len(players)} jogadores")
    for p in players[:5]:
        print(f"  - {p.get('nome')} ({p.get('posicao')})")
    
    print(f"\n📊 Total de requests: {scraper.request_count}")


if __name__ == '__main__':
    main()
