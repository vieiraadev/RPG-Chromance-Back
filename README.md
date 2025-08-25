# 🎮 RPG Chromance - Trainee Wise Systems

Sistema web interativo de RPG baseado em IA, integrando **Angular (front-end)**, **FastAPI (back-end)** e **MongoDB (banco de dados)**.  
O jogo utiliza **LLM** para gerar narrativas dinâmicas e estruturadas, permitindo que o usuário crie personagens, inicie campanhas e tome decisões livres ou sugeridas.

---

## ⚙️ Tecnologias
- **Front-end**: Angular 17+, SCSS, JWT Auth, consumo de API REST  
- **Back-end**: FastAPI, MongoDB, Pydantic, autenticação JWT  
- **IA/LLM**: geração de narrativa e ações, com respostas JSON estruturadas  
- **Infra**: Healthchecks (`/liveness`, `/readiness`, `/health`)  

---

## 🧑‍💻 Funcionalidades do Front-end (Angular)
- **Tela inicial**: Login, Cadastro ou Continuar campanha  
- **Login / Cadastro**: formulários + JWT integrado  
- **Gestão de Personagens**: criar, listar, excluir, iniciar campanha  
- **Tela de Jogo**:  
  - Mostra nome, classe, atributos e inventário  
  - Narrativa gerada pelo LLM  
  - Botões com ações sugeridas  
  - Campo de ação livre  
- **Histórico**: acompanhar campanhas anteriores  

---

## 📌 Organização do Projeto

O projeto segue a metodologia **Scrum**, organizada em **sprints semanais**, garantindo entregas incrementais e revisões contínuas.

A gestão das tarefas é realizada no **Trello**, onde os PBIs (Product Backlog Items) são divididos e acompanhados em cada sprint.  

As principais colunas do quadro no Trello são:

- **Product Backlog** → histórias e requisitos a serem desenvolvidos  
- **Sprint Backlog** → tarefas priorizadas para a sprint atual  
- **In Progress** → atividades em andamento  
- **Review/Testing** → itens concluídos aguardando validação  
- **Done** → funcionalidades finalizadas e entregues  

🔗 **Acesse o quadro no Trello:** ((https://trello.com/invite/b/68ab8e0ecfbf91119b5c6636/ATTIecabd367f91b8616aeaedd53cb544dfcAD69D16B/rpg-wise))  

