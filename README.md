<p align="center">
  <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/eab59c4b-d54e-48b7-9e8b-96f39217e270" />
</p>

# 🎮 RPG Chromance - Backend API

API RESTful para o jogo de RPG textual com IA "RPG Chromance".
Parte do Programa Trainee da Wise Systems.

---

## 🚀 Sobre o Projeto

O **RPG Chromance** é um sistema web de RPG textual ambientado em um universo cyberpunk que utiliza um modelo de linguagem (LLM) para criar narrativas dinâmicas e interativas. Este repositório contém o back-end da aplicação, desenvolvido em Python com o framework FastAPI, responsável por gerenciar toda a lógica de negócio, autenticação, personagens, campanhas e a integração com a IA.

---

## 🛠️ Tecnologias Principais

- **Linguagem**: Python 3.11
- **Framework**: FastAPI
- **Banco de Dados**: MongoDB
- **Banco Vetorial**: ChromaDB (para memória contextual da IA com RAG)
- **Autenticação**: JWT (JSON Web Tokens)
- **Inteligência Artificial**: Groq API com modelo Llama 3.1 70B para geração de narrativas
- **Containerização**: Docker e Docker Compose
- **Dev Environment**: VS Code Dev Container

---

## ✨ Funcionalidades

### Autenticação de Usuários
- Cadastro (`/signup`), login (`/login`) e verificação de usuário (`/me`) com JWT
- Atualização de perfil (`/profile`)
- Sistema de refresh token para renovação automática

### Gerenciamento de Personagens
- Criação, listagem, visualização de detalhes e exclusão de personagens
- Sistema de seleção de personagem ativo
- Sistema de inventário com itens e recompensas
- Uso de itens com aplicação de bônus aos atributos (vida, energia, força, inteligência)

### Sistema de Campanhas
- 3 capítulos pré-definidos (Cubo das Sombras, Laboratório de Cristais Arcanos, Coliseu de Neon)
- Modelo de progresso individual por usuário
- Sistema de inicialização, acompanhamento e cancelamento de campanhas
- Completar capítulos com extração automática de lore

### Integração com LLM (Narrativa Dinâmica)
- **Sistema de Progressão Narrativa**: 10 interações por capítulo divididas em 3 fases
  - Introdução (1-3): Estabelecimento de contexto e atmosfera
  - Desenvolvimento (4-7): Desafios principais e progressão
  - Resolução (8-10): Clímax e entrega de recompensas
- Geração de ações contextuais sugeridas pela IA
- Detecção automática e entrega de recompensas de capítulo
- Sistema de RAG (Retrieval-Augmented Generation) para memória contextual

### Sistema de World Lore (ChromaDB)
- **3 Collections**:
  - `campaign_current`: Narrativas da campanha/capítulo ativo
  - `campaign_archive`: Histórico de campanhas finalizadas
  - `world_lore`: Conhecimento permanente do universo Chromance
- Extração automática de lore ao finalizar capítulos
- Busca vetorial para recuperação de contexto relevante
- Arquivamento automático de narrativas completadas

### Persistência de Dados
- Armazenamento de usuários, personagens e progresso de campanhas no MongoDB
- Sistema de vector store para narrativas e memória contextual
- Health checks para monitoramento de infraestrutura

---

## 🏁 Começando

Estas instruções permitirão que você tenha uma cópia do projeto em operação na sua máquina local para desenvolvimento e testes.

### Pré-requisitos

- Docker e Docker Compose
- Visual Studio Code com a extensão Dev Containers (opcional)
- Python 3.11+ (para execução local)

---

## 🐳 Executando com Docker

### Estrutura de Diretórios

```
/sua-pasta-de-projetos
├── /RPG-Chromance-Back/   <-- (repositório backend)
├── /RPG-Chromance-Front/  <-- (repositório frontend)
└── docker-compose.yml     <-- (crie este arquivo na raiz)
```

### Docker Compose Completo

Crie um arquivo `docker-compose.yml` na raiz que contenha ambos os repositórios:

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./RPG-Chromance-Back
      dockerfile: ./.devcontainer/Dockerfile
    container_name: rpg_chromance_backend
    volumes:
      - ./RPG-Chromance-Back:/workspaces/RPG-Chromance-Back:cached
      - ./RPG-Chromance-Back/chroma_db:/workspaces/RPG-Chromance-Back/chroma_db
    command: sleep infinity
    ports:
      - "8000:8000"
    depends_on:
      - mongo
    env_file:
      - ./RPG-Chromance-Back/.env
    environment:
      MONGO_URI: "mongodb://mongo:27017"
      MONGO_DB: "rpgdb"

  frontend:
    build:
      context: ./RPG-Chromance-Front
      dockerfile: ./.devcontainer/Dockerfile
    container_name: rpg_chromance_frontend
    volumes:
      - ./RPG-Chromance-Front:/workspace:cached
      - /workspace/node_modules
    command: sleep infinity
    ports:
      - "4200:4200"

  mongo:
    image: mongo:7
    container_name: rpg_chromance_mongo
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: rpgdb
    volumes:
      - mongodb_data:/data/db

  mongo-express:
    image: mongo-express:1
    container_name: rpg_chromance_mongo_express
    restart: unless-stopped
    depends_on:
      - mongo
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_SERVER: mongo
      ME_CONFIG_BASICAUTH_USERNAME: admin
      ME_CONFIG_BASICAUTH_PASSWORD: admin

volumes:
  mongodb_data:
```

### Passos para Execução

1. **Clone o repositório**:
```bash
git clone https://github.com/seu-usuario/RPG-Chromance-Back
cd RPG-Chromance-Back
```

2. **Suba os containers**:
```bash
docker-compose up --build -d
```

3. **Abra no VS Code** (opcional):
```bash
code .
```

4. O VS Code irá sugerir "Reopen in Container". Clique nesta opção.

5. Aguarde o Docker construir a imagem e iniciar o container.

6. **Inicie o servidor FastAPI**:
```bash
python scripts/run_dev.py
```

7. O servidor estará disponível em http://localhost:8000

---

## ⚙️ Configuração de Ambiente (.env)

Antes de executar o projeto, é crucial configurar as variáveis de ambiente.

### Localização do Arquivo

```
/RPG-Chromance-Back/
├── .env             <-- (crie este arquivo)
└── ...
```

### Exemplo de Configuração

```bash
# MongoDB
MONGO_URI="mongodb://localhost:27017"
MONGO_DB="rpgdb"

# CORS (adicione o URL do frontend)
CORS_ORIGINS="http://localhost:4200,http://127.0.0.1:4200"

# Groq API (obrigatório para funcionar a IA)
GROQ_API_KEY="sua-chave-groq-api-aqui"

# Configurações do LLM
LLM_MODEL="llama-3.1-70b-versatile"
LLM_MAX_TOKENS="500"
LLM_TEMPERATURE="0.8"
```

### Como Obter a Chave Groq

1. Acesse https://console.groq.com
2. Crie uma conta gratuita
3. Gere uma API key em "API Keys"
4. Cole a chave no arquivo `.env`

---

## 📜 Documentação da API

A documentação interativa da API é gerada automaticamente pelo FastAPI e pode ser acessada através dos seguintes URLs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🗂️ Estrutura de Pastas

```
/
├── app/                          # Código fonte da aplicação
│   ├── api/                      # Endpoints da API
│   │   ├── auth.py               # Autenticação e usuários
│   │   ├── characters.py         # Gerenciamento de personagens
│   │   ├── campaigns.py          # Sistema de campanhas
│   │   └── llm.py                # Integração com LLM
│   ├── core/                     # Configurações e segurança
│   │   ├── database.py           # Conexão MongoDB
│   │   ├── security.py           # JWT e criptografia
│   │   ├── middleware.py         # CORS e middlewares
│   │   └── dependencies.py       # Injeção de dependências
│   ├── models/                   # Modelos de dados MongoDB
│   │   ├── user.py               # Modelo de usuário
│   │   ├── character.py          # Modelo de personagem
│   │   ├── campaign.py           # Modelo de campanha
│   │   └── campaign_progress.py  # Modelo de progresso
│   ├── repositories/             # Camada de acesso a dados
│   │   ├── user_repo.py          # Repositório de usuários
│   │   └── character_repo.py     # Repositório de personagens
│   ├── schemas/                  # Validação Pydantic
│   │   ├── auth.py               # Schemas de autenticação
│   │   ├── character.py          # Schemas de personagem
│   │   ├── campaign.py           # Schemas de campanha
│   │   ├── llm.py                # Schemas de LLM
│   │   └── game.py               # Schemas de jogo
│   ├── services/                 # Lógica de negócio
│   │   ├── auth_service.py       # Serviço de autenticação
│   │   ├── character_service.py  # Serviço de personagens
│   │   ├── campaign_service.py   # Serviço de campanhas
│   │   ├── inventory_service.py  # Serviço de inventário
│   │   ├── llm_service.py        # Serviço de LLM e narrativa
│   │   └── vector_store_service.py # Serviço de ChromaDB
│   ├── config.py                 # Configurações da aplicação
│   └── main.py                   # Ponto de entrada FastAPI
├── .devcontainer/                # Configurações Dev Container
│   ├── devcontainer.json         # Config do VS Code
│   └── Dockerfile                # Imagem do container
├── docs/                         # Documentação
│   └── api.md                    # Documentação dos endpoints
├── scripts/                      # Scripts utilitários
│   ├── run_dev.py                # Script para rodar em dev
│   └── seed_campaigns.py         # Script para popular campanhas
├── tests/                        # Testes
│   ├── conftest.py               # Configuração do pytest
│   └── test_health.py            # Testes de health check
├── chroma_db/                    # Dados do ChromaDB (local)
├── .env                          # Variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo git
├── docker-compose.yml            # Orquestração Docker
├── pyproject.toml                # Configurações do projeto
├── requirements.txt              # Dependências de produção
└── README.md                     # Este arquivo
```

---

## 🎯 Sistema de Progressão Narrativa

O RPG Chromance implementa um sistema único de progressão em **10 interações por capítulo**:

### Fases da Narrativa

1. **Introdução (1-3 interações)**
   - Estabelecimento de atmosfera e contexto
   - Apresentação do ambiente
   - Elementos de mistério inicial

2. **Desenvolvimento (4-7 interações)**
   - Desafios principais do capítulo
   - Elevação progressiva de tensão
   - Progresso do personagem

3. **Resolução (8-10 interações)**
   - Clímax e confronto final
   - Entrega de recompensa do capítulo
   - Transição para próximo capítulo

### Sistema de Recompensas

Cada capítulo possui uma recompensa única que é automaticamente detectada e entregue:

- **Capítulo 1**: Cubo das Sombras (+5 Energia, +3 Inteligência)
- **Capítulo 2**: Cristal Arcano Puro (+4 Inteligência, +2 Vida)
- **Capítulo 3**: Cinturão do Campeão (+5 Força, +3 Vida)

---

## 🧠 Sistema RAG (Retrieval-Augmented Generation)

O projeto implementa um sistema sofisticado de memória contextual usando ChromaDB:

### Collections

1. **campaign_current**: Narrativas da campanha ativa
2. **campaign_archive**: Histórico de campanhas finalizadas
3. **world_lore**: Conhecimento permanente do universo Chromance

### Funcionalidades

- **Busca Vetorial**: Recupera narrativas relevantes baseadas em similaridade semântica
- **Extração de Lore**: Ao completar capítulos, extrai automaticamente fatos importantes para o world lore
- **Arquivamento**: Mantém histórico completo de todas as campanhas
- **Contexto Hierárquico**: Prioriza informações da campanha atual, complementa com world lore

---

## 🧪 Instalar dependências

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt
```
---

## 🔒 Segurança

- Autenticação via JWT com tokens de acesso (24h) e refresh (7 dias)
- Senhas criptografadas com bcrypt (12 rounds)
- Validação rigorosa de dados com Pydantic
- CORS configurável por ambiente

---

## 📝 Scripts Úteis

```bash
# Popular banco com campanhas base
python scripts/seed_campaigns.py

# Rodar servidor de desenvolvimento
python scripts/run_dev.py

# Formatar código
black app/

# Verificar estilo
flake8 app/

# Ordenar imports
isort app/
```

---

## 📄 Licença

Este projeto faz parte do Programa Trainee da Wise Systems.

---

## 🙏 Agradecimentos

- Wise Systems pelo programa de trainee
