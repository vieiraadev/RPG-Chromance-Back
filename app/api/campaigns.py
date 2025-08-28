from typing import List

from fastapi import APIRouter

from app.schemas.campaign import CampanhaCreate, CampanhaOut, HistoricoItem
from app.schemas.game import AcaoRequest, AcaoResponse

router = APIRouter(prefix="/api/campanha", tags=["Campanha"])


@router.post("", response_model=CampanhaOut, status_code=201, summary="Iniciar campanha")
async def iniciar_campanha(body: CampanhaCreate):
    return CampanhaOut(id="camp-1", personagem_id=body.personagem_id, titulo=body.titulo)


@router.get("/{id}", response_model=CampanhaOut, summary="Estado da campanha")
async def estado_campanha(id: str):
    return CampanhaOut(id=id, personagem_id="char-1", titulo="Contrato nas Ruas de Neon")


@router.delete("/{id}", status_code=204, summary="Encerrar campanha")
async def encerrar_campanha(id: str):
    return


@router.get("/{id}/historico", response_model=List[HistoricoItem], summary="Histórico da campanha")
async def listar_historico(id: str):
    return []


@router.post("/{id}/acao", response_model=AcaoResponse, summary="Enviar ação do jogador")
async def enviar_acao(id: str, body: AcaoRequest):
    return AcaoResponse(
        narrativa="Você entra no beco de néons; um drone patrulha acima…",
        acoesDisponiveis=["Atacar", "Hackear", "Conversar"],
        evento={
            "tipo": "combate",
            "inimigo": "Drone de Segurança",
            "danoRecebido": 2,
            "danoCausado": 8,
            "expGanha": 20,
        },
        estadoJogador={"vidaAtual": 98, "nivel": 1, "inventarioAtualizado": ["Pistola de Íons"]},
        proximaEtapa="Escolha sua próxima ação.",
    )
