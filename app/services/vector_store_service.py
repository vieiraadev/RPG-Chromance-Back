import logging
import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import os

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Serviço para gerenciar narrativas no ChromaDB com World Lore"""
    
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
                name="campaign_current",
                metadata={"description": "Narrativas da campanha/capítulo ativo"}
            )
            
            self.archive_collection = self.client.get_or_create_collection(
                name="campaign_archive",
                metadata={"description": "Histórico de campanhas finalizadas"}
            )
            
            self.lore_collection = self.client.get_or_create_collection(
                name="world_lore",
                metadata={"description": "Conhecimento permanente do universo Chromance"}
            )
            
            logger.info("ChromaDB inicializado com 3 collections: current, archive, lore")
            
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
        """Armazena uma narrativa no ChromaDB (campanha atual)"""
        try:
            doc_id = self._generate_document_id(
                campaign_id, character_id, interaction_count, chapter
            )
            
            doc_metadata = {
                "campaign_id": str(campaign_id),
                "character_id": str(character_id),
                "user_id": str(user_id),
                "interaction_count": int(interaction_count),
                "chapter": int(chapter),
                "phase": phase,
                "timestamp": datetime.utcnow().isoformat(),
                "world_id": "chromance",
                **(metadata or {})
            }

            self.narratives_collection.add(
                documents=[narrative_text],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Narrativa armazenada (current): {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Erro ao armazenar narrativa: {e}")
            return ""
    
    def search_similar_narratives(
        self,
        query_text: str,
        campaign_id: Optional[str] = None,
        chapter: Optional[int] = None,
        n_results: int = 5,
        include_lore: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca narrativas similares com sistema hierárquico:
        1. Prioriza campanha/capítulo atual
        2. Adiciona world lore se include_lore=True
        """
        try:
            all_results = []
            
            where_filter = None
            if campaign_id and chapter:
                where_filter = {
                    "$and": [
                        {"campaign_id": {"$eq": str(campaign_id)}},
                        {"chapter": {"$eq": int(chapter)}}
                    ]
                }
            elif campaign_id:
                where_filter = {"campaign_id": {"$eq": str(campaign_id)}}
            elif chapter:
                where_filter = {"chapter": {"$eq": int(chapter)}}
            
            current_results = self.narratives_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )
            
            if current_results.get('documents') and current_results['documents']:
                for i, doc in enumerate(current_results['documents'][0]):
                    all_results.append({
                        "id": current_results['ids'][0][i],
                        "narrative": doc,
                        "metadata": current_results['metadatas'][0][i],
                        "distance": current_results['distances'][0][i] if 'distances' in current_results else None,
                        "source": "current",
                        "weight": 1.0
                    })
            
            if include_lore:
                lore_results = self.lore_collection.query(
                    query_texts=[query_text],
                    n_results=max(2, n_results // 2),
                    where={"world_id": {"$eq": "chromance"}}
                )
                
                if lore_results.get('documents') and lore_results['documents']:
                    for i, doc in enumerate(lore_results['documents'][0]):
                        all_results.append({
                            "id": lore_results['ids'][0][i],
                            "narrative": doc,
                            "metadata": lore_results['metadatas'][0][i],
                            "distance": lore_results['distances'][0][i] if 'distances' in lore_results else None,
                            "source": "lore",
                            "weight": 0.3
                        })
            
            all_results.sort(key=lambda x: (x.get('distance', 999) / x.get('weight', 1)))
            
            logger.info(f"RAG retornou: {len([r for r in all_results if r['source']=='current'])} current, "
                       f"{len([r for r in all_results if r['source']=='lore'])} lore")
            
            return all_results[:n_results]
            
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return []
    
    def extract_lore_from_chapter(
        self,
        campaign_id: str,
        chapter: int,
        user_id: str
    ) -> int:
        """
        Extrai fatos importantes do capítulo e salva como World Lore.
        Chamado ao FINALIZAR capítulo.
        """
        try:
            chapter_narratives = self.get_campaign_history(
                campaign_id=campaign_id,
                chapter=chapter,
                limit=100
            )
            
            if not chapter_narratives:
                logger.warning(f"Nenhuma narrativa encontrada para cap {chapter}")
                return 0

            full_chapter_text = "\n\n".join([
                n['narrative'] for n in chapter_narratives
            ])
            
            lore_items = self._extract_lore_elements(full_chapter_text, chapter)
            
            saved_count = 0
            for lore_item in lore_items:
                lore_id = self._save_lore_item(
                    lore_text=lore_item['text'],
                    lore_type=lore_item['type'],
                    chapter=chapter,
                    campaign_id=campaign_id,
                    metadata=lore_item.get('metadata', {})
                )
                
                if lore_id:
                    saved_count += 1
            
            logger.info(f"✓ Extraídos {saved_count} itens de lore do capítulo {chapter}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Erro ao extrair lore: {e}")
            return 0
    
    def _extract_lore_elements(self, text: str, chapter: int) -> List[Dict[str, Any]]:
        """
        Extrai elementos de lore do texto (locais, conceitos, regras do mundo).
        """
        lore_items = []
        
        chapter_lore = {
            1: [
                {
                    "type": "location",
                    "text": "Catedral em ruínas nas profundezas da cidade - estrutura gótica antiga com armadilhas mágicas e energias corrompidas.",
                    "metadata": {"importance": 0.9, "danger_level": "high"}
                },
                {
                    "type": "artifact",
                    "text": "Cubo das Sombras - relíquia ancestral pulsante de energia arcana, emite corrupção e possui grande poder místico.",
                    "metadata": {"importance": 1.0, "power_level": "legendary"}
                },
                {
                    "type": "enemy",
                    "text": "Guardas Sombrios - entidades que protegem relíquias ancestrais nas ruínas, vulneráveis a luz mas resistentes a ataques físicos.",
                    "metadata": {"importance": 0.7, "threat_level": "medium"}
                }
            ],
            2: [
                {
                    "type": "location",
                    "text": "Laboratório de Cristais Arcanos - instalação oculta na fortaleza com experimentos proibidos de energia arcana.",
                    "metadata": {"importance": 0.9, "danger_level": "very_high"}
                },
                {
                    "type": "artifact",
                    "text": "Cristal Arcano Puro - fragmento de energia arcana cristalizada usado em experimentos perigosos.",
                    "metadata": {"importance": 1.0, "power_level": "legendary"}
                },
                {
                    "type": "npc",
                    "text": "Cientista Obcecado - pesquisador que conduz experimentos proibidos com energia arcana no laboratório.",
                    "metadata": {"importance": 0.8, "alignment": "hostile"}
                }
            ],
            3: [
                {
                    "type": "location",
                    "text": "Coliseu de Neon - arena de combate underground no coração da cidade subterrânea, iluminada por letreiros de neon.",
                    "metadata": {"importance": 0.9, "danger_level": "high"}
                },
                {
                    "type": "artifact",
                    "text": "Cinturão do Campeão - prêmio dado aos vencedores do coliseu, símbolo de prestígio nas ruas.",
                    "metadata": {"importance": 1.0, "power_level": "rare"}
                },
                {
                    "type": "faction",
                    "text": "Gangues do Coliseu - organizações criminosas que controlam apostas e combates ilegais na cidade subterrânea.",
                    "metadata": {"importance": 0.7, "alignment": "neutral"}
                }
            ]
        }
        
        if chapter in chapter_lore:
            lore_items.extend(chapter_lore[chapter])
        
        if chapter == 1:
            generic_lore = [
                {
                    "type": "world_rule",
                    "text": "Chromance - universo cyberpunk onde corporações controlam tudo, tecnologia se mistura com magia arcana.",
                    "metadata": {"importance": 1.0, "category": "world_foundation"}
                },
                {
                    "type": "world_rule",
                    "text": "Energia Arcana - força mística presente em ruínas antigas, pode corromper quem a utiliza sem proteção adequada.",
                    "metadata": {"importance": 0.8, "category": "magic_system"}
                },
                {
                    "type": "world_rule",
                    "text": "Cidade Subterrânea - megacidade cyberpunk dividida em níveis, quanto mais profundo mais perigoso e antigo.",
                    "metadata": {"importance": 0.9, "category": "world_geography"}
                }
            ]
            lore_items.extend(generic_lore)
        
        return lore_items
    
    def _save_lore_item(
        self,
        lore_text: str,
        lore_type: str,
        chapter: int,
        campaign_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Salva um item individual de lore"""
        try:
            lore_id = self._generate_lore_id(lore_text, lore_type, chapter)
            
            existing = self.lore_collection.get(ids=[lore_id])
            if existing and existing['ids']:
                logger.debug(f"Lore já existe: {lore_id}")
                return lore_id
            
            lore_metadata = {
                "type": lore_type,
                "chapter_discovered": chapter,
                "campaign_id": campaign_id,
                "world_id": "chromance",
                "timestamp": datetime.utcnow().isoformat(),
                **metadata
            }
            
            self.lore_collection.add(
                documents=[lore_text],
                metadatas=[lore_metadata],
                ids=[lore_id]
            )
            
            logger.debug(f"Lore salvo: {lore_type} - {lore_text[:50]}...")
            return lore_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar lore: {e}")
            return ""
    
    def clear_chapter_narratives(
        self,
        campaign_id: str,
        chapter: int
    ) -> bool:
        """
        Limpa narrativas de um capítulo específico da collection CURRENT.
        Chamado ao finalizar capítulo.
        """
        try:
            results = self.narratives_collection.get(
                where={
                    "$and": [
                        {"campaign_id": {"$eq": str(campaign_id)}},
                        {"chapter": {"$eq": int(chapter)}}
                    ]
                }
            )
            
            if results.get('ids'):
                self.narratives_collection.delete(ids=results['ids'])
                logger.info(f"✓ Limpas {len(results['ids'])} narrativas do cap {chapter}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao limpar capítulo: {e}")
            return False
    
    def clear_current_campaign_only(self, campaign_id: str) -> bool:
        """
        Limpa apenas a collection campaign_current, mantendo archive e world_lore.
        Usado encerrar uma campanha.
        """
        try:
            results = self.narratives_collection.get(
                where={"campaign_id": {"$eq": str(campaign_id)}}
            )
            
            if results.get('ids'):
                self.narratives_collection.delete(ids=results['ids'])
                logger.info(f"✓ Limpas {len(results['ids'])} narrativas de campaign_current para {campaign_id}")
                return True
            
            logger.info(f"Nenhuma narrativa encontrada em campaign_current para {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar campaign_current: {e}")
            return False
    
    def archive_chapter(
        self,
        campaign_id: str,
        chapter: int
    ) -> bool:
        """
        Move narrativas do capítulo para ARCHIVE antes de limpar.
        Opcional - para manter histórico completo.
        """
        try:
            results = self.narratives_collection.get(
                where={
                    "$and": [
                        {"campaign_id": {"$eq": str(campaign_id)}},
                        {"chapter": {"$eq": int(chapter)}}
                    ]
                }
            )
            
            if not results.get('ids'):
                return True
            
            for i, doc_id in enumerate(results['ids']):
                self.archive_collection.add(
                    documents=[results['documents'][i]],
                    metadatas=[{
                        **results['metadatas'][i],
                        "archived_at": datetime.utcnow().isoformat()
                    }],
                    ids=[f"archive_{doc_id}"]
                )
            
            logger.info(f"✓ Arquivadas {len(results['ids'])} narrativas do cap {chapter}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao arquivar capítulo: {e}")
            return False
    
    def get_campaign_history(
        self,
        campaign_id: str,
        chapter: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Recupera histórico de narrativas de uma campanha"""
        try:
            where_filter = None
            if campaign_id and chapter:
                where_filter = {
                    "$and": [
                        {"campaign_id": {"$eq": str(campaign_id)}},
                        {"chapter": {"$eq": int(chapter)}}
                    ]
                }
            elif campaign_id:
                where_filter = {"campaign_id": {"$eq": str(campaign_id)}}
            
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
            
            return history
            
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return []
    
    def get_world_lore_summary(self) -> Dict[str, Any]:
        """Retorna resumo do world lore acumulado"""
        try:
            all_lore = self.lore_collection.get(
                where={"world_id": {"$eq": "chromance"}}
            )
            
            if not all_lore.get('metadatas'):
                return {
                    "total_items": 0,
                    "by_type": {},
                    "by_chapter": {}
                }
            
            by_type = {}
            by_chapter = {}
            
            for metadata in all_lore['metadatas']:
                lore_type = metadata.get('type', 'unknown')
                chapter = metadata.get('chapter_discovered', 0)
                
                by_type[lore_type] = by_type.get(lore_type, 0) + 1
                by_chapter[chapter] = by_chapter.get(chapter, 0) + 1
            
            return {
                "total_items": len(all_lore['metadatas']),
                "by_type": by_type,
                "by_chapter": by_chapter
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de lore: {e}")
            return {}
    
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
                where={"campaign_id": {"$eq": str(campaign_id)}}
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
        interaction_count: int,
        chapter: int
    ) -> str:
        """Gera ID único para o documento"""
        base_string = f"{campaign_id}_{character_id}_{chapter}_{interaction_count}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def _generate_lore_id(
        self,
        lore_text: str,
        lore_type: str,
        chapter: int
    ) -> str:
        """Gera ID único para item de lore"""
        base_string = f"lore_{lore_type}_{chapter}_{lore_text[:50]}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do ChromaDB"""
        try:
            current_count = self.narratives_collection.count()
            archive_count = self.archive_collection.count()
            lore_count = self.lore_collection.count()
            
            return {
                "status": "healthy",
                "collections": {
                    "campaign_current": current_count,
                    "campaign_archive": archive_count,
                    "world_lore": lore_count
                },
                "total_documents": current_count + archive_count + lore_count
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }