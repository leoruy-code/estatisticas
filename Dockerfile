# Dockerfile para rodar o sistema de estatísticas de futebol com Streamlit
FROM python:3.12-slim

WORKDIR /app

# Copiar apenas requirements.txt primeiro (melhor cache do Docker)
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o resto do projeto
COPY . .

# Criar diretório de dados se não existir
RUN mkdir -p /app/data

EXPOSE 8501

CMD ["streamlit", "run", "src/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
