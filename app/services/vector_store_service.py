import logging
import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import os

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Serviço para gerenciar narrativas no ChromaDB"""
    
    def __init__(self):
        try:
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            

            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            self.narratives_collection = self.client.get_or_create_collection(
                name="narratives",
                metadata={"description": "Narrativas geradas pelo LLM no RPG Chromance"}
            )
            
            logger.info("ChromaDB inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {e}")
            raise
    
    def store_narrative(
        self,
        narrative_text: str,
        campaign_id: str,
        character_id: str,
        user_id: str,
        interaction_count: int,
        chapter: int,
        phase: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Armazena uma narrativa no ChromaDB"""
        try:
            doc_id = self._generate_document_id(
                campaign_id, character_id, interaction_count
            )
            
            doc_metadata = {
                "campaign_id": str(campaign_id),
                "character_id": str(character_id),
                "user_id": str(user_id),
                "interaction_count": int(interaction_count),
                "chapter": int(chapter),
                "phase": phase,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }

            self.narratives_collection.add(
                documents=[narrative_text],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Narrativa armazenada no ChromaDB: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Erro ao armazenar narrativa: {e}")
            return ""
    
    def search_similar_narratives(
        self,
        query_text: str,
        campaign_id: Optional[str] = None,
        chapter: Optional[int] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca narrativas similares usando busca vetorial"""
        try:
            where_filter = {}
            if campaign_id:
                where_filter["campaign_id"] = str(campaign_id)
            if chapter:
                where_filter["chapter"] = int(chapter)
            
            results = self.narratives_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            formatted_results = []
            if results.get('documents') and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "narrative": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Busca vetorial retornou {len(formatted_results)} resultados")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return []
    
    def get_campaign_history(
        self,
        campaign_id: str,
        chapter: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Recupera histórico de narrativas de uma campanha"""
        try:
            where_filter = {"campaign_id": str(campaign_id)}
            if chapter:
                where_filter["chapter"] = int(chapter)
            
            results = self.narratives_collection.get(
                where=where_filter,
                limit=limit
            )
            
            history = []
            if results.get('documents'):
                for i, doc in enumerate(results['documents']):
                    history.append({
                        "id": results['ids'][i],
                        "narrative": doc,
                        "metadata": results['metadatas'][i]
                    })

            history.sort(
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=False
            )
            
            logger.info(f"Histórico recuperado: {len(history)} narrativas")
            return history
            
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return []
    
    def get_chapter_summary(
        self,
        campaign_id: str,
        chapter: int
    ) -> Dict[str, Any]:
        """Retorna resumo de um capítulo específico"""
        try:
            chapter_narratives = self.get_campaign_history(
                campaign_id=campaign_id,
                chapter=chapter,
                limit=100
            )
            
            if not chapter_narratives:
                return {
                    "chapter": chapter,
                    "total_interactions": 0,
                    "phases": {},
                    "narratives": []
                }
            
            phases = {}
            for narrative in chapter_narratives:
                phase = narrative['metadata'].get('phase', 'unknown')
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(narrative)
            
            return {
                "chapter": chapter,
                "total_interactions": len(chapter_narratives),
                "phases": {phase: len(narrs) for phase, narrs in phases.items()},
                "narratives": chapter_narratives
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo do capítulo: {e}")
            return {}
    
    def delete_campaign_narratives(self, campaign_id: str) -> bool:
        """Remove todas as narrativas de uma campanha"""
        try:
            results = self.narratives_collection.get(
                where={"campaign_id": str(campaign_id)}
            )
            
            if results.get('ids'):
                self.narratives_collection.delete(ids=results['ids'])
                logger.info(f"Removidas {len(results['ids'])} narrativas da campanha {campaign_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar narrativas: {e}")
            return False
    
    def _generate_document_id(
        self,
        campaign_id: str,
        character_id: str,
        interaction_count: int
    ) -> str:
        """Gera ID único para o documento"""
        base_string = f"{campaign_id}_{character_id}_{interaction_count}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do ChromaDB"""
        try:
            count = self.narratives_collection.count()
            return {
                "status": "healthy",
                "total_narratives": count,
                "collection": "narratives"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }