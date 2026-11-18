
# Imagem oficial do Python
FROM python:3.13-slim

# Define a pasta de trabalho no container
WORKDIR /app

# Evita arquivos .pyc e ativa logs sem buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copia a lista de dependências
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY app/ ./app/

# Cria o diretório de dados persistentes
RUN mkdir -p /app/dados

# Executa com usuário sem privilégios de root
RUN useradd --create-home botuser && chown -R botuser:botuser /app
USER botuser

# Inicia o bot do Telegram
CMD ["python", "app/bot_telegram.py"]
