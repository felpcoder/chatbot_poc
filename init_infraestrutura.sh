# Criacao Infraestrutura

# Docker
# conforme link https://docs.docker.com/engine/install/ubuntu/

# garantir que nao existe conflito
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)

sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# para verificar que funciona usar:

#sudo docker run hello-world

# node
#garantir que o docker esta corretamente instalado
sudo docker pull node:24-alpine


# clone repo projects

# Frontend

git clone https://github.com/felpcoder/chatbot_poc.git


# front end
# na pasta de frontend
npm install 

npm run dev


# backend

sudo apt install python3.12-venv
sudo apt install pip


# salvar backup.sql no diretorio do initdb

# rodar 

cat backup.sql | docker exec -i database psql -U postgres

# precisa do container database rodando para isso
# precisa setar uma senha desprezível no dockercompose no primeiro run para isso, depois pode retirar a senha do dockercompose


# use o comando abaixo para limpar e iniciar o docker compose

sudo -E docker compose down --remove-orphans && sudo -E docker builder prune -a -f && sudo -E docker image prune -a -f && sudo -E docker compose up --build