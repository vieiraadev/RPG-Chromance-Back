from pydantic import BaseModel
from typing import List, Optional, Literal

class AcaoRequest(BaseModel):
    texto: str 

class Evento(BaseModel):
    tipo: Literal["combate","narrativa","loot"] = "narrativa"
    inimigo: Optional[str] = None
    danoRecebido: Optional[int] = 0
    danoCausado: Optional[int] = 0
    expGanha: Optional[int] = 0

class EstadoJogador(BaseModel):
    vidaAtual: int = 100
    nivel: int = 1
    inventarioAtualizado: List[str] = []

class AcaoResponse(BaseModel):
    narrativa: str
    acoesDisponiveis: List[str] = []
    evento: Evento = Evento()
    estadoJogador: EstadoJogador = EstadoJogador()
    proximaEtapa: Optional[str] = "Escolha sua próxima ação."
