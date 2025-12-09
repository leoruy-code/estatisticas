"""
RAG Estatísticas - Sistema de Predições Brasileirão 2025
Frontend Inovador com Design Futurístico
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# ==================== CONFIG ====================

st.set_page_config(
    page_title="⚽ Brasileirão Analytics 2025",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000/api"

# ==================== STYLES ====================

st.markdown("""
<style>
    /* Importar fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Background com gradiente */
    .stApp {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
    }
    
    /* Remover padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 1400px;
    }
    
    /* Header futurístico */
    .header-container {
        background: linear-gradient(135deg, rgba(15, 32, 39, 0.9) 0%, rgba(32, 58, 67, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00D4FF 0%, #00FF88 50%, #FFD700 100%);
    }
    
    .header-title {
        color: #FFFFFF;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        text-align: center;
        background: linear-gradient(135deg, #00D4FF 0%, #00FF88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
    }
    
    .header-subtitle {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.2rem;
        text-align: center;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Cards de predição */
    .prediction-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .prediction-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2);
        border-color: rgba(0, 212, 255, 0.3);
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 255, 136, 0.1) 100%);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 255, 136, 0.15) 100%);
        transform: scale(1.05);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #00D4FF;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    /* Probability bars */
    .prob-container {
        margin: 1.5rem 0;
    }
    
    .prob-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
    }
    
    .prob-bar {
        height: 40px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.05);
        overflow: hidden;
        position: relative;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .prob-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        transition: width 1s ease-out;
        position: relative;
    }
    
    .prob-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 50%;
        background: linear-gradient(180deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
    }
    
    .prob-home {
        background: linear-gradient(90deg, #00D4FF 0%, #0099FF 100%);
    }
    
    .prob-draw {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
    }
    
    .prob-away {
        background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%);
    }
    
    /* Team selector */
    .team-selector {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00D4FF 0%, #00FF88 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        padding: 0.5rem;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.6);
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00D4FF 0%, #00FF88 100%);
        color: white;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F2027 0%, #203A43 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(0, 212, 255, 0.1);
        border-left: 4px solid #00D4FF;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00D4FF 0%, #00FF88 100%);
        border-radius: 10px;
    }
    
    /* Glass morphism effect */
    .glass {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

@st.cache_data(ttl=300)
def get_teams():
    """Busca lista de times da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/teams", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('teams', [])
        return []
    except Exception as e:
        st.error(f"Erro ao buscar times: {str(e)}")
        return []

def predict_match(home_id: int, away_id: int, n_simulations: int = 50_000):
    """Faz predição de partida (sem cache para garantir valores únicos)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json={
                "mandante_id": home_id, 
                "visitante_id": away_id,
                "n_simulations": n_simulations
            },
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"Erro na API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro na predição: {str(e)}")
        return None

def format_percentage(value):
    """Formata percentual."""
    return f"{value:.1f}%"

# ==================== MAIN APP ====================

def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">⚽ BRASILEIRÃO ANALYTICS</h1>
        <p class="header-subtitle">Sistema Inteligente de Predições • Powered by Monte Carlo & Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown("### 📊 Sobre o Sistema")
        st.markdown("""
        <div class="info-box">
        Sistema avançado de predições utilizando:
        <br><br>
        🎲 <b>Monte Carlo</b><br>
        🤖 <b>Machine Learning</b><br>
        📈 <b>453 partidas</b> analisadas<br>
        🏆 <b>22 competições</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Configurações")
        
        # Controle de simulações
        st.markdown("#### 🎲 Simulações Monte Carlo")
        n_simulations = st.select_slider(
            "Quantidade de simulações",
            options=[10_000, 25_000, 50_000, 100_000, 250_000, 500_000],
            value=50_000,
            format_func=lambda x: f"{x:,}".replace(",", ".")
        )
        
        # Estimativa de tempo
        time_estimate = {
            10_000: "~1-2s",
            25_000: "~2-3s", 
            50_000: "~3-5s",
            100_000: "~8-10s",
            250_000: "~20-25s",
            500_000: "~40-50s"
        }
        st.caption(f"⏱️ Tempo estimado: {time_estimate[n_simulations]}")
        
        st.markdown("---")
        show_stats = st.checkbox("Mostrar estatísticas detalhadas", value=True)
        show_confidence = st.checkbox("Mostrar nível de confiança", value=True)
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["🎯 Predição", "📊 Estatísticas", "🏆 Rankings"])
    
    with tab1:
        show_prediction_tab(show_stats, show_confidence, n_simulations)
    
    with tab2:
        show_statistics_tab()
    
    with tab3:
        show_rankings_tab()

def show_prediction_tab(show_stats, show_confidence, n_simulations):
    """Tab de predição de partidas."""
    
    # Buscar times
    teams = get_teams()
    
    if not teams:
        st.error("❌ Não foi possível carregar os times. Verifique se a API está rodando.")
        return
    
    team_dict = {t['nome']: t['id'] for t in teams}
    team_names = sorted(team_dict.keys())
    
    # Seleção de times com layout moderno
    col1, col2, col3 = st.columns([1, 0.2, 1])
    
    with col1:
        st.markdown('<div class="team-selector">', unsafe_allow_html=True)
        st.markdown("#### 🏠 Time da Casa")
        home_team = st.selectbox(
            "Selecione o mandante",
            team_names,
            key="home",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br><br><h2 style='text-align: center; color: #00D4FF;'>VS</h2>", unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="team-selector">', unsafe_allow_html=True)
        st.markdown("#### ✈️ Time Visitante")
        away_team = st.selectbox(
            "Selecione o visitante",
            team_names,
            key="away",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botão de predição
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 GERAR PREDIÇÃO", use_container_width=True):
            if home_team == away_team:
                st.warning("⚠️ Selecione times diferentes")
                return
            
            with st.spinner(f"🔮 Simulando {n_simulations:,} partidas...".replace(",", ".")):
                prediction = predict_match(team_dict[home_team], team_dict[away_team], n_simulations)
            
            if prediction:
                display_prediction(prediction, home_team, away_team, show_stats, show_confidence)
            else:
                st.error("❌ Erro ao gerar predição")

def display_prediction(prediction, home_team, away_team, show_stats, show_confidence):
    """Exibe resultados da predição."""
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Extrair dados da estrutura da API
    previsao = prediction.get('previsao', {})
    resultado = previsao.get('resultado', {})
    gols = previsao.get('gols', {})
    
    # Card principal de resultado
    st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
    
    # Probabilidades principais
    st.markdown("### 🎲 Probabilidades do Resultado")
    
    probs = [
        ("vitoria_mandante", home_team, "prob-home", "#00D4FF"),
        ("empate", "Empate", "prob-draw", "#FFD700"),
        ("vitoria_visitante", away_team, "prob-away", "#FF416C")
    ]
    
    for key, label, css_class, color in probs:
        prob = resultado.get(key, 0)
        st.markdown(f"""
        <div class="prob-container">
            <div class="prob-label">
                <span>{label}</span>
                <span style="color: {color}; font-size: 1.2rem;">{format_percentage(prob)}</span>
            </div>
            <div class="prob-bar">
                <div class="prob-fill {css_class}" style="width: {prob}%;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Estatísticas em colunas
    if show_stats:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{gols.get('mandante_media', 0):.1f}</div>
                <div class="stat-label">Gols Casa</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{gols.get('visitante_media', 0):.1f}</div>
                <div class="stat-label">Gols Fora</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{format_percentage(gols.get('over_2.5', 0))}</div>
                <div class="stat-label">Over 2.5</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{format_percentage(gols.get('btts', 0))}</div>
                <div class="stat-label">BTTS</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Placar mais provável
        placares = previsao.get('placares', [])
        if placares:
            st.markdown("<br>", unsafe_allow_html=True)
            placar = placares[0]  # Primeiro placar é o mais provável
            st.markdown(f"""
            <div class="prediction-card" style="text-align: center;">
                <h3 style="color: rgba(255,255,255,0.7); margin-bottom: 1rem;">⚡ Placar Mais Provável</h3>
                <h1 style="color: #00D4FF; font-size: 4rem; margin: 0;">
                    {placar['mandante']} × {placar['visitante']}
                </h1>
                <p style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                    Probabilidade: {format_percentage(placar['probabilidade'])}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Nível de confiança
    if show_confidence:
        st.markdown("<br>", unsafe_allow_html=True)
        confidence = prediction.get('confianca', 0)
        simulacoes = previsao.get('simulacoes', 0)
        
        color = "#00FF88" if confidence > 70 else "#FFD700" if confidence > 40 else "#FF416C"
        
        st.markdown(f"""
        <div class="prediction-card" style="background: rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 style="color: rgba(255,255,255,0.7); margin: 0;">🎯 Nível de Confiança</h4>
                    <p style="color: rgba(255,255,255,0.5); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        Baseado em {simulacoes:,} simulações Monte Carlo
                    </p>
                </div>
                <div style="text-align: right;">
                    <h1 style="color: {color}; font-size: 3rem; margin: 0;">{format_percentage(confidence)}</h1>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_statistics_tab():
    """Tab de estatísticas gerais."""
    
    try:
        # Stats do sistema
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            metrics = [
                ("📊 Total Partidas", stats.get('total_partidas', 0), "#00D4FF"),
                ("🏆 Competições", stats.get('competicoes', 0), "#00FF88"),
                ("⚽ Times Ativos", stats.get('times_ativos', 0), "#FFD700"),
                ("👥 Jogadores", stats.get('total_jogadores', 0), "#FF416C")
            ]
            
            for col, (label, value, color) in zip([col1, col2, col3, col4], metrics):
                with col:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value" style="color: {color};">{value}</div>
                        <div class="stat-label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Distribuição por competição
            if 'por_competicao' in stats:
                st.markdown("### 📈 Distribuição por Competição")
                
                for comp in stats['por_competicao'][:10]:
                    pct = (comp['partidas'] / stats['total_partidas'] * 100) if stats['total_partidas'] > 0 else 0
                    st.markdown(f"""
                    <div class="prob-container">
                        <div class="prob-label">
                            <span>{comp['liga']}</span>
                            <span style="color: #00D4FF;">{comp['partidas']} partidas ({pct:.1f}%)</span>
                        </div>
                        <div class="prob-bar">
                            <div class="prob-fill prob-home" style="width: {pct}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {str(e)}")

def show_rankings_tab():
    """Tab de rankings."""
    
    st.markdown("### 🏆 Rankings dos Times")
    st.info("Em desenvolvimento - Em breve rankings completos!")

if __name__ == "__main__":
    main()
