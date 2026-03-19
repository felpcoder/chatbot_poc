# 1. Imagem base Node LTS
FROM node:20

# 2. Diretório de trabalho dentro do container
WORKDIR /app

# 3. Copiar arquivos de dependências primeiro (para aproveitar cache)
COPY package*.json ./

# 4. Instalar dependências
RUN npm install

# 5. Copiar o restante do código
COPY . .

# 6. Expor porta do Vite
EXPOSE 5173
# 7. Comando padrão para desenvolvimento
CMD ["npx", "vite", "--host", "--port", "5173"]