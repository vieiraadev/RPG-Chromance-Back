# API Documentation

## Visão Geral

Esta documentação descreve os endpoints disponíveis na API, organizados por funcionalidade.

---

## Auth

Endpoints relacionados à autenticação e gerenciamento de usuários.

### POST /api/auth/signup
Criar nova conta de usuário.

**Descrição:** Criar nova conta

### POST /api/auth/login
Autenticar usuário e retornar JWT.

**Descrição:** Autenticar e retornar JWT

### POST /api/auth/refresh
Renovar token de acesso expirado.

**Descrição:** Renovar token de acesso

### GET /api/auth/me
Obter dados do usuário autenticado.

**Descrição:** Dados do usuário autenticado

**Autenticação:** Requerida 🔒

### PUT /api/auth/profile
Atualizar dados do usuário autenticado.

**Descrição:** Atualizar dados do usuário autenticado

**Autenticação:** Requerida 🔒

### POST /api/auth/logout
Fazer logout e invalidar token.

**Descrição:** Fazer logout (invalidar token)

**Autenticação:** Requerida 🔒

---

## Characters

Endpoints para gerenciamento de personagens.

### POST /api/characters
Criar um novo personagem.

**Descrição:** Create Character

**Autenticação:** Requerida 🔒

### GET /api/characters
Listar todos os personagens.

**Descrição:** List Characters

**Autenticação:** Requerida 🔒

### GET /api/characters/selected
Obter o personagem atualmente selecionado.

**Descrição:** Get Selected Character

**Autenticação:** Requerida 🔒

### POST /api/characters/{character_id}/select
Selecionar um personagem específico.

**Descrição:** Select Character

**Parâmetros:**
- `character_id` - ID do personagem

**Autenticação:** Requerida 🔒

### GET /api/characters/{character_id}
Obter detalhes de um personagem específico.

**Descrição:** Get Character

**Parâmetros:**
- `character_id` - ID do personagem

**Autenticação:** Requerida 🔒

### PUT /api/characters/{character_id}
Atualizar dados de um personagem.

**Descrição:** Update Character

**Parâmetros:**
- `character_id` - ID do personagem

**Autenticação:** Requerida 🔒

### DELETE /api/characters/{character_id}
Deletar um personagem.

**Descrição:** Delete Character

**Parâmetros:**
- `character_id` - ID do personagem

**Autenticação:** Requerida 🔒

### GET /api/characters/{character_id}/inventory
Buscar o inventário de um personagem.

**Descrição:** Buscar inventário

**Parâmetros:**
- `character_id` - ID do personagem

**Autenticação:** Requerida 🔒

### POST /api/characters/{character_id}/inventory/{item_id}/use
Usar um item do inventário.

**Descrição:** Use Item

**Parâmetros:**
- `character_id` - ID do personagem
- `item_id` - ID do item

**Autenticação:** Requerida 🔒

---

## Campaigns

Endpoints para gerenciamento de campanhas.

### GET /api/campaigns/
Listar todas as campanhas.

**Descrição:** Get Campaigns

**Autenticação:** Requerida 🔒

### POST /api/campaigns/
Criar uma nova campanha.

**Descrição:** Create Campaign

**Autenticação:** Requerida 🔒

### GET /api/campaigns/active/status
Obter status da campanha ativa.

**Descrição:** Get Active Campaign Status

**Autenticação:** Requerida 🔒

### GET /api/campaigns/{campaign_id}
Obter detalhes de uma campanha específica.

**Descrição:** Get Campaign

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### PUT /api/campaigns/{campaign_id}
Atualizar dados de uma campanha.

**Descrição:** Update Campaign

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### POST /api/campaigns/start
Iniciar uma campanha.

**Descrição:** Start Campaign

**Autenticação:** Requerida 🔒

### DELETE /api/campaigns/{campaign_id}/cancel
Cancelar uma campanha.

**Descrição:** Cancel Campaign

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### PUT /api/campaigns/{campaign_id}/complete-chapter
Completar um capítulo da campanha.

**Descrição:** Complete Chapter

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### POST /api/campaigns/seed
Criar campanhas de exemplo (seed).

**Descrição:** Seed Campaigns

**Autenticação:** Requerida 🔒

---

## LLM

Endpoints relacionados ao Large Language Model e narrativas.

### POST /api/llm/chat
Interagir com o LLM com progressão de história.

**Descrição:** Chat com LLM com progressão

**Autenticação:** Requerida 🔒

### POST /api/llm/reset-progression
Resetar a progressão do capítulo atual.

**Descrição:** Resetar progressão do capítulo

**Autenticação:** Requerida 🔒

### POST /api/llm/character-suggestion
Obter sugestões de personagens do LLM.

**Descrição:** Sugestão de personagem

### GET /api/llm/health
Verificar status de saúde do serviço LLM.

**Descrição:** Health check da LLM

### GET /api/llm/chroma/health
Verificar status de saúde do ChromaDB.

**Descrição:** Health check do ChromaDB

### GET /api/llm/chroma/campaign/{campaign_id}/history
Obter histórico de narrativas de uma campanha.

**Descrição:** Histórico de narrativas da campanha

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### GET /api/llm/chroma/campaign/{campaign_id}/chapter/{chapter}/summary
Obter resumo de um capítulo específico.

**Descrição:** Resumo do capítulo

**Parâmetros:**
- `campaign_id` - ID da campanha
- `chapter` - Número do capítulo

**Autenticação:** Requerida 🔒

### POST /api/llm/chroma/search
Buscar narrativas por similaridade vetorial.

**Descrição:** Busca vetorial de narrativas

**Autenticação:** Requerida 🔒

### DELETE /api/llm/chroma/campaign/{campaign_id}
Deletar todas as narrativas de uma campanha.

**Descrição:** Deletar narrativas da campanha

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

### GET /api/llm/chroma/campaign/{campaign_id}/full-context
Obter contexto completo da campanha para retomada.

**Descrição:** Contexto completo da campanha para retomada

**Parâmetros:**
- `campaign_id` - ID da campanha

**Autenticação:** Requerida 🔒

---

## Infra

Endpoints de infraestrutura e monitoramento.

### GET /health
Verificar status de saúde geral da API.

**Descrição:** Health

---

## Autenticação

Endpoints que exibem o ícone de cadeado (🔒) requerem autenticação via token JWT no header:

```
Authorization: Bearer {seu-token-jwt}
```

## Códigos de Status HTTP

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Requisição inválida
- `401` - Não autenticado
- `403` - Não autorizado
- `404` - Recurso não encontrado
- `500` - Erro interno do servidor