import json
import os

# Diretórios
data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')

# Elencos dos times do Brasileirão 2025 (principais jogadores)
JOGADORES_BRASILEIRAO_2025 = [
    # Flamengo
    {"nome": "Rossi", "time": "Flamengo", "posicao": "Goleiro"},
    {"nome": "Wesley", "time": "Flamengo", "posicao": "Lateral"},
    {"nome": "Léo Pereira", "time": "Flamengo", "posicao": "Zagueiro"},
    {"nome": "Fabrício Bruno", "time": "Flamengo", "posicao": "Zagueiro"},
    {"nome": "Ayrton Lucas", "time": "Flamengo", "posicao": "Lateral"},
    {"nome": "Pulgar", "time": "Flamengo", "posicao": "Volante"},
    {"nome": "De La Cruz", "time": "Flamengo", "posicao": "Meia"},
    {"nome": "Arrascaeta", "time": "Flamengo", "posicao": "Meia"},
    {"nome": "Gerson", "time": "Flamengo", "posicao": "Meia"},
    {"nome": "Bruno Henrique", "time": "Flamengo", "posicao": "Atacante"},
    {"nome": "Pedro", "time": "Flamengo", "posicao": "Atacante"},
    
    # Palmeiras
    {"nome": "Weverton", "time": "Palmeiras", "posicao": "Goleiro"},
    {"nome": "Marcos Rocha", "time": "Palmeiras", "posicao": "Lateral"},
    {"nome": "Gustavo Gómez", "time": "Palmeiras", "posicao": "Zagueiro"},
    {"nome": "Murilo", "time": "Palmeiras", "posicao": "Zagueiro"},
    {"nome": "Piquerez", "time": "Palmeiras", "posicao": "Lateral"},
    {"nome": "Zé Rafael", "time": "Palmeiras", "posicao": "Volante"},
    {"nome": "Richard Ríos", "time": "Palmeiras", "posicao": "Volante"},
    {"nome": "Raphael Veiga", "time": "Palmeiras", "posicao": "Meia"},
    {"nome": "Estêvão", "time": "Palmeiras", "posicao": "Atacante"},
    {"nome": "Rony", "time": "Palmeiras", "posicao": "Atacante"},
    {"nome": "Flaco López", "time": "Palmeiras", "posicao": "Atacante"},
    
    # Botafogo
    {"nome": "John", "time": "Botafogo", "posicao": "Goleiro"},
    {"nome": "Vitinho", "time": "Botafogo", "posicao": "Lateral"},
    {"nome": "Bastos", "time": "Botafogo", "posicao": "Zagueiro"},
    {"nome": "Alexander Barboza", "time": "Botafogo", "posicao": "Zagueiro"},
    {"nome": "Cuiabano", "time": "Botafogo", "posicao": "Lateral"},
    {"nome": "Marlon Freitas", "time": "Botafogo", "posicao": "Volante"},
    {"nome": "Gregore", "time": "Botafogo", "posicao": "Volante"},
    {"nome": "Savarino", "time": "Botafogo", "posicao": "Meia"},
    {"nome": "Luiz Henrique", "time": "Botafogo", "posicao": "Atacante"},
    {"nome": "Júnior Santos", "time": "Botafogo", "posicao": "Atacante"},
    
    # São Paulo
    {"nome": "Rafael", "time": "São Paulo", "posicao": "Goleiro"},
    {"nome": "Rafinha", "time": "São Paulo", "posicao": "Lateral"},
    {"nome": "Arboleda", "time": "São Paulo", "posicao": "Zagueiro"},
    {"nome": "Alan Franco", "time": "São Paulo", "posicao": "Zagueiro"},
    {"nome": "Welington", "time": "São Paulo", "posicao": "Lateral"},
    {"nome": "Alisson", "time": "São Paulo", "posicao": "Volante"},
    {"nome": "Luiz Gustavo", "time": "São Paulo", "posicao": "Volante"},
    {"nome": "Lucas", "time": "São Paulo", "posicao": "Meia"},
    {"nome": "Luciano", "time": "São Paulo", "posicao": "Atacante"},
    {"nome": "Calleri", "time": "São Paulo", "posicao": "Atacante"},
    
    # Grêmio
    {"nome": "Marchesín", "time": "Grêmio", "posicao": "Goleiro"},
    {"nome": "João Pedro", "time": "Grêmio", "posicao": "Lateral"},
    {"nome": "Kannemann", "time": "Grêmio", "posicao": "Zagueiro"},
    {"nome": "Geromel", "time": "Grêmio", "posicao": "Zagueiro"},
    {"nome": "Reinaldo", "time": "Grêmio", "posicao": "Lateral"},
    {"nome": "Villasanti", "time": "Grêmio", "posicao": "Volante"},
    {"nome": "Pepê", "time": "Grêmio", "posicao": "Meia"},
    {"nome": "Cristaldo", "time": "Grêmio", "posicao": "Meia"},
    {"nome": "Soteldo", "time": "Grêmio", "posicao": "Atacante"},
    {"nome": "Diego Costa", "time": "Grêmio", "posicao": "Atacante"},
    
    # Internacional
    {"nome": "Fabrício", "time": "Internacional", "posicao": "Goleiro"},
    {"nome": "Bustos", "time": "Internacional", "posicao": "Lateral"},
    {"nome": "Vitão", "time": "Internacional", "posicao": "Zagueiro"},
    {"nome": "Mercado", "time": "Internacional", "posicao": "Zagueiro"},
    {"nome": "Renê", "time": "Internacional", "posicao": "Lateral"},
    {"nome": "Fernando", "time": "Internacional", "posicao": "Volante"},
    {"nome": "Thiago Maia", "time": "Internacional", "posicao": "Volante"},
    {"nome": "Alan Patrick", "time": "Internacional", "posicao": "Meia"},
    {"nome": "Wesley", "time": "Internacional", "posicao": "Atacante"},
    {"nome": "Borré", "time": "Internacional", "posicao": "Atacante"},
    
    # Fluminense
    {"nome": "Fábio", "time": "Fluminense", "posicao": "Goleiro"},
    {"nome": "Samuel Xavier", "time": "Fluminense", "posicao": "Lateral"},
    {"nome": "Thiago Silva", "time": "Fluminense", "posicao": "Zagueiro"},
    {"nome": "Thiago Santos", "time": "Fluminense", "posicao": "Zagueiro"},
    {"nome": "Marcelo", "time": "Fluminense", "posicao": "Lateral"},
    {"nome": "André", "time": "Fluminense", "posicao": "Volante"},
    {"nome": "Martinelli", "time": "Fluminense", "posicao": "Volante"},
    {"nome": "Ganso", "time": "Fluminense", "posicao": "Meia"},
    {"nome": "Arias", "time": "Fluminense", "posicao": "Atacante"},
    {"nome": "Cano", "time": "Fluminense", "posicao": "Atacante"},
    
    # Corinthians
    {"nome": "Cássio", "time": "Corinthians", "posicao": "Goleiro"},
    {"nome": "Fagner", "time": "Corinthians", "posicao": "Lateral"},
    {"nome": "Gil", "time": "Corinthians", "posicao": "Zagueiro"},
    {"nome": "Cacá", "time": "Corinthians", "posicao": "Zagueiro"},
    {"nome": "Matheus Bidu", "time": "Corinthians", "posicao": "Lateral"},
    {"nome": "Raniele", "time": "Corinthians", "posicao": "Volante"},
    {"nome": "Breno Bidon", "time": "Corinthians", "posicao": "Volante"},
    {"nome": "Rodrigo Garro", "time": "Corinthians", "posicao": "Meia"},
    {"nome": "Yuri Alberto", "time": "Corinthians", "posicao": "Atacante"},
    {"nome": "Memphis Depay", "time": "Corinthians", "posicao": "Atacante"},
    
    # Atlético Mineiro
    {"nome": "Everson", "time": "Atlético Mineiro", "posicao": "Goleiro"},
    {"nome": "Saravia", "time": "Atlético Mineiro", "posicao": "Lateral"},
    {"nome": "Bruno Fuchs", "time": "Atlético Mineiro", "posicao": "Zagueiro"},
    {"nome": "Jemerson", "time": "Atlético Mineiro", "posicao": "Zagueiro"},
    {"nome": "Guilherme Arana", "time": "Atlético Mineiro", "posicao": "Lateral"},
    {"nome": "Otávio", "time": "Atlético Mineiro", "posicao": "Volante"},
    {"nome": "Alan Franco", "time": "Atlético Mineiro", "posicao": "Volante"},
    {"nome": "Gustavo Scarpa", "time": "Atlético Mineiro", "posicao": "Meia"},
    {"nome": "Hulk", "time": "Atlético Mineiro", "posicao": "Atacante"},
    {"nome": "Paulinho", "time": "Atlético Mineiro", "posicao": "Atacante"},
    
    # Cruzeiro
    {"nome": "Cássio", "time": "Cruzeiro", "posicao": "Goleiro"},
    {"nome": "William", "time": "Cruzeiro", "posicao": "Lateral"},
    {"nome": "João Marcelo", "time": "Cruzeiro", "posicao": "Zagueiro"},
    {"nome": "Zé Ivaldo", "time": "Cruzeiro", "posicao": "Zagueiro"},
    {"nome": "Marlon", "time": "Cruzeiro", "posicao": "Lateral"},
    {"nome": "Lucas Romero", "time": "Cruzeiro", "posicao": "Volante"},
    {"nome": "Matheus Henrique", "time": "Cruzeiro", "posicao": "Volante"},
    {"nome": "Matheus Pereira", "time": "Cruzeiro", "posicao": "Meia"},
    {"nome": "Gabriel Veron", "time": "Cruzeiro", "posicao": "Atacante"},
    {"nome": "Lautaro Díaz", "time": "Cruzeiro", "posicao": "Atacante"},
    
    # Bahia
    {"nome": "Marcos Felipe", "time": "Bahia", "posicao": "Goleiro"},
    {"nome": "Gilberto", "time": "Bahia", "posicao": "Lateral"},
    {"nome": "Gabriel Xavier", "time": "Bahia", "posicao": "Zagueiro"},
    {"nome": "Kanu", "time": "Bahia", "posicao": "Zagueiro"},
    {"nome": "Luciano Juba", "time": "Bahia", "posicao": "Lateral"},
    {"nome": "Caio Alexandre", "time": "Bahia", "posicao": "Volante"},
    {"nome": "Jean Lucas", "time": "Bahia", "posicao": "Volante"},
    {"nome": "Everton Ribeiro", "time": "Bahia", "posicao": "Meia"},
    {"nome": "Cauly", "time": "Bahia", "posicao": "Meia"},
    {"nome": "Everaldo", "time": "Bahia", "posicao": "Atacante"},
    
    # Vasco da Gama
    {"nome": "Léo Jardim", "time": "Vasco da Gama", "posicao": "Goleiro"},
    {"nome": "Paulo Henrique", "time": "Vasco da Gama", "posicao": "Lateral"},
    {"nome": "Maicon", "time": "Vasco da Gama", "posicao": "Zagueiro"},
    {"nome": "Léo", "time": "Vasco da Gama", "posicao": "Zagueiro"},
    {"nome": "Lucas Piton", "time": "Vasco da Gama", "posicao": "Lateral"},
    {"nome": "Hugo Moura", "time": "Vasco da Gama", "posicao": "Volante"},
    {"nome": "Mateus Carvalho", "time": "Vasco da Gama", "posicao": "Volante"},
    {"nome": "Philippe Coutinho", "time": "Vasco da Gama", "posicao": "Meia"},
    {"nome": "Payet", "time": "Vasco da Gama", "posicao": "Meia"},
    {"nome": "Vegetti", "time": "Vasco da Gama", "posicao": "Atacante"},
    
    # Athletico Paranaense
    {"nome": "Léo Linck", "time": "Athletico Paranaense", "posicao": "Goleiro"},
    {"nome": "Madson", "time": "Athletico Paranaense", "posicao": "Lateral"},
    {"nome": "Kaique Rocha", "time": "Athletico Paranaense", "posicao": "Zagueiro"},
    {"nome": "Thiago Heleno", "time": "Athletico Paranaense", "posicao": "Zagueiro"},
    {"nome": "Fernando", "time": "Athletico Paranaense", "posicao": "Lateral"},
    {"nome": "Erick", "time": "Athletico Paranaense", "posicao": "Volante"},
    {"nome": "Fernandinho", "time": "Athletico Paranaense", "posicao": "Volante"},
    {"nome": "Christian", "time": "Athletico Paranaense", "posicao": "Meia"},
    {"nome": "Canobbio", "time": "Athletico Paranaense", "posicao": "Atacante"},
    {"nome": "Pablo", "time": "Athletico Paranaense", "posicao": "Atacante"},
    
    # Fortaleza
    {"nome": "João Ricardo", "time": "Fortaleza", "posicao": "Goleiro"},
    {"nome": "Tinga", "time": "Fortaleza", "posicao": "Lateral"},
    {"nome": "Brítez", "time": "Fortaleza", "posicao": "Zagueiro"},
    {"nome": "Titi", "time": "Fortaleza", "posicao": "Zagueiro"},
    {"nome": "Bruno Pacheco", "time": "Fortaleza", "posicao": "Lateral"},
    {"nome": "Lucas Sasha", "time": "Fortaleza", "posicao": "Volante"},
    {"nome": "Hércules", "time": "Fortaleza", "posicao": "Volante"},
    {"nome": "Pochettino", "time": "Fortaleza", "posicao": "Meia"},
    {"nome": "Pikachu", "time": "Fortaleza", "posicao": "Atacante"},
    {"nome": "Lucero", "time": "Fortaleza", "posicao": "Atacante"},
    
    # Bragantino
    {"nome": "Cleiton", "time": "Bragantino", "posicao": "Goleiro"},
    {"nome": "Nathan Mendes", "time": "Bragantino", "posicao": "Lateral"},
    {"nome": "Douglas Mendes", "time": "Bragantino", "posicao": "Zagueiro"},
    {"nome": "Eduardo Santos", "time": "Bragantino", "posicao": "Zagueiro"},
    {"nome": "Juninho Capixaba", "time": "Bragantino", "posicao": "Lateral"},
    {"nome": "Eric Ramires", "time": "Bragantino", "posicao": "Volante"},
    {"nome": "Jadsom", "time": "Bragantino", "posicao": "Volante"},
    {"nome": "Lincoln", "time": "Bragantino", "posicao": "Meia"},
    {"nome": "Vitinho", "time": "Bragantino", "posicao": "Atacante"},
    {"nome": "Eduardo Sasha", "time": "Bragantino", "posicao": "Atacante"},
]

def adicionar_estatisticas_padrao(jogador):
    """Adiciona estatísticas zeradas ao jogador"""
    return {
        **jogador,
        "gols": 0,
        "assistencias": 0,
        "cartoes_amarelos": 0,
        "cartoes_vermelhos": 0,
        "faltas_cometidas": 0,
        "faltas_sofridas": 0,
        "chutes": 0,
        "chutes_no_gol": 0,
        "desarmes": 0
    }

def carregar_jogadores_existentes():
    """Carrega jogadores já existentes"""
    if not os.path.exists(jogadores_path):
        return []
    with open(jogadores_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_jogadores(jogadores):
    """Salva os jogadores no arquivo JSON"""
    os.makedirs(os.path.dirname(jogadores_path), exist_ok=True)
    with open(jogadores_path, 'w', encoding='utf-8') as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=2)

def adicionar_jogadores_brasileirao():
    """Adiciona todos os jogadores dos times do Brasileirão"""
    print("⚽ Adicionando jogadores do Brasileirão 2025...")
    
    jogadores_existentes = carregar_jogadores_existentes()
    
    # Criar chave única para verificar duplicatas
    chaves_existentes = {f"{j['nome'].lower()}_{j['time'].lower()}" for j in jogadores_existentes}
    
    jogadores_adicionados = 0
    jogadores_ignorados = 0
    
    for jogador in JOGADORES_BRASILEIRAO_2025:
        chave = f"{jogador['nome'].lower()}_{jogador['time'].lower()}"
        
        if chave in chaves_existentes:
            jogadores_ignorados += 1
        else:
            jogador_completo = adicionar_estatisticas_padrao(jogador)
            jogadores_existentes.append(jogador_completo)
            jogadores_adicionados += 1
            if jogadores_adicionados % 20 == 0:
                print(f"   ✅ {jogadores_adicionados} jogadores adicionados...")
    
    # Salvar todos os jogadores
    salvar_jogadores(jogadores_existentes)
    
    print(f"\n🎉 Processo concluído!")
    print(f"   ✅ Jogadores adicionados: {jogadores_adicionados}")
    print(f"   ⚠️  Jogadores já existentes: {jogadores_ignorados}")
    print(f"   📊 Total de jogadores no sistema: {len(jogadores_existentes)}")
    print(f"\n💡 Os jogadores foram adicionados com estatísticas zeradas.")
    print(f"   Você pode atualizar as estatísticas posteriormente pela interface!")

if __name__ == "__main__":
    adicionar_jogadores_brasileirao()
