
# Sistema de Estatísticas de Futebol para Apostas ⚽

Este projeto tem como objetivo analisar informações de jogadores e times para gerar estatísticas e probabilidades para apostas múltiplas em futebol, facilitando a tomada de decisão para apostadores.

## 🚀 Funcionalidades

- ✅ **Cadastro de jogadores** com estatísticas detalhadas (gols, assistências, cartões, etc.)
- ✅ **Criação e gerenciamento de times** com escalações
- ✅ **Análise estatística** de times e jogadores
- ✅ **Interface web moderna** com Streamlit
- ✅ **Armazenamento em JSON** (fácil de editar e importar/exportar)
- ✅ **Deploy com Docker** para facilitar a execução

## 📦 Requisitos

- **Docker** e **Docker Compose** (recomendado)
- OU **Python 3.12+** (para execução local)

## 🐳 Como Usar com Docker (Recomendado)

### 1. Construir e Iniciar o Container

```bash
docker-compose up --build
```

### 2. Acessar a Aplicação

Abra seu navegador em: **http://localhost:8501**

### 3. Parar o Container

```bash
docker-compose down
```

### Comandos Docker Úteis

```bash
# Reconstruir a imagem
docker-compose build

# Rodar em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar e remover volumes
docker-compose down -v
```

## 💻 Como Usar Localmente (sem Docker)

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação Web

```bash
streamlit run src/frontend/app.py
```

Acesse: **http://localhost:8501**

### 3. Usar CLI para Cadastro

```bash
# Cadastrar jogadores e times via linha de comando
python src/data_manager.py

# Analisar estatísticas de times
python src/analyze.py
```

## 📁 Estrutura do Projeto

```
RAG ESTATISTICAS/
├── Dockerfile              # Configuração Docker
├── docker-compose.yml      # Orquestração Docker
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── data/                  # Dados persistidos
│   ├── jogadores.json    # Jogadores cadastrados
│   └── times.json        # Times cadastrados
└── src/                   # Código-fonte
    ├── models.py         # Modelos de dados
    ├── data_manager.py   # CLI para cadastro
    ├── analyze.py        # Análise estatística
    └── frontend/
        └── app.py        # Interface Streamlit
```

## 📊 Dados de Exemplo

O projeto já vem com dados de exemplo incluindo:
- 6 jogadores (Neymar Jr, Cristiano Ronaldo, Benzema, Mané, Mahrez, Mitrovic)
- 2 times (Al-Nassr e Al-Hilal)

Você pode adicionar, editar ou remover dados através da interface web ou editando os arquivos JSON.

## 🎯 Próximas Funcionalidades

- [ ] Comparação direta entre times (estatísticas lado a lado)
- [ ] Gráficos e visualizações interativas
- [ ] Exportação de relatórios em PDF
- [ ] Importação de dados via CSV/Excel
- [ ] Web scraping de sites de estatísticas
- [ ] API REST para integração
- [ ] Machine learning para previsões
- [ ] Histórico de partidas
- [ ] Cálculo de probabilidades de apostas

## 🛠️ Tecnologias Utilizadas

- **Python 3.12**
- **Streamlit** - Interface web
- **Docker** - Containerização
- **JSON** - Armazenamento de dados

## 📝 Notas

- Os dados são armazenados em arquivos JSON na pasta `data/`
- O Docker monta um volume para persistir os dados entre reinicializações
- Você pode editar os arquivos JSON diretamente se preferir

## 🤝 Contribuições

Este projeto está em desenvolvimento ativo e aberto a sugestões e contribuições!

---

**Desenvolvido para análise de estatísticas esportivas** 🎲⚽
