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

git clone https://github.com/felpcoder/chatbot_poc_frontend.git

## Para rodar a primeira vez

#Ir até a pasta e executar 

npm install 

npm run dev

# instalar python venv para backend
sudo apt install python3.12-venv

#instalar pip
sudo apt install pip
