import json
import os

# Diretórios
data_dir = os.path.join(os.path.dirname(__file__), '../data')
times_path = os.path.join(data_dir, 'times.json')

# Times do Brasileirão 2025 com URLs dos escudos
TIMES_BRASILEIRAO_2025 = [
    {
        "nome": "Flamengo",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/9/93/Flamengo-RJ_%28BRA%29.png",
        "jogadores": []
    },
    {
        "nome": "Palmeiras",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Botafogo",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/5/52/Botafogo_de_Futebol_e_Regatas_logo.svg",
        "jogadores": []
    },
    {
        "nome": "São Paulo",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg",
        "jogadores": []
    },
    {
        "nome": "Grêmio",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Gremio_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Internacional",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg",
        "jogadores": []
    },
    {
        "nome": "Fluminense",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Fluminense_FC_escudo.svg",
        "jogadores": []
    },
    {
        "nome": "Corinthians",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Corinthians_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Atlético Mineiro",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/5/5f/Atletico_mineiro_galo.png",
        "jogadores": []
    },
    {
        "nome": "Cruzeiro",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg",
        "jogadores": []
    },
    {
        "nome": "Bahia",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/2/25/Esporte_Clube_Bahia_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Vasco da Gama",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/4/43/CRVascodaGama.png",
        "jogadores": []
    },
    {
        "nome": "Athletico Paranaense",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/8/8b/Athletico_Paranaense.png",
        "jogadores": []
    },
    {
        "nome": "Fortaleza",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/4/40/FortalezaEsporteClube.svg",
        "jogadores": []
    },
    {
        "nome": "Bragantino",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/9/9b/Red_Bull_Bragantino_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Santos",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/3/32/Santos_Logo.png",
        "jogadores": []
    },
    {
        "nome": "Juventude",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Juventude_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Cuiabá",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/0/0c/Cuiaba_Esporte_Clube_logo.svg",
        "jogadores": []
    },
    {
        "nome": "Vitória",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/c/c1/EC_Vit%C3%B3ria.png",
        "jogadores": []
    },
    {
        "nome": "Atlético Goianiense",
        "imagem": "https://upload.wikimedia.org/wikipedia/commons/f/f4/Atletico_Clube_Goianiense.png",
        "jogadores": []
    }
]

def carregar_times_existentes():
    """Carrega times já existentes"""
    if not os.path.exists(times_path):
        return []
    with open(times_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_times(times):
    """Salva os times no arquivo JSON"""
    os.makedirs(os.path.dirname(times_path), exist_ok=True)
    with open(times_path, 'w', encoding='utf-8') as f:
        json.dump(times, f, ensure_ascii=False, indent=2)

def adicionar_times_brasileirao():
    """Adiciona todos os times do Brasileirão 2025"""
    print("🏆 Carregando times do Brasileirão 2025...")
    
    times_existentes = carregar_times_existentes()
    nomes_existentes = {t['nome'].lower() for t in times_existentes}
    
    times_adicionados = 0
    times_ignorados = 0
    
    for time in TIMES_BRASILEIRAO_2025:
        if time['nome'].lower() in nomes_existentes:
            print(f"⚠️  {time['nome']} já existe, pulando...")
            times_ignorados += 1
        else:
            times_existentes.append(time)
            print(f"✅ {time['nome']} adicionado!")
            times_adicionados += 1
    
    # Salvar todos os times
    salvar_times(times_existentes)
    
    print(f"\n🎉 Processo concluído!")
    print(f"   ✅ Times adicionados: {times_adicionados}")
    print(f"   ⚠️  Times já existentes: {times_ignorados}")
    print(f"   📊 Total de times no sistema: {len(times_existentes)}")

if __name__ == "__main__":
    adicionar_times_brasileirao()
