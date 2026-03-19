# Dockerfile
# 1. Escolhe a imagem base
FROM python:3.12-slim

# 2. Define diretório de trabalho dentro do container
WORKDIR /app

# 3. Copia os arquivos de requirements
COPY requirements.txt .

# 4. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia o restante do código da API
COPY . .

# 6. Expõe a porta que a API vai rodar
EXPOSE 8000

# 7. Comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]