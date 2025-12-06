import sys, requests
sys.path.insert(0, 'src')
from config_api_football import get_next_key, BASE_URL

headers = {'x-apisports-key': get_next_key()}

print('🔎 LIGAS NO BRASIL')
url = f'{BASE_URL}/leagues'
params = {'country':'Brazil'}
res = requests.get(url, headers=headers, params=params)
print('Status:', res.status_code)
if res.status_code==200:
    data = res.json()
    print('Total ligas:', len(data.get('response', [])))
    for item in data.get('response', [])[:10]:
        league = item['league']
        seasons = item['seasons']
        years = [s['year'] for s in seasons][-5:]
        print(f"- {league['name']} (id {league['id']}), anos recentes: {years}")
else:
    print(res.text[:300])

print('\n🔎 LIGA 71 DETALHES')
params = {'id':71}
res2 = requests.get(url, headers=headers, params=params)
print('Status:', res2.status_code)
if res2.status_code==200:
    d2 = res2.json()
    if d2.get('response'):
        item = d2['response'][0]
        seasons = item['seasons']
        years = [s['year'] for s in seasons]
        print('League:', item['league']['name'])
        print('Seasons:', years[-10:])
        s2025 = next((s for s in seasons if s['year']==2025), None)
        if s2025:
            print('2025 coverage:', s2025.get('coverage'))
        else:
            print('2025 not listed')
