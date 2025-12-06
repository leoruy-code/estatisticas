import streamlit as st
import json
import os
import base64
from io import BytesIO

st.set_page_config(page_title="RAG Estatísticas ⚽", layout="wide", page_icon="⚽")

# ==================== SIDEBAR MENU ====================
st.sidebar.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    .sidebar-title {
        color: #00d4ff;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #00d4ff;
        margin-bottom: 1rem;
    }
    .menu-section {
        color: #888;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
    }
</style>
<div class="sidebar-title">⚽ RAG Estatísticas</div>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="menu-section">📂 Navegação</div>', unsafe_allow_html=True)

pagina = st.sidebar.radio(
    "Menu",
    [
        "🏠 Início",
        "📊 Ver Times e Estatísticas",
        "🎯 Análise de Partida (Poisson)",
        "🏆 Ranking de Times",
        "➕ Adicionar Jogador",
        "⚽ Adicionar Time",
        "👥 Gerenciar Time",
    ],
    label_visibility="collapsed"
)

data_dir = os.path.join(os.path.dirname(__file__), '../../data')
times_path = os.path.join(data_dir, 'times.json')
jogadores_path = os.path.join(data_dir, 'jogadores.json')
images_dir = os.path.join(data_dir, 'images')

# Garantir que o diretório de imagens existe
os.makedirs(images_dir, exist_ok=True)

def carregar_json(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_json(obj, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def salvar_imagem_time(uploaded_file, nome_time):
    """Salva a imagem do time e retorna o caminho do arquivo"""
    if uploaded_file is not None:
        # Criar nome de arquivo seguro
        nome_arquivo = f"{nome_time.lower().replace(' ', '_')}.png"
        caminho_imagem = os.path.join(images_dir, nome_arquivo)
        
        # Salvar a imagem
        with open(caminho_imagem, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return nome_arquivo
    return None

def carregar_imagem_time(imagem_info):
    """Carrega a imagem do time - pode ser arquivo local ou URL"""
    if imagem_info:
        # Se for uma URL (começa com http)
        if isinstance(imagem_info, str) and imagem_info.startswith('http'):
            return imagem_info
        # Se for um arquivo local
        elif isinstance(imagem_info, str):
            caminho_imagem = os.path.join(images_dir, imagem_info)
            if os.path.exists(caminho_imagem):
                return caminho_imagem
    return None

if pagina == "🏠 Início":
    st.title("⚽ Sistema de Estatísticas de Futebol")
    st.write("### Bem-vindo ao sistema de análise de estatísticas para apostas!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**📊 Funcionalidades**")
        st.write("- Cadastro de jogadores com estatísticas detalhadas")
        st.write("- Criação e gerenciamento de times")
        st.write("- Análise estatística de times")
        st.write("- Comparação entre equipes")
    
    with col2:
        jogadores = carregar_json(jogadores_path)
        times = carregar_json(times_path)
        
        st.success("**📈 Status do Sistema**")
        st.metric("Jogadores Cadastrados", len(jogadores))
        st.metric("Times Cadastrados", len(times))
    
    st.write("---")
    st.write("Use o menu lateral para navegar pelas funcionalidades.")

elif pagina == "➕ Adicionar Jogador":
    st.title("➕ Cadastro de Jogador")
    
    with st.form("form_jogador"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome do jogador *", placeholder="Ex: Neymar Jr")
            time = st.text_input("Time *", placeholder="Ex: Al-Hilal")
            gols = st.number_input("Gols", min_value=0, value=0)
            assistencias = st.number_input("Assistências", min_value=0, value=0)
            cartoes_amarelos = st.number_input("Cartões amarelos", min_value=0, value=0)
            cartoes_vermelhos = st.number_input("Cartões vermelhos", min_value=0, value=0)
        
        with col2:
            faltas_cometidas = st.number_input("Faltas cometidas", min_value=0, value=0)
            faltas_sofridas = st.number_input("Faltas sofridas", min_value=0, value=0)
            chutes = st.number_input("Chutes", min_value=0, value=0)
            chutes_no_gol = st.number_input("Chutes no gol", min_value=0, value=0)
            desarmes = st.number_input("Desarmes", min_value=0, value=0)
        
        submitted = st.form_submit_button("💾 Salvar Jogador", use_container_width=True)
        
        if submitted:
            if not nome or not time:
                st.error("❌ Nome e Time são obrigatórios!")
            else:
                jogadores = carregar_json(jogadores_path)
                
                # Verificar se jogador já existe
                if any(j['nome'].lower() == nome.lower() and j['time'].lower() == time.lower() for j in jogadores):
                    st.warning(f"⚠️ Jogador {nome} do time {time} já existe!")
                else:
                    novo_jogador = {
                        "nome": nome,
                        "time": time,
                        "gols": gols,
                        "assistencias": assistencias,
                        "cartoes_amarelos": cartoes_amarelos,
                        "cartoes_vermelhos": cartoes_vermelhos,
                        "faltas_cometidas": faltas_cometidas,
                        "faltas_sofridas": faltas_sofridas,
                        "chutes": chutes,
                        "chutes_no_gol": chutes_no_gol,
                        "desarmes": desarmes
                    }
                    jogadores.append(novo_jogador)
                    salvar_json(jogadores, jogadores_path)
                    st.success(f"✅ Jogador **{nome}** salvo com sucesso!")
                    st.balloons()

elif pagina == "⚽ Adicionar Time":
    st.title("⚽ Cadastro de Time")
    
    with st.form("form_time"):
        nome_time = st.text_input("Nome do time *", placeholder="Ex: Flamengo")
        
        st.write("**Imagem/Logo do Time:**")
        opcao_imagem = st.radio(
            "Como deseja adicionar a imagem?",
            ["📷 Upload de arquivo", "🔗 URL da imagem"],
            horizontal=True
        )
        
        foto_time = None
        url_imagem = None
        
        if opcao_imagem == "📷 Upload de arquivo":
            foto_time = st.file_uploader("Envie a imagem", type=["png", "jpg", "jpeg"], help="Envie uma imagem do escudo ou logo do time")
        else:
            url_imagem = st.text_input("Cole o link da imagem", placeholder="https://exemplo.com/logo.png")
        
        submitted = st.form_submit_button("💾 Criar Time", use_container_width=True)
        
        if submitted:
            if not nome_time:
                st.error("❌ Nome do time é obrigatório!")
            else:
                times = carregar_json(times_path)
                
                # Verificar se time já existe
                if any(t['nome'].lower() == nome_time.lower() for t in times):
                    st.warning(f"⚠️ Time {nome_time} já existe!")
                else:
                    # Determinar qual imagem usar
                    imagem_info = None
                    if url_imagem and url_imagem.strip():
                        imagem_info = url_imagem.strip()
                    elif foto_time:
                        imagem_info = salvar_imagem_time(foto_time, nome_time)
                    
                    novo_time = {
                        "nome": nome_time,
                        "imagem": imagem_info,
                        "jogadores": []
                    }
                    times.append(novo_time)
                    salvar_json(times, times_path)
                    st.success(f"✅ Time **{nome_time}** criado com sucesso!")
                    if imagem_info:
                        st.success("📷 Imagem do time salva!")
                    st.info("💡 Agora você pode adicionar jogadores ao time na página 'Gerenciar Time'")

elif pagina == "👥 Gerenciar Time":
    st.title("👥 Gerenciar Time - Adicionar Jogadores")
    
    times = carregar_json(times_path)
    jogadores = carregar_json(jogadores_path)
    
    if not times:
        st.warning("⚠️ Nenhum time cadastrado! Crie um time primeiro.")
    elif not jogadores:
        st.warning("⚠️ Nenhum jogador cadastrado! Adicione jogadores primeiro.")
    else:
        nomes_times = [t["nome"] for t in times]
        time_selecionado = st.selectbox("Selecione o time para gerenciar", nomes_times)
        time_idx = nomes_times.index(time_selecionado)
        time_atual = times[time_idx]
        
        # Mostrar imagem do time se existir
        col_img, col_info = st.columns([1, 3])
        
        with col_img:
            imagem_path = carregar_imagem_time(time_atual.get('imagem'))
            if imagem_path:
                st.image(imagem_path, width=150, caption=time_selecionado)
            else:
                st.write("")
        
        with col_info:
            st.write(f"### Time: {time_selecionado}")
        
        st.write("---")
        
        # Seção para editar/adicionar imagem do time
        with st.expander("📷 Editar Imagem do Time"):
            st.write("**Imagem atual:**")
            imagem_atual = carregar_imagem_time(time_atual.get('imagem'))
            if imagem_atual:
                st.image(imagem_atual, width=200)
                st.caption("Faça upload de uma nova imagem ou cole um link para substituir")
            else:
                st.info("Nenhuma imagem cadastrada para este time")
            
            opcao_edicao = st.radio(
                "Como deseja atualizar a imagem?",
                ["📷 Upload de arquivo", "🔗 URL da imagem"],
                horizontal=True,
                key=f"opcao_edicao_{time_selecionado}"
            )
            
            nova_imagem = None
            nova_url = None
            
            if opcao_edicao == "📷 Upload de arquivo":
                nova_imagem = st.file_uploader(
                    "Nova imagem do time", 
                    type=["png", "jpg", "jpeg"],
                    key=f"upload_img_{time_selecionado}",
                    help="Envie uma nova imagem para substituir a atual"
                )
            else:
                nova_url = st.text_input(
                    "Cole o link da imagem",
                    placeholder="https://exemplo.com/logo.png",
                    key=f"url_img_{time_selecionado}"
                )
            
            if st.button("💾 Atualizar Imagem", key=f"btn_img_{time_selecionado}"):
                imagem_info = None
                
                if nova_url and nova_url.strip():
                    imagem_info = nova_url.strip()
                elif nova_imagem:
                    imagem_info = salvar_imagem_time(nova_imagem, time_selecionado)
                
                if imagem_info:
                    times[time_idx]["imagem"] = imagem_info
                    salvar_json(times, times_path)
                    st.success("✅ Imagem do time atualizada com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Selecione uma imagem ou cole um link primeiro!")
        
        st.write("---")
        
        # Mostrar jogadores atuais do time
        st.write("### 👥 Gerenciar Jogadores")
        jogadores_atuais = time_atual.get("jogadores", [])
        # Buscar jogadores completos do time
        jogadores_do_time = [j for j in jogadores if j.get('time') == time_selecionado]
        if jogadores_do_time:
            st.write(f"**Jogadores atuais ({len(jogadores_do_time)}):**")
            for jog in jogadores_do_time:
                st.write(f"- {jog['nome']} (Gols: {jog.get('gols', 0)}, Assistências: {jog.get('assistencias', 0)})")
        else:
            st.info("Nenhum jogador no time ainda.")
        
        st.write("")
        
        # Selecionar jogadores disponíveis
        nomes_jogadores = [f"{j['nome']} ({j['time']})" for j in jogadores]
        jogadores_selecionados = st.multiselect(
            "Selecione os jogadores para adicionar ao time", 
            nomes_jogadores,
            help="Você pode selecionar múltiplos jogadores"
        )
        
        if st.button("💾 Atualizar Jogadores do Time", use_container_width=True):
            # Extrair apenas os nomes dos jogadores selecionados
            nomes_selecionados = [nome.split(" (")[0] for nome in jogadores_selecionados]
            
            # Filtrar jogadores completos
            times[time_idx]["jogadores"] = [j for j in jogadores if j["nome"] in nomes_selecionados]
            salvar_json(times, times_path)
            st.success(f"✅ Time **{time_selecionado}** atualizado com {len(times[time_idx]['jogadores'])} jogadores!")
            st.rerun()

elif pagina == "📊 Ver Times e Estatísticas":
    st.title("📊 Times e Estatísticas")
    
    times = carregar_json(times_path)
    todos_jogadores = carregar_json(jogadores_path)
    
    if not times:
        st.warning("⚠️ Nenhum time cadastrado!")
    else:
        # Seleção de times
        nomes_times = [t["nome"] for t in times]
        time_selecionado = st.selectbox("Selecione um time", nomes_times)
        time = next(t for t in times if t["nome"] == time_selecionado)
        
        st.write("---")
        
        # Buscar jogadores completos de jogadores.json filtrando pelo time
        jogadores_nomes = time.get("jogadores", [])
        jogadores = [j for j in todos_jogadores if j.get('time') == time['nome']]
        
        if not jogadores:
            st.info(f"O time **{time['nome']}** ainda não possui jogadores cadastrados.")
        else:
            # Cabeçalho com imagem e nome do time
            col_img, col_nome = st.columns([1, 4])
            
            with col_img:
                imagem_path = carregar_imagem_time(time.get('imagem'))
                if imagem_path:
                    st.image(imagem_path, width=120)
            
            with col_nome:
                st.subheader(f"⚽ {time['nome']}")
                st.write(f"**Total de jogadores:** {len(jogadores)}")
            
            # Estatísticas do time
            st.write("### 📈 Estatísticas do Time")
            
            # Calcular totais
            n_jogadores = len(jogadores) if jogadores else 1
            total_gols = sum(j.get('gols', 0) for j in jogadores)
            total_assist = sum(j.get('assistencias', 0) for j in jogadores)
            total_chutes = sum(j.get('chutes', 0) for j in jogadores)
            total_chutes_gol = sum(j.get('chutes_no_gol', 0) for j in jogadores)
            total_faltas = sum(j.get('faltas_cometidas', 0) for j in jogadores)
            total_escanteios = sum(j.get('escanteios', 0) for j in jogadores)  # se disponível
            
            # Médias
            media_gols = total_gols / n_jogadores
            media_assist = total_assist / n_jogadores
            media_chutes = total_chutes / n_jogadores
            media_chutes_gol = total_chutes_gol / n_jogadores
            media_faltas = total_faltas / n_jogadores
            media_escanteios = total_escanteios / n_jogadores
            precisao_chutes = (total_chutes_gol / total_chutes * 100) if total_chutes > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("⚽ Total Gols", total_gols)
                st.metric("Média Gols", f"{media_gols:.2f}")
            
            with col2:
                st.metric("🎯 Total Assistências", total_assist)
                st.metric("Média Assistências", f"{media_assist:.2f}")
            
            with col3:
                st.metric("👟 Total Chutes", total_chutes)
                st.metric("Média Chutes", f"{media_chutes:.2f}")
                st.metric("🎯 Chutes ao Gol", total_chutes_gol)
                st.metric("Média Chutes ao Gol", f"{media_chutes_gol:.2f}")
                st.metric("Precisão", f"{precisao_chutes:.1f}%")
            
            with col4:
                st.metric("🚩 Escanteios", total_escanteios)
                st.metric("Média Escanteios", f"{media_escanteios:.2f}")
                st.metric("⚠️ Faltas Cometidas", total_faltas)
                st.metric("Média Faltas", f"{media_faltas:.2f}")
            
            with col5:
                total_amarelos = sum(j.get('cartoes_amarelos', 0) for j in jogadores)
                total_vermelhos = sum(j.get('cartoes_vermelhos', 0) for j in jogadores)
                st.metric("🟨 Cartões Amarelos", total_amarelos)
                st.metric("🟥 Cartões Vermelhos", total_vermelhos)
            
            # Lista de jogadores
            st.write("### 👥 Lista de Jogadores")
            
            jogador_selecionado_nome = st.selectbox(
                "Selecione um jogador para ver detalhes",
                [j["nome"] for j in jogadores]
            )
            
            jogador = next(j for j in jogadores if j["nome"] == jogador_selecionado_nome)
            
            # Layout com foto e estatísticas
            col_foto, col_stats = st.columns([1, 3])
            
            with col_foto:
                foto_url = jogador.get('foto_url')
                if foto_url:
                    try:
                        st.image(foto_url, width=150, caption=jogador['nome'])
                    except:
                        st.write("📷 Foto não disponível")
                else:
                    st.write("📷 Sem foto")
            
            with col_stats:
                st.write(f"#### Estatísticas de {jogador['nome']}")
                
                # Rating se disponível
                rating = jogador.get('rating', 0)
                if rating > 0:
                    st.metric("⭐ Rating", f"{rating:.2f}")
                
                # Tabs para organizar estatísticas
                tab1, tab2, tab3, tab4 = st.tabs(["⚽ Ataque", "🎯 Passes", "🛡️ Defesa", "📊 Geral"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Gols", jogador.get('gols', 0))
                        st.metric("xG (Esperados)", f"{jogador.get('gols_esperados', 0):.2f}")
                        st.metric("Chutes", jogador.get('chutes', 0))
                        st.metric("Grandes Chances Criadas", jogador.get('grandes_chances_criadas', 0))
                    with col2:
                        st.metric("Chutes no Gol", jogador.get('chutes_no_gol', 0))
                        conversao = jogador.get('conversao_gols', 0)
                        st.metric("Conversão", f"{conversao:.1f}%")
                        st.metric("Grandes Chances Perdidas", jogador.get('grandes_chances_perdidas', 0))
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Assistências", jogador.get('assistencias', 0))
                        st.metric("xA (Esperadas)", f"{jogador.get('assistencias_esperadas', 0):.2f}")
                        st.metric("Total de Passes", jogador.get('total_passes', 0))
                        st.metric("Passes Decisivos", jogador.get('passes_decisivos', 0))
                    with col2:
                        passes_certos = jogador.get('passes_certos', 0)
                        total_passes = jogador.get('total_passes', 1)
                        precisao_passes = (passes_certos / total_passes * 100) if total_passes > 0 else 0
                        st.metric("Precisão de Passes", f"{precisao_passes:.1f}%")
                        st.metric("Passes Longos Certos", f"{jogador.get('passes_longos_certos', 0):.0f}")
                        st.metric("Cruzamentos Certos", f"{jogador.get('cruzamentos_certos', 0):.0f}")
                
                with tab3:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Desarmes", jogador.get('desarmes', 0))
                        st.metric("Interceptações", f"{jogador.get('interceptacoes', 0):.1f}")
                        st.metric("Duelos Ganhos", jogador.get('duelos_ganhos', 0))
                        st.metric("Duelos Aéreos", jogador.get('duelos_aereos_ganhos', 0))
                    with col2:
                        duelos_total = jogador.get('duelos_totais', 1)
                        duelos_ganhos = jogador.get('duelos_ganhos', 0)
                        taxa_duelos = (duelos_ganhos / duelos_total * 100) if duelos_total > 0 else 0
                        st.metric("Taxa de Duelos", f"{taxa_duelos:.1f}%")
                        st.metric("Dribles Certos", f"{jogador.get('dribles_certos', 0):.0f}")
                        st.metric("Defesas (GK)", jogador.get('defesas', 0))
                
                with tab4:
                    col1, col2 = st.columns(2)
                    partidas = jogador.get('partidas', 0)
                    faltas_cometidas = jogador.get('faltas_cometidas', 0)
                    media_faltas_jogador = faltas_cometidas / partidas if partidas > 0 else 0
                    with col1:
                        st.metric("Partidas", partidas)
                        st.metric("Minutos Jogados", jogador.get('minutos_jogados', 0))
                        st.metric("Cartões Amarelos", jogador.get('cartoes_amarelos', 0))
                        st.metric("Cartões Vermelhos", jogador.get('cartoes_vermelhos', 0))
                    with col2:
                        st.metric("Faltas Cometidas", faltas_cometidas)
                        st.metric("Média Faltas/Partida", f"{media_faltas_jogador:.2f}")
                        st.metric("Faltas Sofridas", jogador.get('faltas_sofridas', 0))
                        st.metric("Impedimentos", jogador.get('impedimentos', 0))
                        st.metric("Pênaltis Marcados", jogador.get('penaltis_marcados', 0))

elif pagina == "🎯 Análise de Partida (Poisson)":
    st.title("🎯 Análise de Partida - Modelo Poisson")
    st.write("Simule partidas e obtenha probabilidades baseadas em estatísticas reais.")
    
    # Importar o analisador
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from poisson_analyzer import PoissonAnalyzer, prob_to_odds, calcular_1x2, calcular_resultado_exato
    
    @st.cache_resource
    def get_analyzer():
        return PoissonAnalyzer(
            jogadores_path=os.path.join(os.path.dirname(__file__), '../../data/jogadores.json'),
            times_path=os.path.join(os.path.dirname(__file__), '../../data/times.json')
        )
    
    analyzer = get_analyzer()
    
    # Seleção de times
    nomes_times = sorted(analyzer.times_stats.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 Time da Casa", nomes_times, index=nomes_times.index("Flamengo") if "Flamengo" in nomes_times else 0)
    with col2:
        away_team = st.selectbox("✈️ Time Visitante", nomes_times, index=nomes_times.index("Palmeiras") if "Palmeiras" in nomes_times else 1)
    
    # Exibir dados de forma dos times selecionados
    st.write("---")
    st.write("### 📈 Forma Recente dos Times")
    
    col1, col2 = st.columns(2)
    
    with col1:
        home_stats = analyzer.get_team_stats(home_team)
        home_forma = analyzer.get_forma_multiplicador(home_team)
        home_metricas = analyzer.get_metricas_recentes(home_team, 5)
        
        st.write(f"**🏠 {home_team}**")
        if home_metricas:
            v, e, d = home_metricas.get('vitorias', 0), home_metricas.get('empates', 0), home_metricas.get('derrotas', 0)
            st.write(f"📊 Últimas 5: **{v}V {e}E {d}D**")
            st.write(f"⚽ Gols Marcados: **{home_metricas.get('gols_marcados_media', 0):.1f}/jogo**")
            st.write(f"🥅 Gols Sofridos: **{home_metricas.get('gols_sofridos_media', 0):.1f}/jogo**")
        
        if home_forma > 1.05:
            st.success(f"📈 Forma: **{home_forma:.2f}** (Boa fase)")
        elif home_forma < 0.95:
            st.error(f"📉 Forma: **{home_forma:.2f}** (Má fase)")
        else:
            st.info(f"➡️ Forma: **{home_forma:.2f}** (Estável)")
        
        if home_stats:
            st.write(f"⚔️ Attack: **{home_stats.attack_strength:.2f}** | 🛡️ Defense: **{home_stats.defense_weakness:.2f}**")
    
    with col2:
        away_stats = analyzer.get_team_stats(away_team)
        away_forma = analyzer.get_forma_multiplicador(away_team)
        away_metricas = analyzer.get_metricas_recentes(away_team, 5)
        
        st.write(f"**✈️ {away_team}**")
        if away_metricas:
            v, e, d = away_metricas.get('vitorias', 0), away_metricas.get('empates', 0), away_metricas.get('derrotas', 0)
            st.write(f"📊 Últimas 5: **{v}V {e}E {d}D**")
            st.write(f"⚽ Gols Marcados: **{away_metricas.get('gols_marcados_media', 0):.1f}/jogo**")
            st.write(f"🥅 Gols Sofridos: **{away_metricas.get('gols_sofridos_media', 0):.1f}/jogo**")
        
        if away_forma > 1.05:
            st.success(f"📈 Forma: **{away_forma:.2f}** (Boa fase)")
        elif away_forma < 0.95:
            st.error(f"📉 Forma: **{away_forma:.2f}** (Má fase)")
        else:
            st.info(f"➡️ Forma: **{away_forma:.2f}** (Estável)")
        
        if away_stats:
            st.write(f"⚔️ Attack: **{away_stats.attack_strength:.2f}** | 🛡️ Defense: **{away_stats.defense_weakness:.2f}**")
    
    # Multiplicadores opcionais
    with st.expander("⚙️ Ajustes Manuais (opcional)"):
        col1, col2, col3 = st.columns(3)
        with col1:
            home_advantage = st.slider("Vantagem Casa", 1.0, 1.2, 1.08, 0.01)
        with col2:
            usar_forma = st.checkbox("Usar Forma Automática", value=True)
        with col3:
            if not usar_forma:
                form_manual = st.slider("Ajuste Manual", 0.8, 1.2, 1.0, 0.05)
    
    if st.button("🔮 Analisar Partida", use_container_width=True, type="primary"):
        pred = analyzer.prever_partida(home_team, away_team, home_advantage, usar_forma=usar_forma)
        
        if pred:
            st.write("---")
            st.subheader(f"⚽ {home_team} vs {away_team}")
            
            # Lambdas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"λ Gols {home_team}", f"{pred.lambda_home_goals:.2f}")
            with col2:
                st.metric(f"λ Gols {away_team}", f"{pred.lambda_away_goals:.2f}")
            with col3:
                st.metric("λ Total Gols", f"{pred.lambda_total_goals:.2f}")
            
            st.write("---")
            
            # Over/Under Gols
            st.write("### 🎯 Probabilidades Over/Under Gols")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                prob = pred.prob_over_05_goals
                st.metric("Over 0.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col2:
                prob = pred.prob_over_15_goals
                st.metric("Over 1.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col3:
                prob = pred.prob_over_25_goals
                st.metric("Over 2.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col4:
                prob = pred.prob_over_35_goals
                st.metric("Over 3.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            
            # Escanteios
            st.write("### 🚩 Probabilidades Escanteios")
            st.write(f"**λ {home_team}:** {pred.lambda_home_corners:.1f} | **λ {away_team}:** {pred.lambda_away_corners:.1f} | **Total:** {pred.lambda_total_corners:.1f}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                prob = pred.prob_over_85_corners
                st.metric("Over 8.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col2:
                prob = pred.prob_over_95_corners
                st.metric("Over 9.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col3:
                prob = pred.prob_over_105_corners
                st.metric("Over 10.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            with col4:
                prob = pred.prob_over_115_corners
                st.metric("Over 11.5", f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.2f}")
            
            # BTTS e 1X2
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### ⚽ Both Teams To Score")
                st.metric("BTTS - Sim", f"{pred.prob_btts*100:.1f}%", f"odd {prob_to_odds(pred.prob_btts):.2f}")
                st.metric("BTTS - Não", f"{(1-pred.prob_btts)*100:.1f}%", f"odd {prob_to_odds(1-pred.prob_btts):.2f}")
            
            with col2:
                st.write("### 🏆 Resultado (1X2)")
                probs_1x2 = calcular_1x2(pred.lambda_home_goals, pred.lambda_away_goals)
                st.metric(f"Vitória {home_team}", f"{probs_1x2['home']*100:.1f}%", f"odd {prob_to_odds(probs_1x2['home']):.2f}")
                st.metric("Empate", f"{probs_1x2['draw']*100:.1f}%", f"odd {prob_to_odds(probs_1x2['draw']):.2f}")
                st.metric(f"Vitória {away_team}", f"{probs_1x2['away']*100:.1f}%", f"odd {prob_to_odds(probs_1x2['away']):.2f}")
            
            # Placares
            st.write("### 📋 Top 10 Placares Mais Prováveis")
            placares = calcular_resultado_exato(pred.lambda_home_goals, pred.lambda_away_goals)
            top_placares = sorted(placares.items(), key=lambda x: x[1], reverse=True)[:10]
            
            cols = st.columns(5)
            for i, (placar, prob) in enumerate(top_placares):
                with cols[i % 5]:
                    st.metric(placar, f"{prob*100:.1f}%", f"odd {prob_to_odds(prob):.1f}")
        else:
            st.error("Times não encontrados!")

elif pagina == "🏆 Ranking de Times":
    st.title("🏆 Ranking de Times")
    
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from poisson_analyzer import PoissonAnalyzer
    
    @st.cache_resource
    def get_analyzer():
        return PoissonAnalyzer(
            jogadores_path=os.path.join(os.path.dirname(__file__), '../../data/jogadores.json'),
            times_path=os.path.join(os.path.dirname(__file__), '../../data/times.json')
        )
    
    analyzer = get_analyzer()
    
    # Médias da Liga
    st.write("### 📊 Médias da Liga (Brasileirão 2025)")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("⚽ Gols/Jogo", f"{analyzer.league_averages['avg_goals_per_match']:.2f}")
    with col2:
        st.metric("🥅 Gols Sofridos", f"{analyzer.league_averages.get('avg_goals_conceded', 0):.2f}")
    with col3:
        st.metric("👟 Chutes/Jogo", f"{analyzer.league_averages['avg_shots_per_match']:.2f}")
    with col4:
        st.metric("⚠️ Faltas/Jogo", f"{analyzer.league_averages['avg_fouls_per_match']:.2f}")
    with col5:
        st.metric("🚩 Escanteios/Jogo", f"{analyzer.league_averages['avg_corners_per_match']:.2f}")
    
    st.write("---")
    
    # Tabs para diferentes rankings
    tab1, tab2, tab3, tab4 = st.tabs(["⚔️ Ataque", "🛡️ Defesa", "📈 Forma", "🚩 Escanteios"])
    
    with tab1:
        st.write("### 🔥 Ranking por Attack Strength")
        st.write("*Attack Strength > 1.0 = ataque acima da média*")
        
        ranking = analyzer.ranking_times()
        
        for i, (nome, strength, gols) in enumerate(ranking, 1):
            if strength >= 1.2:
                emoji = "🔥"
            elif strength >= 1.0:
                emoji = "✅"
            elif strength >= 0.8:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
            with col1:
                st.write(f"**{i}.**")
            with col2:
                st.write(f"{emoji} **{nome}**")
            with col3:
                st.write(f"Attack: **{strength:.2f}**")
            with col4:
                st.write(f"⚽ {gols:.2f}/jogo")
    
    with tab2:
        st.write("### 🛡️ Ranking por Defense Weakness")
        st.write("*Defense < 1.0 = defesa sólida (sofre menos gols) | > 1.0 = defesa fraca*")
        
        # Ordenar por defense_weakness (menor é melhor)
        defense_ranking = []
        for nome, ts in analyzer.times_stats.items():
            metricas = analyzer.times_metricas.get(nome, {})
            gols_sofridos = metricas.get('gols_sofridos_media', 0)
            defense_ranking.append((nome, ts.defense_weakness, gols_sofridos))
        
        defense_ranking.sort(key=lambda x: x[1])  # Menor defense_weakness = melhor defesa
        
        for i, (nome, weakness, gols_sofridos) in enumerate(defense_ranking, 1):
            if weakness <= 0.8:
                emoji = "🏆"  # Defesa excelente
            elif weakness <= 1.0:
                emoji = "✅"  # Defesa boa
            elif weakness <= 1.2:
                emoji = "⚠️"  # Defesa média
            else:
                emoji = "❌"  # Defesa ruim
            
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
            with col1:
                st.write(f"**{i}.**")
            with col2:
                st.write(f"{emoji} **{nome}**")
            with col3:
                st.write(f"Defense: **{weakness:.2f}**")
            with col4:
                st.write(f"🥅 {gols_sofridos:.2f}/jogo")
    
    with tab3:
        st.write("### 📈 Ranking por Forma Recente")
        st.write("*Baseado nas últimas 5 partidas | > 1.0 = boa fase | < 1.0 = má fase*")
        
        forma_ranking = []
        for nome in analyzer.times_stats.keys():
            forma = analyzer.get_forma_multiplicador(nome)
            metricas = analyzer.get_metricas_recentes(nome, 5)
            v = metricas.get('vitorias', 0)
            e = metricas.get('empates', 0)
            d = metricas.get('derrotas', 0)
            forma_ranking.append((nome, forma, v, e, d))
        
        forma_ranking.sort(key=lambda x: x[1], reverse=True)  # Maior forma = melhor
        
        for i, (nome, forma, v, e, d) in enumerate(forma_ranking, 1):
            if forma >= 1.1:
                emoji = "🚀"  # Excelente forma
            elif forma >= 1.0:
                emoji = "📈"  # Boa forma
            elif forma >= 0.9:
                emoji = "➡️"  # Estável
            else:
                emoji = "📉"  # Má forma
            
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
            with col1:
                st.write(f"**{i}.**")
            with col2:
                st.write(f"{emoji} **{nome}**")
            with col3:
                st.write(f"Forma: **{forma:.2f}**")
            with col4:
                st.write(f"📊 {v}V {e}E {d}D")
    
    with tab4:
        st.write("### 🚩 Ranking por Escanteios")
        st.write("*Média de escanteios por partida | Casa vs Fora*")
        
        escanteios_ranking = analyzer.ranking_escanteios()
        
        for i, (nome, media, casa, fora) in enumerate(escanteios_ranking, 1):
            if media >= 6.0:
                emoji = "🔥"  # Muitos escanteios
            elif media >= 5.0:
                emoji = "✅"  # Bom
            elif media >= 4.0:
                emoji = "➡️"  # Médio
            else:
                emoji = "⬇️"  # Poucos
            
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1.5])
            with col1:
                st.write(f"**{i}.**")
            with col2:
                st.write(f"{emoji} **{nome}**")
            with col3:
                st.write(f"**{media:.1f}**/jogo")
            with col4:
                st.write(f"🏠 {casa:.1f} | ✈️ {fora:.1f}")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div style="text-align:center;color:#666;font-size:0.8rem;">'
    'RAG Estatísticas v2.1<br/>Brasileirão 2025'
    '</div>',
    unsafe_allow_html=True
)

