import os
from models import carregar_json, Jogador, Time

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')
times_path = os.path.join(data_dir, 'times.json')

def calcular_media(lista, campo):
    valores = [item.get(campo, 0) for item in lista if campo in item]
    return sum(valores) / len(valores) if valores else 0

def analisar_time(time_dict):
    jogadores = time_dict['jogadores']
    stats = {
        'media_gols': calcular_media(jogadores, 'gols'),
        'media_assistencias': calcular_media(jogadores, 'assistencias'),
        'media_cartoes_amarelos': calcular_media(jogadores, 'cartoes_amarelos'),
        'media_cartoes_vermelhos': calcular_media(jogadores, 'cartoes_vermelhos'),
        'media_faltas_cometidas': calcular_media(jogadores, 'faltas_cometidas'),
        'media_faltas_sofridas': calcular_media(jogadores, 'faltas_sofridas'),
        'media_chutes': calcular_media(jogadores, 'chutes'),
        'media_chutes_no_gol': calcular_media(jogadores, 'chutes_no_gol'),
        'media_desarmes': calcular_media(jogadores, 'desarmes'),
    }
    return stats

def exibir_estatisticas():
    times = carregar_json(times_path)
    if not times:
        print('Nenhum time cadastrado!')
        return
    print('Times disponíveis:')
    for idx, t in enumerate(times):
        print(f'{idx+1}: {t["nome"]}')
    idx_a = int(input('Escolha o número do Time A: ')) - 1
    idx_b = int(input('Escolha o número do Time B: ')) - 1
    time_a = times[idx_a]
    time_b = times[idx_b]
    stats_a = analisar_time(time_a)
    stats_b = analisar_time(time_b)
    print(f'\nEstatísticas do {time_a["nome"]}:')
    for k, v in stats_a.items():
        print(f'{k}: {v:.2f}')
    print(f'\nEstatísticas do {time_b["nome"]}:')
    for k, v in stats_b.items():
        print(f'{k}: {v:.2f}')

def main():
    exibir_estatisticas()

if __name__ == '__main__':
    main()
