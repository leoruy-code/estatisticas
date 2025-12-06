import sys, requests
sys.path.insert(0, 'src')
from config_api_football import API_KEYS, BASE_URL

TARGETS = [
    (f"{BASE_URL}/leagues", {"id": 71}),
    (f"{BASE_URL}/teams", {"league": 71, "season": 2025}),
    (f"{BASE_URL}/fixtures", {"league": 71, "season": 2025}),
    (f"{BASE_URL}/players", {"team": 33, "season": 2025}),  # Flamengo exemplo
]

def check_key(key: str):
    headers = {"x-apisports-key": key}
    print(f"\n== CHAVE {key[:6]}... ==")
    for url, params in TARGETS:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=20)
            size = len(r.text or "")
            ok = r.status_code
            resp = []
            if ok == 200:
                data = r.json()
                resp = data.get("response", [])
            print(f"{url.split('/')[-1]:>10} -> status {ok}, itens {len(resp)}, bytes {size}")
        except Exception as e:
            print(f"{url} -> erro {e}")

if __name__ == "__main__":
    print("Diagnóstico API-Football (liga 71, season 2025)")
    for key in API_KEYS:
        check_key(key)
