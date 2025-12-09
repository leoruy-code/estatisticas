"""
RAG Estatísticas - Flamengo
Frontend moderno e simples
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# ==================== CONFIG ====================

st.set_page_config(
    page_title="Flamengo - Estatísticas 2025",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estatisticas',
    'user': 'estatisticas_user',
    'password': 'estatisticas_pass'
}

# ==================== STYLES ====================

st.markdown("""
<style>
    /* Remover padding padrão */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    
    /* Header customizado */
    .header-container {
        background: linear-gradient(135deg, #E3000F 0%, #000000 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: #FFD700;
        font-size: 1.2rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Cards de estatísticas */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #E3000F;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(227,0,15,0.2);
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stat-value {
        color: #E3000F;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .stat-subtitle {
        color: #999;
        font-size: 0.85rem;
    }
    
    /* Tabela de jogadores */
    .player-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Últimos jogos */
    .game-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #E3000F;
        margin-bottom: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .game-result-v {
        background: #00C851;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .game-result-e {
        background: #FFB300;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .game-result-d {
        background: #FF4444;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #E3000F 0%, #000000 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(227,0,15,0.4);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px 10px 0 0;
        padding: 1rem 2rem;
        font-weight: 600;
        border: 2px solid #f0f0f0;
    }
    
    .stTabs [aria-selected="true"] {
        background: #E3000F;
        color: white;
        border-color: #E3000F;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES ====================

def get_team_stats():
    """Busca estatísticas do time."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM team_stats WHERE team_id = 1
    """)
    stats = dict(cursor.fetchone())
    conn.close()
    return stats

def get_players_stats():
    """Busca jogadores com estatísticas."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT p.nome, p.posicao,
               ps.raw_stats
        FROM players p
        JOIN player_stats ps ON ps.player_id = p.id
        WHERE p.time_atual_id = 1
        ORDER BY (ps.raw_stats->>'nota_media')::float DESC NULLS LAST
    """)
    players = [dict(p) for p in cursor.fetchall()]
    conn.close()
    return players

# ==================== HEADER ====================

st.markdown("""
<div class="header-container">
    <h1 class="header-title">🔴⚫ FLAMENGO</h1>
    <p class="header-subtitle">Estatísticas Brasileirão 2025</p>
</div>
""", unsafe_allow_html=True)

# ==================== DADOS ====================

team_stats = get_team_stats()
players = get_players_stats()

# ==================== CONTEÚDO ====================

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🏆 Posição</div>
        <div class="stat-value">{team_stats['posicao']}º</div>
        <div class="stat-subtitle">{team_stats['pontos']} pontos</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">⚽ Gols Marcados</div>
        <div class="stat-value">{team_stats['gols_marcados_total']}</div>
        <div class="stat-subtitle">{team_stats['gols_marcados_media']:.2f} por jogo</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🥅 Gols Sofridos</div>
        <div class="stat-value">{team_stats['gols_sofridos_total']}</div>
        <div class="stat-subtitle">{team_stats['gols_sofridos_media']:.2f} por jogo</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">⭐ Nota Média</div>
        <div class="stat-value">{team_stats['nota_media']:.2f}</div>
        <div class="stat-subtitle">SofaScore</div>
    </div>
    """, unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Estatísticas", "👥 Jogadores", "📅 Últimos Jogos"])

with tab1:
    st.markdown("### 📊 Estatísticas do Time")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚽ Ataque")
        st.metric("Finalizações/jogo", f"{team_stats['chutes_for_media']:.1f}")
        st.metric("Escanteios/jogo", f"{team_stats['escanteios_for_media']:.1f}")
        st.metric("Posse de bola", f"{team_stats['posse_media']:.1f}%")
        
    with col2:
        st.markdown("#### 🛡️ Defesa")
        st.metric("Clean Sheets", team_stats['clean_sheets'])
        st.metric("Cartões/jogo", f"{team_stats['cartoes_for_media']:.1f}")
        st.metric("Faltas/jogo", f"{team_stats['faltas_for_media']:.1f}")
    
    # Stats detalhadas do raw_stats
    if team_stats['raw_stats']:
        st.markdown("---")
        st.markdown("#### 📈 Estatísticas Detalhadas")
        
        raw = team_stats['raw_stats']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Assistências", raw.get('assistencias', 0))
            st.metric("Dribles certos", raw.get('dribles_certos', 0))
            
        with col2:
            st.metric("Grandes chances", raw.get('grandes_chances_criadas', 0))
            st.metric("Passes certos", raw.get('passes_certos', 0))
            
        with col3:
            st.metric("Desarmes", raw.get('desarmes', 0))
            st.metric("Interceptações", raw.get('interceptacoes', 0))
            
        with col4:
            st.metric("Defesas", raw.get('defesas', 0))
            st.metric("Cortes", raw.get('cortes', 0))

with tab2:
    st.markdown("### 👥 Elenco - Top Jogadores")
    
    # Filtro de posição
    posicoes = ['Todas'] + sorted(list(set([p['posicao'] for p in players if p['posicao']])))
    filtro_pos = st.selectbox("Filtrar por posição:", posicoes)
    
    # Filtrar jogadores
    players_filtrados = players
    if filtro_pos != 'Todas':
        players_filtrados = [p for p in players if p['posicao'] == filtro_pos]
    
    # Mostrar jogadores
    for player in players_filtrados[:20]:
        stats = player['raw_stats']
        if stats:
            jogos = stats.get('jogos', 0)
            gols = stats.get('gols', 0)
            assists = stats.get('assistencias', 0)
            nota = stats.get('nota_media', 0)
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{player['nome']}**")
                st.caption(f"{player['posicao']}")
            with col2:
                st.metric("Jogos", jogos)
            with col3:
                st.metric("Gols", gols)
            with col4:
                st.metric("Assists", assists)
            with col5:
                st.metric("⭐", f"{nota:.2f}")
            
            st.divider()

with tab3:
    st.markdown("### 📅 Últimos 10 Jogos")
    
    if team_stats['ultimos_jogos']:
        ultimos = team_stats['ultimos_jogos']
        
        # Forma (últimos 5)
        forma = ''.join([j['resultado'] for j in ultimos[:5]])
        st.markdown(f"**Forma:** {forma}")
        st.markdown("---")
        
        for jogo in ultimos:
            resultado_class = f"game-result-{jogo['resultado'].lower()}"
            resultado_text = {'V': 'Vitória', 'E': 'Empate', 'D': 'Derrota'}[jogo['resultado']]
            
            st.markdown(f"""
            <div class="game-item">
                <div>
                    <strong>{jogo['mandante']}</strong> {jogo['placar_casa']} x {jogo['placar_fora']} <strong>{jogo['visitante']}</strong>
                </div>
                <div class="{resultado_class}">{resultado_text}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum jogo registrado ainda.")

# Footer
st.markdown("---")
st.caption("🔴⚫ Dados atualizados via SofaScore | Brasileirão 2025")
