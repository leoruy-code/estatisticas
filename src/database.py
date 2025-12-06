"""
Módulo de conexão e operações com PostgreSQL
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import json

# Configuração do banco
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'estatisticas')
DB_USER = os.getenv('DB_USER', 'estatisticas_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'estatisticas_pass')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine e Session
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Context manager para sessão do banco"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def inserir_time(nome, imagem_url=None):
    """Insere ou atualiza um time"""
    with get_db() as db:
        result = db.execute(
            text("""
                INSERT INTO times (nome, imagem_url)
                VALUES (:nome, :imagem_url)
                ON CONFLICT (nome) DO UPDATE SET
                    imagem_url = EXCLUDED.imagem_url,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """),
            {"nome": nome, "imagem_url": imagem_url}
        )
        return result.scalar()

def inserir_jogador(jogador_data):
    """Insere ou atualiza um jogador"""
    with get_db() as db:
        # Primeiro, garantir que o time existe
        time_id = db.execute(
            text("SELECT id FROM times WHERE nome = :nome"),
            {"nome": jogador_data['time']}
        ).scalar()
        
        if not time_id:
            time_id = inserir_time(jogador_data['time'])
        
        # Preparar dados do jogador
        jogador_data['time_id'] = time_id
        
        # Inserir ou atualizar jogador
        db.execute(
            text("""
                INSERT INTO jogadores (
                    nome, time_id, posicao, foto_url, sofascore_id,
                    gols, assistencias, partidas, minutos_jogados,
                    cartoes_amarelos, cartoes_vermelhos,
                    faltas_cometidas, faltas_sofridas,
                    chutes, chutes_no_gol, grandes_chances_perdidas, grandes_chances_criadas,
                    gols_esperados, conversao_gols,
                    desarmes, interceptacoes, defesas, gols_sofridos,
                    passes_certos, total_passes, passes_decisivos, assistencias_esperadas,
                    passes_longos_certos, cruzamentos_certos,
                    dribles_certos, total_dribles, duelos_ganhos, duelos_totais,
                    duelos_aereos_ganhos, duelos_terrestres_ganhos,
                    posse_perdida, erros_finalizacao, erros_gol, impedimentos,
                    penaltis_marcados, penaltis_sofridos, penaltis_cometidos,
                    rating
                ) VALUES (
                    :nome, :time_id, :posicao, :foto_url, :sofascore_id,
                    :gols, :assistencias, :partidas, :minutos_jogados,
                    :cartoes_amarelos, :cartoes_vermelhos,
                    :faltas_cometidas, :faltas_sofridas,
                    :chutes, :chutes_no_gol, :grandes_chances_perdidas, :grandes_chances_criadas,
                    :gols_esperados, :conversao_gols,
                    :desarmes, :interceptacoes, :defesas, :gols_sofridos,
                    :passes_certos, :total_passes, :passes_decisivos, :assistencias_esperadas,
                    :passes_longos_certos, :cruzamentos_certos,
                    :dribles_certos, :total_dribles, :duelos_ganhos, :duelos_totais,
                    :duelos_aereos_ganhos, :duelos_terrestres_ganhos,
                    :posse_perdida, :erros_finalizacao, :erros_gol, :impedimentos,
                    :penaltis_marcados, :penaltis_sofridos, :penaltis_cometidos,
                    :rating
                )
                ON CONFLICT (nome, time_id) DO UPDATE SET
                    posicao = EXCLUDED.posicao,
                    foto_url = EXCLUDED.foto_url,
                    sofascore_id = EXCLUDED.sofascore_id,
                    gols = EXCLUDED.gols,
                    assistencias = EXCLUDED.assistencias,
                    partidas = EXCLUDED.partidas,
                    minutos_jogados = EXCLUDED.minutos_jogados,
                    cartoes_amarelos = EXCLUDED.cartoes_amarelos,
                    cartoes_vermelhos = EXCLUDED.cartoes_vermelhos,
                    faltas_cometidas = EXCLUDED.faltas_cometidas,
                    faltas_sofridas = EXCLUDED.faltas_sofridas,
                    chutes = EXCLUDED.chutes,
                    chutes_no_gol = EXCLUDED.chutes_no_gol,
                    grandes_chances_perdidas = EXCLUDED.grandes_chances_perdidas,
                    grandes_chances_criadas = EXCLUDED.grandes_chances_criadas,
                    gols_esperados = EXCLUDED.gols_esperados,
                    conversao_gols = EXCLUDED.conversao_gols,
                    desarmes = EXCLUDED.desarmes,
                    interceptacoes = EXCLUDED.interceptacoes,
                    defesas = EXCLUDED.defesas,
                    gols_sofridos = EXCLUDED.gols_sofridos,
                    passes_certos = EXCLUDED.passes_certos,
                    total_passes = EXCLUDED.total_passes,
                    passes_decisivos = EXCLUDED.passes_decisivos,
                    assistencias_esperadas = EXCLUDED.assistencias_esperadas,
                    passes_longos_certos = EXCLUDED.passes_longos_certos,
                    cruzamentos_certos = EXCLUDED.cruzamentos_certos,
                    dribles_certos = EXCLUDED.dribles_certos,
                    total_dribles = EXCLUDED.total_dribles,
                    duelos_ganhos = EXCLUDED.duelos_ganhos,
                    duelos_totais = EXCLUDED.duelos_totais,
                    duelos_aereos_ganhos = EXCLUDED.duelos_aereos_ganhos,
                    duelos_terrestres_ganhos = EXCLUDED.duelos_terrestres_ganhos,
                    posse_perdida = EXCLUDED.posse_perdida,
                    erros_finalizacao = EXCLUDED.erros_finalizacao,
                    erros_gol = EXCLUDED.erros_gol,
                    impedimentos = EXCLUDED.impedimentos,
                    penaltis_marcados = EXCLUDED.penaltis_marcados,
                    penaltis_sofridos = EXCLUDED.penaltis_sofridos,
                    penaltis_cometidos = EXCLUDED.penaltis_cometidos,
                    rating = EXCLUDED.rating,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {
                **jogador_data,
                'sofascore_id': jogador_data.get('id'),
                'posicao': jogador_data.get('posicao', ''),
                'foto_url': jogador_data.get('foto_url'),
                'gols': jogador_data.get('gols', 0),
                'assistencias': jogador_data.get('assistencias', 0),
                'partidas': jogador_data.get('partidas', 0),
                'minutos_jogados': jogador_data.get('minutos_jogados', 0),
                'cartoes_amarelos': jogador_data.get('cartoes_amarelos', 0),
                'cartoes_vermelhos': jogador_data.get('cartoes_vermelhos', 0),
                'faltas_cometidas': jogador_data.get('faltas_cometidas', 0),
                'faltas_sofridas': jogador_data.get('faltas_sofridas', 0),
                'chutes': jogador_data.get('chutes', 0),
                'chutes_no_gol': jogador_data.get('chutes_no_gol', 0),
                'grandes_chances_perdidas': jogador_data.get('grandes_chances_perdidas', 0),
                'grandes_chances_criadas': jogador_data.get('grandes_chances_criadas', 0),
                'gols_esperados': jogador_data.get('gols_esperados', 0),
                'conversao_gols': jogador_data.get('conversao_gols', 0),
                'desarmes': jogador_data.get('desarmes', 0),
                'interceptacoes': jogador_data.get('interceptacoes', 0),
                'defesas': jogador_data.get('defesas', 0),
                'gols_sofridos': jogador_data.get('gols_sofridos', 0),
                'passes_certos': jogador_data.get('passes_certos', 0),
                'total_passes': jogador_data.get('total_passes', 0),
                'passes_decisivos': jogador_data.get('passes_decisivos', 0),
                'assistencias_esperadas': jogador_data.get('assistencias_esperadas', 0),
                'passes_longos_certos': jogador_data.get('passes_longos_certos', 0),
                'cruzamentos_certos': jogador_data.get('cruzamentos_certos', 0),
                'dribles_certos': jogador_data.get('dribles_certos', 0),
                'total_dribles': jogador_data.get('total_dribles', 0),
                'duelos_ganhos': jogador_data.get('duelos_ganhos', 0),
                'duelos_totais': jogador_data.get('duelos_totais', 0),
                'duelos_aereos_ganhos': jogador_data.get('duelos_aereos_ganhos', 0),
                'duelos_terrestres_ganhos': jogador_data.get('duelos_terrestres_ganhos', 0),
                'posse_perdida': jogador_data.get('posse_perdida', 0),
                'erros_finalizacao': jogador_data.get('erros_finalizacao', 0),
                'erros_gol': jogador_data.get('erros_gol', 0),
                'impedimentos': jogador_data.get('impedimentos', 0),
                'penaltis_marcados': jogador_data.get('penaltis_marcados', 0),
                'penaltis_sofridos': jogador_data.get('penaltis_sofridos', 0),
                'penaltis_cometidos': jogador_data.get('penaltis_cometidos', 0),
                'rating': jogador_data.get('rating', 0),
            }
        )

def buscar_times():
    """Retorna todos os times"""
    with get_db() as db:
        result = db.execute(text("SELECT * FROM estatisticas_times ORDER BY nome"))
        return [dict(row._mapping) for row in result]

def buscar_jogadores_time(time_nome):
    """Retorna todos os jogadores de um time"""
    with get_db() as db:
        result = db.execute(
            text("""
                SELECT j.* FROM jogadores j
                JOIN times t ON j.time_id = t.id
                WHERE t.nome = :nome
                ORDER BY j.rating DESC, j.gols DESC
            """),
            {"nome": time_nome}
        )
        return [dict(row._mapping) for row in result]

def buscar_top_artilheiros(limit=10):
    """Retorna top artilheiros"""
    with get_db() as db:
        result = db.execute(
            text("""
                SELECT j.nome, t.nome as time, j.gols, j.partidas, j.rating
                FROM jogadores j
                JOIN times t ON j.time_id = t.id
                WHERE j.partidas > 0
                ORDER BY j.gols DESC, j.rating DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        return [dict(row._mapping) for row in result]

def migrar_json_para_db():
    """Migra dados do JSON para o banco de dados"""
    print("🔄 MIGRANDO DADOS DO JSON PARA POSTGRESQL")
    print("=" * 70)
    
    # Carregar dados JSON
    with open('../data/times.json', 'r', encoding='utf-8') as f:
        times_json = json.load(f)
    
    with open('../data/jogadores.json', 'r', encoding='utf-8') as f:
        jogadores_json = json.load(f)
    
    print(f"📊 Times no JSON: {len(times_json)}")
    print(f"📊 Jogadores no JSON: {len(jogadores_json)}")
    print()
    
    # Inserir times
    print("⏳ Inserindo times...")
    times_inseridos = 0
    for time in times_json:
        try:
            inserir_time(time['nome'], time.get('imagem'))
            times_inseridos += 1
        except Exception as e:
            print(f"❌ Erro ao inserir time {time['nome']}: {e}")
    
    print(f"✅ Times inseridos: {times_inseridos}")
    print()
    
    # Inserir jogadores
    print("⏳ Inserindo jogadores...")
    jogadores_inseridos = 0
    for jogador in jogadores_json:
        try:
            inserir_jogador(jogador)
            jogadores_inseridos += 1
            if jogadores_inseridos % 100 == 0:
                print(f"   Processados: {jogadores_inseridos}...")
        except Exception as e:
            print(f"❌ Erro ao inserir {jogador.get('nome')}: {e}")
    
    print(f"✅ Jogadores inseridos: {jogadores_inseridos}")
    print()
    print("🎉 MIGRAÇÃO CONCLUÍDA!")
