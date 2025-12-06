-- Schema para banco de dados de estatísticas de futebol
-- PostgreSQL

CREATE TABLE IF NOT EXISTS times (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    imagem_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jogadores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    time_id INTEGER REFERENCES times(id) ON DELETE CASCADE,
    posicao VARCHAR(50),
    foto_url TEXT,
    sofascore_id INTEGER,
    
    -- Estatísticas básicas
    gols INTEGER DEFAULT 0,
    assistencias INTEGER DEFAULT 0,
    partidas INTEGER DEFAULT 0,
    minutos_jogados INTEGER DEFAULT 0,
    
    -- Cartões
    cartoes_amarelos INTEGER DEFAULT 0,
    cartoes_vermelhos INTEGER DEFAULT 0,
    
    -- Faltas
    faltas_cometidas INTEGER DEFAULT 0,
    faltas_sofridas INTEGER DEFAULT 0,
    
    -- Finalização
    chutes INTEGER DEFAULT 0,
    chutes_no_gol INTEGER DEFAULT 0,
    grandes_chances_perdidas INTEGER DEFAULT 0,
    grandes_chances_criadas INTEGER DEFAULT 0,
    gols_esperados DECIMAL(5,2) DEFAULT 0,
    conversao_gols DECIMAL(5,2) DEFAULT 0,
    
    -- Defesa
    desarmes INTEGER DEFAULT 0,
    interceptacoes DECIMAL(5,1) DEFAULT 0,
    defesas INTEGER DEFAULT 0,
    gols_sofridos INTEGER DEFAULT 0,
    
    -- Passes
    passes_certos DECIMAL(6,1) DEFAULT 0,
    total_passes INTEGER DEFAULT 0,
    passes_decisivos INTEGER DEFAULT 0,
    assistencias_esperadas DECIMAL(5,2) DEFAULT 0,
    passes_longos_certos DECIMAL(5,1) DEFAULT 0,
    cruzamentos_certos DECIMAL(5,1) DEFAULT 0,
    
    -- Dribles e duelos
    dribles_certos DECIMAL(5,1) DEFAULT 0,
    total_dribles INTEGER DEFAULT 0,
    duelos_ganhos INTEGER DEFAULT 0,
    duelos_totais INTEGER DEFAULT 0,
    duelos_aereos_ganhos INTEGER DEFAULT 0,
    duelos_terrestres_ganhos INTEGER DEFAULT 0,
    
    -- Posse e erros
    posse_perdida INTEGER DEFAULT 0,
    erros_finalizacao INTEGER DEFAULT 0,
    erros_gol INTEGER DEFAULT 0,
    impedimentos INTEGER DEFAULT 0,
    
    -- Pênaltis
    penaltis_marcados INTEGER DEFAULT 0,
    penaltis_sofridos INTEGER DEFAULT 0,
    penaltis_cometidos INTEGER DEFAULT 0,
    
    -- Performance
    rating DECIMAL(4,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(nome, time_id)
);

-- Índices para performance
CREATE INDEX idx_jogadores_time ON jogadores(time_id);
CREATE INDEX idx_jogadores_nome ON jogadores(nome);
CREATE INDEX idx_jogadores_gols ON jogadores(gols DESC);
CREATE INDEX idx_jogadores_assistencias ON jogadores(assistencias DESC);
CREATE INDEX idx_jogadores_rating ON jogadores(rating DESC);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_times_updated_at BEFORE UPDATE ON times
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jogadores_updated_at BEFORE UPDATE ON jogadores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View para estatísticas agregadas por time
CREATE OR REPLACE VIEW estatisticas_times AS
SELECT 
    t.id,
    t.nome,
    t.imagem_url,
    COUNT(j.id) as total_jogadores,
    SUM(j.gols) as total_gols,
    SUM(j.assistencias) as total_assistencias,
    AVG(j.rating) as rating_medio,
    SUM(j.partidas) as total_partidas
FROM times t
LEFT JOIN jogadores j ON t.id = j.time_id
GROUP BY t.id, t.nome, t.imagem_url;
