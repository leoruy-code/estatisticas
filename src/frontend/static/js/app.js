/**
 * RAG Estatísticas - Frontend JavaScript
 */

const API_URL = '';

// State
let teams = [];
let selectedMandante = null;
let selectedVisitante = null;

// ==================== INIT ====================

document.addEventListener('DOMContentLoaded', async () => {
    await loadTeams();
    setupEventListeners();
});

// ==================== API CALLS ====================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadTeams() {
    try {
        const data = await apiCall('/api/teams');
        teams = data.teams;
        populateTeamSelects();
        renderTeamsGrid();
    } catch (error) {
        console.error('Erro ao carregar times:', error);
        // Fallback with sample data
        teams = [
            { id: 1, nome: 'Flamengo', ataque: 1.25, defesa: 0.85, confianca: 90 },
            { id: 2, nome: 'Palmeiras', ataque: 1.20, defesa: 0.80, confianca: 88 },
            { id: 3, nome: 'Corinthians', ataque: 1.10, defesa: 1.05, confianca: 85 },
        ];
        populateTeamSelects();
        renderTeamsGrid();
    }
}

async function predict(mandanteId, visitanteId) {
    showLoading(true);
    
    try {
        const competicao = document.getElementById('competicao-select').value;
        
        const data = await apiCall('/api/predict', {
            method: 'POST',
            body: JSON.stringify({
                mandante_id: mandanteId,
                visitante_id: visitanteId,
                league_id: 1,
                tipo_competicao: competicao
            })
        });
        
        displayResults(data);
    } catch (error) {
        console.error('Erro na previsão:', error);
        alert('Erro ao gerar previsão. Tente novamente.');
    } finally {
        showLoading(false);
    }
}

// ==================== UI FUNCTIONS ====================

function populateTeamSelects() {
    const mandanteSelect = document.getElementById('mandante-select');
    const visitanteSelect = document.getElementById('visitante-select');
    
    const options = teams.map(t => 
        `<option value="${t.id}">${t.nome}</option>`
    ).join('');
    
    mandanteSelect.innerHTML = '<option value="">Selecione...</option>' + options;
    visitanteSelect.innerHTML = '<option value="">Selecione...</option>' + options;
}

function renderTeamsGrid() {
    const grid = document.getElementById('teams-grid');
    
    grid.innerHTML = teams.map(team => `
        <div class="team-card" onclick="selectTeam(${team.id})">
            <div class="team-card-header">
                <span class="team-name">${team.nome}</span>
                <span class="team-confidence">${team.confianca}%</span>
            </div>
            <div class="team-stats">
                <div class="team-stat">
                    <div class="team-stat-label">Ataque</div>
                    <div class="team-stat-value">${team.ataque.toFixed(2)}</div>
                </div>
                <div class="team-stat">
                    <div class="team-stat-label">Defesa</div>
                    <div class="team-stat-value">${team.defesa.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayResults(data) {
    const results = document.getElementById('results');
    results.classList.remove('hidden');
    
    // Match title
    document.getElementById('match-title').textContent = 
        `${data.partida.mandante} vs ${data.partida.visitante}`;
    
    // Confidence
    document.getElementById('confidence-badge').textContent = 
        `${data.confianca}% confiança`;
    
    // Result probabilities
    const previsao = data.previsao;
    const resultado = previsao.resultado;
    
    const probHome = document.getElementById('prob-home');
    const probDraw = document.getElementById('prob-draw');
    const probAway = document.getElementById('prob-away');
    
    probHome.style.width = `${resultado.vitoria_mandante}%`;
    probHome.querySelector('.prob-value').textContent = `${resultado.vitoria_mandante}%`;
    
    probDraw.style.width = `${resultado.empate}%`;
    probDraw.querySelector('.prob-value').textContent = `${resultado.empate}%`;
    
    probAway.style.width = `${resultado.vitoria_visitante}%`;
    probAway.querySelector('.prob-value').textContent = `${resultado.vitoria_visitante}%`;
    
    // Goals
    const gols = previsao.gols;
    document.getElementById('gols-mandante').textContent = gols.mandante_media;
    document.getElementById('gols-visitante').textContent = gols.visitante_media;
    document.getElementById('gols-total').textContent = gols.total_media;
    document.getElementById('over-15').textContent = `${gols['over_1.5']}%`;
    document.getElementById('over-25').textContent = `${gols['over_2.5']}%`;
    document.getElementById('btts').textContent = `${gols.btts}%`;
    
    // Cards
    const cartoes = previsao.cartoes;
    document.getElementById('cartoes-mandante').textContent = cartoes.mandante_media;
    document.getElementById('cartoes-visitante').textContent = cartoes.visitante_media;
    document.getElementById('over-cartoes').textContent = `${cartoes['over_4.5']}%`;
    
    // Corners
    const escanteios = previsao.escanteios;
    document.getElementById('escanteios-mandante').textContent = escanteios.mandante_media;
    document.getElementById('escanteios-visitante').textContent = escanteios.visitante_media;
    document.getElementById('over-escanteios').textContent = `${escanteios['over_10.5']}%`;
    
    // Scores
    const scoresGrid = document.getElementById('scores-grid');
    scoresGrid.innerHTML = previsao.placares.slice(0, 8).map(p => `
        <div class="score-item">
            <div class="score-value">${p.placar}</div>
            <div class="score-prob">${p.probabilidade}%</div>
        </div>
    `).join('');
    
    // Scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

function selectTeam(teamId) {
    const team = teams.find(t => t.id === teamId);
    if (!team) return;
    
    const mandanteSelect = document.getElementById('mandante-select');
    const visitanteSelect = document.getElementById('visitante-select');
    
    if (!mandanteSelect.value) {
        mandanteSelect.value = teamId;
        updateTeamBadge('mandante', team);
    } else if (!visitanteSelect.value && mandanteSelect.value != teamId) {
        visitanteSelect.value = teamId;
        updateTeamBadge('visitante', team);
    }
    
    checkPredictButton();
}

function updateTeamBadge(type, team) {
    const badge = document.getElementById(`${type}-badge`);
    if (team) {
        badge.innerHTML = `
            <span>Ataque: ${team.ataque.toFixed(2)} | Defesa: ${team.defesa.toFixed(2)}</span>
        `;
    } else {
        badge.innerHTML = '';
    }
}

function checkPredictButton() {
    const mandanteSelect = document.getElementById('mandante-select');
    const visitanteSelect = document.getElementById('visitante-select');
    const predictBtn = document.getElementById('predict-btn');
    
    const canPredict = mandanteSelect.value && visitanteSelect.value && 
                       mandanteSelect.value !== visitanteSelect.value;
    
    predictBtn.disabled = !canPredict;
}

// ==================== EVENT LISTENERS ====================

function setupEventListeners() {
    const mandanteSelect = document.getElementById('mandante-select');
    const visitanteSelect = document.getElementById('visitante-select');
    const predictBtn = document.getElementById('predict-btn');
    
    mandanteSelect.addEventListener('change', (e) => {
        const team = teams.find(t => t.id == e.target.value);
        updateTeamBadge('mandante', team);
        checkPredictButton();
    });
    
    visitanteSelect.addEventListener('change', (e) => {
        const team = teams.find(t => t.id == e.target.value);
        updateTeamBadge('visitante', team);
        checkPredictButton();
    });
    
    predictBtn.addEventListener('click', () => {
        const mandanteId = parseInt(mandanteSelect.value);
        const visitanteId = parseInt(visitanteSelect.value);
        
        if (mandanteId && visitanteId) {
            predict(mandanteId, visitanteId);
        }
    });
    
    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
            
            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}
