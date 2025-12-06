import json
import os
from models import Jogador, Time, salvar_json, carregar_json

data_dir = os.path.join(os.path.dirname(__file__), '../data')
jogadores_path = os.path.join(data_dir, 'jogadores.json')
times_path = os.path.join(data_dir, 'times.json')

def carregar_lista(caminho):
    if not os.path.exists(caminho):
        return []
    return carregar_json(caminho)

def salvar_lista(lista, caminho):
    salvar_json(lista, caminho)

def add_jogador():
    nome = input('Nome do jogador: ')
    time = input('Time: ')
    # Apenas campos essenciais via input manual - o resto vem do scraper
    gols = int(input('Gols feitos: ') or 0)
    assistencias = int(input('Assistências: ') or 0)
    cartoes_amarelos = int(input('Cartões amarelos: ') or 0)
    cartoes_vermelhos = int(input('Cartões vermelhos: ') or 0)
    
    # Criar jogador com valores padrão para campos avançados
    jogador = Jogador(
        nome=nome, 
        time=time, 
        gols=gols, 
        assistencias=assistencias, 
        cartoes_amarelos=cartoes_amarelos, 
        cartoes_vermelhos=cartoes_vermelhos
    )
    jogadores = carregar_lista(jogadores_path)
    jogadores.append(jogador.to_dict())
    salvar_lista(jogadores, jogadores_path)
    print(f'Jogador {nome} adicionado!')

def add_time():
    nome = input('Nome do time: ')
    jogadores = carregar_lista(jogadores_path)
    if not jogadores:
        print('Nenhum jogador cadastrado!')
        return
    print('Jogadores disponíveis:')
    for idx, j in enumerate(jogadores):
        print(f'{idx+1}: {j["nome"]}')
    idxs = input('Digite os números dos jogadores do time separados por vírgula: ')
    idxs = [int(i.strip())-1 for i in idxs.split(',') if i.strip().isdigit()]
    jogadores_time = [Jogador(**j) for i, j in enumerate(jogadores) if i in idxs]
    time = Time(nome, jogadores_time)
    times = carregar_lista(times_path)
    times.append(time.to_dict())
    salvar_lista(times, times_path)
    print(f'Time {nome} adicionado!')

def main():
    print('1. Adicionar jogador')
    print('2. Adicionar time')
    op = input('Escolha uma opção: ')
    if op == '1':
        add_jogador()
    elif op == '2':
        add_time()
    else:
        print('Opção inválida!')

if __name__ == '__main__':
    main()
