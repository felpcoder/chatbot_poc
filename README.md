# 📌 Projeto: Chatbot de Risco de Crédito (FastAPI + React + PostgreSQL)

## 🧠 Visão Geral

Este projeto implementa um chatbot técnico voltado para **Risco de Crédito e Regulação Bancária**, utilizado como suporte para squads de dados (Cientistas, Engenheiros e PMs) em contexto bancário.

A aplicação é fullstack, composta por **backend**, **frontend** e infraestrutura containerizada, com execução local via **WSL (Ubuntu)** e exposição opcional para a web.

---

## 🏗️ Arquitetura

### 🔧 Backend

* Desenvolvido com **FastAPI**
* Responsável por:

  * Receber mensagens dos usuários
  * Processar contexto e histórico de conversas
  * Utilizar arquitetura **RAG (Retrieval-Augmented Generation)**
  * Integrar embeddings para busca semântica
  * Gerar respostas técnicas baseadas em documentos regulatórios

---

### 🎨 Frontend

* Desenvolvido com **React**
* Interface de interação com o usuário
* Consome a API do backend para envio e exibição das mensagens

---

### 🗄️ Banco de Dados

* **PostgreSQL**
* Armazena:

  * Usuários
  * Conversas
  * Histórico de mensagens

---

## 🐳 Infraestrutura

A aplicação é totalmente containerizada utilizando **Docker**.

Os serviços incluem:

* Backend (FastAPI)
* Frontend (React)
* Banco de dados (PostgreSQL)

### ▶️ Subindo o ambiente

Para subir o ambiente eu rodo:

```bash
sudo -E docker compose up --build
```
Vale salientar que mesmo com o código é preciso também do banco de dados com tabelas,  de setar corretamente as variáveis de ambiente, de configurar o cloudflared para conseguir rodar o projeto.

---

## 💻 Execução Local

O projeto está sendo executado em ambiente local via:

* **WSL (Ubuntu)**
* Acesso via link `[meu aplicativo](https://frontend.devpersonalprojects.com/)`


---

## 🌐 Exposição Externa

A aplicação pode ser disponibilizada na web utilizando:

* **Cloudflared Tunnel**

Essa abordagem permite:

* Expor o serviço local sem abrir portas manualmente
* Criar uma URL pública segura
* Facilitar testes e demonstrações

---

## 🧠 Objetivo de Negócio

O sistema foi projetado para atuar como um **especialista técnico em risco de crédito e regulação bancária**, com foco em:

* **Risco de Crédito**

  * PD (Probability of Default)
  * LGD (Loss Given Default)
  * EAD (Exposure at Default)
  * ECL (Expected Credit Loss)

* **Regulação Bancária**

  * Basileia III
  * Normativas do BACEN e CMN
  * IFRS 9
  * LGPD

* **Dados e Modelagem**

  * Estruturação de dados para risco
  * Pipelines ETL
  * Engenharia e ciência de dados aplicadas ao crédito

---

## 🧠 Funcionamento Técnico

O chatbot opera utilizando arquitetura:

### 🔍 RAG (Retrieval-Augmented Generation)

* Documentos regulatórios são convertidos em **embeddings**
* Armazenados e indexados para busca por similaridade
* A cada pergunta:

  1. O embedding da query é gerado
  2. Trechos mais relevantes são recuperados
  3. Esses dados são usados como contexto
  4. O modelo gera uma resposta fundamentada

---

## 📦 Tecnologias Utilizadas

* **FastAPI**
* **React**
* **PostgreSQL**
* **Docker / Docker Compose**
* **Cloudflared Tunnel**
* Arquitetura **RAG com embeddings**

---

## 🚀 Objetivo do Projeto

Criar uma base robusta para um assistente técnico capaz de:

* Apoiar decisões em risco de crédito
* Acelerar análises regulatórias
* Padronizar conhecimento técnico dentro de squads de dados
* Integrar dados, modelos e regulação em uma única interface

---

## To do

- Criar tela para que usuario possa se registrar.
- Criar layout para manter chats históricos
- Ajustar backend para criar mecanismo de chat histórico e de memória através desses chats por contexto.
- Melhorar readme dos subdiretórios