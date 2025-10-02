# 🛠️ Setup Guide - RPG Chromance Backend

Guia passo a passo para configurar e executar o backend do RPG Chromance.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.11+**
- **Docker e Docker Compose**
- **Git**
- **VS Code** (recomendado com extensão Dev Containers)

---

## 🚀 Instalação Rápida

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/RPG-Chromance-Back.git
cd RPG-Chromance-Back
```

### 2. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
touch .env
```

Adicione o seguinte conteúdo:

```bash
# MongoDB
MONGO_URI="mongodb://localhost:27017"
MONGO_DB="rpgdb"

# CORS (URLs do frontend)
CORS_ORIGINS="http://localhost:4200,http://127.0.0.1:4200"

# Groq API (obrigatório para IA funcionar)
GROQ_API_KEY="sua-chave-groq-aqui"

# Configurações do LLM
LLM_MODEL=llama-3.1-8b-instant
LLM_MAX_TOKENS="500"
LLM_TEMPERATURE="0.8"
```

### 3. Obtenha sua Chave Groq API

1. Acesse https://console.groq.com
2. Crie uma conta gratuita
3. Vá em **API Keys**
4. Clique em **Create API Key**
5. Copie a chave e cole no `.env`

### 4. Suba os Containers Docker

Na pasta raiz do projeto:

```bash
docker-compose up -d
```

Isso irá iniciar:
- **MongoDB** (porta 27017)
- **Mongo Express** (porta 8081 - interface web)

### 5. Entre no Dev Container (VS Code)

1. Abra o projeto no VS Code
2. Pressione `F1` e digite: **Dev Containers: Reopen in Container**
3. Aguarde o container ser construído

### 6. Instale as Dependências

Dentro do container:

```bash
pip install -r requirements.txt
```

### 7. Popule o Banco com Campanhas Base

```bash
python scripts/seed_campaigns.py
```

Confirme digitando `s` quando solicitado.

### 8. Inicie o Servidor

```bash
python scripts/run_dev.py
```

O servidor estará disponível em: **http://localhost:8000**

---

## ✅ Verificação da Instalação

### Teste os Health Checks

```bash
# Health geral
curl http://localhost:8000/health

# Liveness
curl http://localhost:8000/liveness

# Readiness
curl http://localhost:8000/readiness
```

### Acesse a Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Verifique o MongoDB

Acesse **Mongo Express** em: http://localhost:8081

- **Usuário**: `admin`
- **Senha**: `admin`

---

## 🗂️ Estrutura das Collections MongoDB

Após o seed, você terá:

```
rpgdb/
├── users              # Usuários cadastrados
├── characters         # Personagens dos usuários
├── campaigns          # Campanhas base (globais)
└── campaign_progress  # Progresso individual por usuário
```

---

## 🧪 Testando a API

### 1. Criar Usuário

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@exemplo.com",
    "senha": "senha123"
  }'
```

### 2. Fazer Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@exemplo.com",
    "senha": "senha123"
  }'
```
---

## 🐛 Troubleshooting

### Erro: "MongoDB connection refused"

```bash
# Verifique se o container está rodando
docker ps | grep mongo

# Reinicie o MongoDB
docker-compose restart mongo
```

### Erro: "GROQ_API_KEY not found"

Verifique se o `.env` está na raiz do projeto e contém a chave válida.

### Erro: "Module not found"

```bash
# Reinstale as dependências
pip install --force-reinstall -r requirements.txt
```

### ChromaDB não inicializa

```bash
# Remova a pasta e deixe recriar
rm -rf chroma_db/
# Reinicie o servidor
```

### Porta 8000 já em uso

```bash
# Descubra o processo
lsof -i :8000

# Mate o processo
kill -9 PID
```

---

## 🔄 Comandos Úteis

```bash
# Popular campanhas novamente
python scripts/seed_campaigns.py

# Rodar em modo desenvolvimento
python scripts/run_dev.py

# Formatar código
black app/

# Verificar estilo
flake8 app/

# Limpar cache Python
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## 🌐 Variáveis de Ambiente Completas

```bash
# MongoDB
MONGO_URI="mongodb://localhost:27017"
MONGO_DB="rpgdb"

# CORS
CORS_ORIGINS="http://localhost:4200,http://127.0.0.1:4200"

# Groq API
GROQ_API_KEY="gsk_..."
LLM_MODEL=llama-3.1-8b-instant
LLM_MAX_TOKENS="500"
LLM_TEMPERATURE="0.8"

```

---

## 📊 Monitoramento

---

## 🔒 Segurança

### Em Desenvolvimento

- JWT expira em 24h
- Refresh token válido por 7 dias
- Senhas criptografadas com bcrypt (12 rounds)

---

## 📝 Próximos Passos

1. Configure o frontend: `/RPG-Chromance-Front`
2. Crie seu primeiro personagem
3. Inicie uma campanha
4. Explore a documentação da API

---

## Suporte

- Documentação completa: `README.md`
- API Docs: http://localhost:8000/docs