from typing import List, Literal, Optional

from pydantic import BaseModel


class CampanhaCreate(BaseModel):
    personagem_id: str
    titulo: Optional[str] = "Contrato nas Ruas de Neon"


class CampanhaOut(BaseModel):
    id: str
    personagem_id: str
    status: Literal["ativa", "encerrada"] = "ativa"
    titulo: str


class HistoricoItem(BaseModel):
    id: str
    campanha_id: str
    role: Literal["jogador", "narrador", "sistema"]
    conteudo: str
    criadoEm: str
