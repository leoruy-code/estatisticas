-- ============================================================
-- RAG Estatísticas - Schema do Banco de Dados
-- Baseado no plano: novopensamento.md
-- ============================================================

-- ==================== TIMES ====================

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    liga VARCHAR(50) DEFAULT 'Brasileirão',
    sofascore_id INTEGER,
    logo_url TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Gols
    jogos_total INTEGER DEFAULT 0,
    gols_marcados_total INTEGER DEFAULT 0,
    gols_marcados_media DECIMAL(5,2) DEFAULT 0,
    gols_sofridos_total INTEGER DEFAULT 0,
    gols_sofridos_media DECIMAL(5,2) DEFAULT 0,
    
    -- Escanteios
    escanteios_for_total INTEGER DEFAULT 0,
    escanteios_for_media DECIMAL(5,2) DEFAULT 0,
    escanteios_against_total INTEGER DEFAULT 0,
    escanteios_against_media DECIMAL(5,2) DEFAULT 0,
    
    -- Chutes
    chutes_for_total INTEGER DEFAULT 0,
    chutes_for_media DECIMAL(5,2) DEFAULT 0,
    chutes_against_total INTEGER DEFAULT 0,
    chutes_against_media DECIMAL(5,2) DEFAULT 0,
    
    -- Cartões
    cartoes_for_total INTEGER DEFAULT 0,
    cartoes_for_media DECIMAL(5,2) DEFAULT 0,
    cartoes_against_total INTEGER DEFAULT 0,
    cartoes_against_media DECIMAL(5,2) DEFAULT 0,
    
    -- Faltas
    faltas_for_total INTEGER DEFAULT 0,
    faltas_for_media DECIMAL(5,2) DEFAULT 0,
    faltas_against_total INTEGER DEFAULT 0,
    faltas_against_media DECIMAL(5,2) DEFAULT 0,
    
    -- Força Calculada
    attack_strength DECIMAL(5,3) DEFAULT 1.0,
    defense_weakness DECIMAL(5,3) DEFAULT 1.0,
    forma_multiplicador DECIMAL(5,3) DEFAULT 1.0,
    
    periodo VARCHAR(20) DEFAULT '2025',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(team_id, periodo)
);

-- ==================== PARTIDAS ====================

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    data TIMESTAMP NOT NULL,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    
    -- Resultado
    home_goals INTEGER,
    away_goals INTEGER,
    
    -- Estatísticas
    home_corners INTEGER DEFAULT 0,
    away_corners INTEGER DEFAULT 0,
    home_shots INTEGER DEFAULT 0,
    away_shots INTEGER DEFAULT 0,
    home_shots_on_target INTEGER DEFAULT 0,
    away_shots_on_target INTEGER DEFAULT 0,
    home_fouls INTEGER DEFAULT 0,
    away_fouls INTEGER DEFAULT 0,
    home_yellow_cards INTEGER DEFAULT 0,
    away_yellow_cards INTEGER DEFAULT 0,
    home_red_cards INTEGER DEFAULT 0,
    away_red_cards INTEGER DEFAULT 0,
    
    -- Metadados
    status VARCHAR(20) DEFAULT 'finished',
    liga VARCHAR(50) DEFAULT 'Brasileirão',
    rodada INTEGER,
    sofascore_event_id INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sofascore_event_id)
);

-- Índices para consultas frequentes
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(data);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);

-- ==================== JOGADORES ====================

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    time_atual_id INTEGER REFERENCES teams(id),
    posicao VARCHAR(30),
    numero_camisa INTEGER,
    nacionalidade VARCHAR(50),
    nascimento DATE,
    altura DECIMAL(3,2),
    pe_preferido VARCHAR(20),
    foto_url TEXT,
    sofascore_id INTEGER,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_players_team ON players(time_atual_id);

CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    
    -- Tempo de Jogo
    jogos_total INTEGER DEFAULT 0,
    minutos_total INTEGER DEFAULT 0,
    minutos_por_jogo DECIMAL(5,2) DEFAULT 0,
    titularidades INTEGER DEFAULT 0,
    
    -- Gols e Finalizações
    gols_total INTEGER DEFAULT 0,
    gols_por_90 DECIMAL(5,3) DEFAULT 0,
    gols_esperados_xg DECIMAL(6,3) DEFAULT 0,
    xg_por_90 DECIMAL(5,3) DEFAULT 0,
    finalizacoes_total INTEGER DEFAULT 0,
    finalizacoes_por_90 DECIMAL(5,2) DEFAULT 0,
    finalizacoes_no_gol INTEGER DEFAULT 0,
    conversao_gols DECIMAL(5,2) DEFAULT 0,
    grandes_chances_criadas INTEGER DEFAULT 0,
    grandes_chances_perdidas INTEGER DEFAULT 0,
    
    -- Assistências e Passes
    assistencias_total INTEGER DEFAULT 0,
    assistencias_esperadas_xa DECIMAL(6,3) DEFAULT 0,
    passes_total INTEGER DEFAULT 0,
    passes_certos INTEGER DEFAULT 0,
    passes_decisivos INTEGER DEFAULT 0,
    passes_chave_por_90 DECIMAL(5,2) DEFAULT 0,
    passes_longos_certos INTEGER DEFAULT 0,
    cruzamentos_total INTEGER DEFAULT 0,
    cruzamentos_certos INTEGER DEFAULT 0,
    cruzamentos_por_90 DECIMAL(5,2) DEFAULT 0,
    
    -- Escanteios (cobrados)
    escanteios_cobrados INTEGER DEFAULT 0,
    escanteios_cobrados_por_90 DECIMAL(5,2) DEFAULT 0,
    
    -- Defesa
    desarmes_total INTEGER DEFAULT 0,
    interceptacoes_total INTEGER DEFAULT 0,
    duelos_ganhos INTEGER DEFAULT 0,
    duelos_totais INTEGER DEFAULT 0,
    duelos_aereos_ganhos INTEGER DEFAULT 0,
    dribles_certos INTEGER DEFAULT 0,
    
    -- Disciplina
    faltas_cometidas INTEGER DEFAULT 0,
    faltas_cometidas_por_90 DECIMAL(5,2) DEFAULT 0,
    faltas_sofridas INTEGER DEFAULT 0,
    cartoes_amarelos INTEGER DEFAULT 0,
    cartoes_amarelos_por_90 DECIMAL(5,3) DEFAULT 0,
    cartoes_vermelhos INTEGER DEFAULT 0,
    
    -- Goleiro
    defesas INTEGER DEFAULT 0,
    gols_sofridos INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    
    -- Índices Calculados (Issues 9-11)
    off_index DECIMAL(6,3) DEFAULT 0,      -- Índice ofensivo
    cross_index DECIMAL(6,3) DEFAULT 0,    -- Índice de cruzamentos/bola parada
    foul_index DECIMAL(6,3) DEFAULT 0,     -- Índice de faltas/cartões
    
    -- Metadados
    periodo VARCHAR(20) DEFAULT '2025',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(player_id, periodo)
);

-- ==================== ESCALAÇÕES ====================

CREATE TABLE IF NOT EXISTS lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    is_starter BOOLEAN DEFAULT TRUE,
    position_played VARCHAR(30),
    minutes_played INTEGER DEFAULT 0,
    rating DECIMAL(4,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lineups_match ON lineups(match_id);
CREATE INDEX IF NOT EXISTS idx_lineups_player ON lineups(player_id);

-- ==================== CALIBRAÇÃO ====================

CREATE TABLE IF NOT EXISTS calibration_data (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    method VARCHAR(30) NOT NULL,
    parameters JSONB,
    brier_before DECIMAL(6,4),
    brier_after DECIMAL(6,4),
    improvement_pct DECIMAL(5,2),
    n_samples INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== PREVISÕES (LOG) ====================

CREATE TABLE IF NOT EXISTS predictions_log (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    
    -- Lambdas calculados
    lambda_home_goals DECIMAL(5,3),
    lambda_away_goals DECIMAL(5,3),
    lambda_home_corners DECIMAL(5,2),
    lambda_away_corners DECIMAL(5,2),
    
    -- Probabilidades previstas
    prob_home_win DECIMAL(5,4),
    prob_draw DECIMAL(5,4),
    prob_away_win DECIMAL(5,4),
    prob_over_25 DECIMAL(5,4),
    prob_btts DECIMAL(5,4),
    prob_over_95_corners DECIMAL(5,4),
    
    -- Resultado real (para backtest)
    actual_home_goals INTEGER,
    actual_away_goals INTEGER,
    actual_corners INTEGER,
    
    -- Metadados
    model_version VARCHAR(20) DEFAULT 'v5.0',
    n_simulations INTEGER DEFAULT 50000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== VIEWS ÚTEIS ====================

-- View de times com estatísticas
CREATE OR REPLACE VIEW v_teams_full AS
SELECT 
    t.id,
    t.nome,
    t.liga,
    ts.jogos_total,
    ts.gols_marcados_media,
    ts.gols_sofridos_media,
    ts.escanteios_for_media,
    ts.chutes_for_media,
    ts.cartoes_for_media,
    ts.attack_strength,
    ts.defense_weakness,
    ts.forma_multiplicador
FROM teams t
LEFT JOIN team_stats ts ON t.id = ts.team_id AND ts.periodo = '2025'
WHERE t.ativo = TRUE;

-- View de jogadores com estatísticas
CREATE OR REPLACE VIEW v_players_full AS
SELECT 
    p.id,
    p.nome,
    t.nome as time,
    p.posicao,
    ps.jogos_total,
    ps.gols_total,
    ps.gols_por_90,
    ps.assistencias_total,
    ps.finalizacoes_por_90,
    ps.cartoes_amarelos,
    ps.faltas_cometidas_por_90,
    ps.off_index,
    ps.cross_index,
    ps.foul_index
FROM players p
JOIN teams t ON p.time_atual_id = t.id
LEFT JOIN player_stats ps ON p.id = ps.player_id AND ps.periodo = '2025'
WHERE p.ativo = TRUE;

-- ==================== FUNÇÕES ====================

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_stats_updated_at
    BEFORE UPDATE ON team_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_stats_updated_at
    BEFORE UPDATE ON player_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== DADOS INICIAIS ====================

-- Inserir times do Brasileirão se não existirem
INSERT INTO teams (nome, liga) VALUES
    ('Flamengo', 'Brasileirão'),
    ('Palmeiras', 'Brasileirão'),
    ('São Paulo', 'Brasileirão'),
    ('Corinthians', 'Brasileirão'),
    ('Fluminense', 'Brasileirão'),
    ('Botafogo', 'Brasileirão'),
    ('Vasco', 'Brasileirão'),
    ('Internacional', 'Brasileirão'),
    ('Grêmio', 'Brasileirão'),
    ('Atlético-MG', 'Brasileirão'),
    ('Cruzeiro', 'Brasileirão'),
    ('Santos', 'Brasileirão'),
    ('Bahia', 'Brasileirão'),
    ('Fortaleza', 'Brasileirão'),
    ('Ceará', 'Brasileirão'),
    ('Sport', 'Brasileirão'),
    ('Athletico-PR', 'Brasileirão'),
    ('Coritiba', 'Brasileirão'),
    ('Goiás', 'Brasileirão'),
    ('Cuiabá', 'Brasileirão')
ON CONFLICT (nome) DO NOTHING;

-- Mensagem de conclusão
DO $$
BEGIN
    RAISE NOTICE 'Schema RAG Estatísticas criado com sucesso!';
END $$;
