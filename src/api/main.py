"""
FastAPI Backend - RAG Estatísticas

API REST para previsões de partidas de futebol.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.league_stats import LeagueStats
from core.team_model import TeamModel
from core.player_model import PlayerModel
from engine.parameters import ParameterCalculator
from engine.monte_carlo import MonteCarloSimulator
from engine.context import MatchContext, TipoCompeticao, ImportanciaJogo
from engine.lineup_adjuster import LineupAdjuster
from analysis.predictions import MatchPredictor
from analysis.calibration import ModelCalibrator

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'estatisticas'),
    'user': os.getenv('DB_USER', 'estatisticas_user'),
    'password': os.getenv('DB_PASS', 'estatisticas_pass')
}

# Inicializar FastAPI
app = FastAPI(
    title="RAG Estatísticas",
    description="API para previsões de partidas de futebol usando Monte Carlo",
    version="2.0.0"
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# Inicializar componentes (lazy loading)
_predictor = None
_calibrator = None


def get_predictor() -> MatchPredictor:
    global _predictor
    if _predictor is None:
        _predictor = MatchPredictor(DB_CONFIG, n_simulations=50_000)
    return _predictor


def get_calibrator() -> ModelCalibrator:
    global _calibrator
    if _calibrator is None:
        _calibrator = ModelCalibrator(DB_CONFIG, get_predictor())
    return _calibrator


# ==================== SCHEMAS ====================

class PredictionRequest(BaseModel):
    mandante_id: int
    visitante_id: int
    league_id: int = 1
    lineup_mandante: Optional[List[int]] = None
    lineup_visitante: Optional[List[int]] = None
    tipo_competicao: Optional[str] = "pontos_corridos"
    n_simulations: Optional[int] = 50_000  # Número de simulações Monte Carlo


class TeamResponse(BaseModel):
    id: int
    nome: str
    ataque: float
    defesa: float
    confianca: float


# ==================== ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página inicial - serve o frontend."""
    with open("src/frontend/templates/index.html", "r") as f:
        return f.read()


@app.get("/api/health")
async def health_check():
    """Verifica se a API está funcionando."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/teams")
async def get_teams(league_id: int = 1):
    """Lista todos os times de uma liga."""
    try:
        predictor = get_predictor()
        teams = predictor.team_model.get_all_teams_strength(league_id)
        
        return {
            "teams": [
                {
                    "id": t.team_id,
                    "nome": t.team_name,
                    "ataque": round(float(t.ataque_geral), 2),
                    "defesa": round(float(t.defesa_geral), 2),
                    "jogos": t.jogos_casa + t.jogos_fora,
                    "confianca": round(float(t.confianca) * 100, 0)
                }
                for t in teams
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_id}")
async def get_team_detail(team_id: int, league_id: int = 1):
    """Detalhes de um time específico."""
    try:
        predictor = get_predictor()
        team = predictor.team_model.calculate_team_strength(team_id, league_id)
        players = predictor.player_model.get_team_players_ratings(team_id)
        
        return {
            "team": {
                "id": team.team_id,
                "nome": team.team_name,
                "ataque_casa": round(float(team.ataque_casa), 2),
                "ataque_fora": round(float(team.ataque_fora), 2),
                "defesa_casa": round(float(team.defesa_casa), 2),
                "defesa_fora": round(float(team.defesa_fora), 2),
                "jogos_casa": team.jogos_casa,
                "jogos_fora": team.jogos_fora,
                "confianca": round(float(team.confianca) * 100, 0)
            },
            "jogadores": [
                {
                    "id": p.player_id,
                    "nome": p.nome,
                    "posicao": p.posicao,
                    "rating": round(float(p.rating_geral), 1),
                    "ataque": round(float(p.rating_ataque), 1),
                    "defesa": round(float(p.rating_defesa), 1)
                }
                for p in sorted(players, key=lambda x: x.rating_geral, reverse=True)[:20]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict")
async def predict_match(request: PredictionRequest):
    """
    Gera previsão completa para uma partida.
    
    Retorna probabilidades de resultado, gols, cartões e escanteios.
    """
    try:
        # Usar predictor customizado se n_simulations diferente do padrão
        if request.n_simulations and request.n_simulations != 50_000:
            predictor = MatchPredictor(DB_CONFIG, n_simulations=request.n_simulations)
        else:
            predictor = get_predictor()
        
        # Criar contexto se especificado
        context = None
        if request.tipo_competicao:
            tipo_map = {
                "pontos_corridos": TipoCompeticao.PONTOS_CORRIDOS,
                "mata_mata": TipoCompeticao.MATA_MATA,
                "grupo": TipoCompeticao.GRUPO
            }
            context = MatchContext(
                mandante_id=request.mandante_id,
                visitante_id=request.visitante_id,
                league_id=request.league_id,
                competicao=tipo_map.get(request.tipo_competicao, TipoCompeticao.PONTOS_CORRIDOS)
            )
        
        prediction = predictor.predict(
            mandante_id=request.mandante_id,
            visitante_id=request.visitante_id,
            league_id=request.league_id,
            context=context,
            lineup_mandante=request.lineup_mandante,
            lineup_visitante=request.lineup_visitante
        )
        
        return prediction.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predict/quick")
async def predict_quick(
    mandante_id: int,
    visitante_id: int,
    league_id: int = 1
):
    """Previsão rápida (só probabilidades de resultado)."""
    try:
        predictor = get_predictor()
        result = predictor.predict_quick(mandante_id, visitante_id, league_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Retorna estatísticas gerais do sistema."""
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Total de partidas
        cursor.execute("""
            SELECT COUNT(*) FROM matches 
            WHERE sofascore_event_id IS NOT NULL
        """)
        total_partidas = cursor.fetchone()[0]
        
        # Competições
        cursor.execute("""
            SELECT COUNT(DISTINCT liga) FROM matches 
            WHERE sofascore_event_id IS NOT NULL
        """)
        competicoes = cursor.fetchone()[0]
        
        # Times ativos
        cursor.execute("SELECT COUNT(*) FROM teams WHERE ativo = true")
        times_ativos = cursor.fetchone()[0]
        
        # Total jogadores
        cursor.execute("SELECT COUNT(DISTINCT id) FROM players")
        total_jogadores = cursor.fetchone()[0]
        
        # Por competição
        cursor.execute("""
            SELECT 
                liga,
                COUNT(*) as partidas
            FROM matches 
            WHERE sofascore_event_id IS NOT NULL
            GROUP BY liga
            ORDER BY partidas DESC
        """)
        por_competicao = [
            {"liga": row[0], "partidas": row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "total_partidas": total_partidas,
            "competicoes": competicoes,
            "times_ativos": times_ativos,
            "total_jogadores": total_jogadores,
            "por_competicao": por_competicao
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/league/stats")
async def get_league_stats(league_id: int = 1, temporada: str = "2025"):
    """Retorna estatísticas da liga (médias de referência)."""
    try:
        predictor = get_predictor()
        stats = predictor.league_stats.calculate_averages(league_id, temporada)
        variance = predictor.league_stats.get_variance_stats(league_id, temporada)
        
        return {
            "medias": {
                "gols_mandante": round(stats.gols_mandante, 2),
                "gols_visitante": round(stats.gols_visitante, 2),
                "gols_total": round(stats.gols_total, 2),
                "cartoes_total": round(stats.cartoes_total, 2),
                "escanteios_total": round(stats.escanteios_total, 2)
            },
            "total_jogos": stats.total_jogos,
            "variancia": variance,
            "temporada": temporada
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calibration")
async def get_calibration(league_id: int = 1):
    """Retorna métricas de calibração do modelo."""
    try:
        calibrator = get_calibrator()
        result = calibrator.calibrate(league_id)
        suggestions = calibrator.suggest_adjustments(result)
        
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/simulate")
async def simulate_manual(
    lambda_mandante: float = Query(1.5, ge=0.1, le=5.0),
    lambda_visitante: float = Query(1.0, ge=0.1, le=5.0),
    n_simulations: int = Query(10000, ge=1000, le=100000)
):
    """
    Simulação manual com parâmetros customizados.
    
    Útil para testes e análises.
    """
    try:
        simulator = MonteCarloSimulator(n_simulations)
        result = simulator.quick_simulate(lambda_mandante, lambda_visitante)
        
        return {
            "parametros": {
                "lambda_mandante": lambda_mandante,
                "lambda_visitante": lambda_visitante,
                "n_simulations": n_simulations
            },
            "resultado": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{team_id}")
async def get_team_players(team_id: int):
    """Lista jogadores de um time com ratings."""
    try:
        predictor = get_predictor()
        players = predictor.player_model.get_team_players_ratings(team_id)
        
        return {
            "jogadores": [
                {
                    "id": p.player_id,
                    "nome": p.nome,
                    "posicao": p.posicao,
                    "rating_geral": round(p.rating_geral, 1),
                    "rating_ataque": round(p.rating_ataque, 1),
                    "rating_defesa": round(p.rating_defesa, 1),
                    "rating_disciplina": round(p.rating_disciplina, 1),
                    "gols_p90": round(p.gols_p90, 2),
                    "assistencias_p90": round(p.assistencias_p90, 2),
                    "jogos": p.jogos
                }
                for p in sorted(players, key=lambda x: x.rating_geral, reverse=True)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
