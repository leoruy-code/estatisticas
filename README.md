# ⚽ Sistema de Análise Poisson - Brasileirão 2025

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)
![License](https://img.shields.io/badge/License-MIT-green)

**Sistema profissional de análise de apostas esportivas usando distribuição Poisson**

[Features](#-features) • [Instalação](#-instalação) • [Como Usar](#-como-usar) • [Tecnologias](#-tecnologias)

</div>

---

## 🎯 Sobre o Projeto

Sistema completo de análise estatística para apostas no Brasileirão 2025, baseado em **metodologia profissional de casas de apostas**. Utiliza distribuição de Poisson para calcular probabilidades precisas de eventos em partidas de futebol.

### 📊 Base de Dados
- **722 jogadores** com estatísticas completas da temporada
- **20 times** do Brasileirão 2025
- Dados reais de **partidas, gols, escanteios, chutes e faltas**
- Histórico de **últimas 20 partidas** por time
- **Multiplicadores de forma** baseados em desempenho recente

---

## 🚀 Features

### 🎲 Análise de Partidas (Poisson)
- **Probabilidades Over/Under** para gols (0.5, 1.5, 2.5, 3.5)
- **Probabilidades Over/Under** para escanteios (8.5, 9.5, 10.5, 11.5)
- **BTTS** (Both Teams To Score)
- **Resultado 1X2** (vitória casa, empate, vitória fora)
- **Top placares** mais prováveis
- **Odds justas** sem margem da casa

### 📈 Rankings e Estatísticas
- **⚔️ Ataque**: Attack Strength por time
- **🛡️ Defesa**: Defense Weakness (dados reais de gols sofridos)
- **📈 Forma**: Multiplicadores baseados em últimas 5 partidas
- **🚩 Escanteios**: Médias por time (casa/fora)

### 🧮 Motor de Cálculo
```python
λ = league_avg × attack_strength × opponent_defense_weakness × home_advantage × form_multiplier
```

- **Attack Strength** = Gols marcados / Média da liga
- **Defense Weakness** = Gols sofridos / Média da liga (dados reais)
- **Form Multiplier** = Ajuste baseado em desempenho recente (0.8 - 1.2)
- **Home Advantage** = 1.08 (8% a mais em casa)

---

## 🛠️ Instalação

### Pré-requisitos
- Python 3.14+
- pip

### Passo a Passo

```bash
# 1. Clone o repositório
git clone https://github.com/leoruy-code/estatisticas.git
cd estatisticas

# 2. Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou
.venv\Scripts\activate  # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Execute o frontend
streamlit run src/frontend/app.py
```

O sistema abrirá automaticamente em `http://localhost:8501`

---

## 💻 Como Usar

### Interface Web

1. **🎯 Análise de Partida**
   - Selecione time da casa e visitante
   - Veja forma recente automática dos times
   - Analise probabilidades de gols e escanteios
   - Obtenha odds justas para suas apostas

2. **🏆 Rankings**
   - Consulte força ofensiva/defensiva
   - Veja times em boa/má forma
   - Compare médias de escanteios

3. **📊 Ver Times e Estatísticas**
   - Estatísticas completas de cada time
   - Lista de jogadores com métricas individuais

### Análise via Python

```python
from src.poisson_analyzer import PoissonAnalyzer

# Inicializar analisador
analyzer = PoissonAnalyzer()

# Analisar partida
pred = analyzer.prever_partida("Flamengo", "Palmeiras")

print(f"Over 2.5 gols: {pred.prob_over_25_goals*100:.1f}%")
print(f"Over 10.5 escanteios: {pred.prob_over_105_corners*100:.1f}%")
print(f"BTTS: {pred.prob_btts*100:.1f}%")
```

---

## 📁 Estrutura do Projeto

```
estatisticas/
├── src/
│   ├── frontend/
│   │   └── app.py                    # Interface Streamlit
│   ├── poisson_analyzer.py           # Motor de análise Poisson
│   ├── buscar_estatisticas.py        # Coleta stats jogadores
│   ├── buscar_partidas.py            # Coleta histórico partidas
│   └── buscar_escanteios.py          # Coleta dados escanteios
├── data/
│   ├── jogadores.json                # 722 jogadores
│   └── times.json                    # 20 times + métricas
└── requirements.txt
```

---

## 🔬 Tecnologias

| Tecnologia | Uso |
|------------|-----|
| **Python 3.14** | Linguagem principal |
| **Streamlit** | Interface web interativa |
| **SciPy** | Cálculos de distribuição Poisson |
| **NumPy** | Operações matemáticas |
| **Requests** | API SofaScore |
| **Pandas** | Manipulação de dados |

---

## 📊 Exemplo de Análise

**Flamengo (casa) vs Palmeiras (fora)**

```
📊 LAMBDAS ESTIMADOS
  λ Gols Flamengo: 1.18
  λ Gols Palmeiras: 1.08
  λ Total Gols: 2.26
  λ Total Escanteios: 13.25

🎯 PROBABILIDADES GOLS
  Over 2.5: 39.2% (odd 2.55)
  BTTS: 45.7% (odd 2.19)

🚩 ESCANTEIOS
  Over 10.5: 76.9% (odd 1.30)
  Over 11.5: 67.2% (odd 1.49)

🏆 RESULTADO (1X2)
  Vitória Flamengo: 38.2% (odd 2.62)
  Empate: 28.6% (odd 3.49)
  Vitória Palmeiras: 33.1% (odd 3.02)
```

---

## 🔄 Atualização de Dados

Para atualizar estatísticas dos times:

```bash
# Atualizar estatísticas de jogadores
python src/buscar_estatisticas.py

# Atualizar histórico de partidas e forma
python src/buscar_partidas.py

# Atualizar dados de escanteios
python src/buscar_escanteios.py
```

---

## 📝 Metodologia

O sistema segue metodologia profissional baseada em:

1. **Distribuição de Poisson** para eventos raros (gols)
2. **Força ofensiva/defensiva** normalizada pela média da liga
3. **Dados reais** de partidas para precisão
4. **Multiplicadores contextuais** (casa, forma, etc.)
5. **Odds justas** sem margem da casa de apostas

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas features
- Melhorar a documentação
- Adicionar novos mercados de apostas

---

## 📜 Licença

Este projeto é fornecido "como está" para fins educacionais e de pesquisa.

**⚠️ Aviso**: Este sistema é para análise estatística. Aposte com responsabilidade.

---

## 👨‍💻 Autor

**Leonardo Ruy** - [@leoruy-code](https://github.com/leoruy-code)

---

<div align="center">

**⭐ Se este projeto te ajudou, considere dar uma estrela!**

</div>
