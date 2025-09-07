"""
Script para popular o banco de dados com as campanhas dos capítulos 1, 2 e 3
Uso: python scripts/seed_campaigns.py
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_database


def main():
    print("RPG Chromance - Seed de Campanhas")
    print("=" * 50)
    
    db = get_database()
    campaigns_collection = db["campaigns"]
    
    print("\n ATENÇÃO: Este script irá:")
    print("  1. REMOVER todas as campanhas existentes")
    print("  2. Adicionar as campanhas dos capítulos 1, 2 e 3")
    
    response = input("\nDeseja continuar? (s/N): ")
    
    if response.lower() != 's':
        print("Operação cancelada")
        return 1
    
    print("\nPopulando banco de dados...")
    
    try:
        campaigns_collection.delete_many({})
        
        campaigns_data = [
            {
                "campaign_id": "arena-sombras",
                "title": "Capítulo 1 : O Cubo das Sombras",
                "chapter": 1,
                "description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral.",
                "full_description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral. Para conquistá-lo, deve enfrentar as armadilhas ocultas que protegem seu poder e resistir à corrupção que emana da própria relíquia. Cada passo ecoa no salão silencioso, enquanto a luz azul da espada e do artefato guia seu caminho através da escuridão. O destino do mundo depende de sua escolha: dominar o cubo ou ser consumido por ele.",
                "image": "./assets/images/campaign-thumb1.jpg",
                "thumbnail": "./assets/images/campaign-thumb1.jpg",
                "rewards": [
                    {"type": "weapon", "name": "Lâmina Cybernética", "icon": "sword"},
                    {"type": "armor", "name": "Escudo Neural", "icon": "shield"},
                    {"type": "health", "name": "Vida +100", "icon": "heart"},
                    {"type": "tech", "name": "Chip de Combate", "icon": "chip"}
                ],
                "is_locked": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "campaign_id": "laboratorio-cristais",
                "title": "Capítulo 2 : Laboratório de Cristais Arcanos",
                "chapter": 2,
                "description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas com fragmentos de energia arcana.",
                "full_description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas com fragmentos de energia arcana. Sua última criação gerou uma reação instável, transformando o local em um campo de chamas e caos. O jogador deve atravessar o laboratório em colapso, evitando explosões e defendendo-se das máquinas de defesa ativadas pelo surto de energia.",
                "image": "./assets/images/campaign-thumb2.jpg",
                "thumbnail": "./assets/images/campaign-thumb2.jpg",
                "rewards": [
                    {"type": "weapon", "name": "Bastão Arcano", "icon": "sword"},
                    {"type": "armor", "name": "Manto de Cristal", "icon": "shield"},
                    {"type": "health", "name": "Poção Vital", "icon": "heart"},
                    {"type": "tech", "name": "Cristal Energético", "icon": "chip"}
                ],
                "is_locked": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "campaign_id": "coliseu-de-neon",
                "title": "Capítulo 3 : Coliseu de Neon",
                "chapter": 3,
                "description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes e iluminado apenas por letreiros de neon.",
                "full_description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes e iluminado apenas por letreiros de neon, ocorre o torneio clandestino mais brutal do submundo. Aqui, guerreiros e máquinas se enfrentam em lutas sangrentas, enquanto a multidão mascarada assiste em êxtase.",
                "image": "./assets/images/campaign-image3.jpg",
                "thumbnail": "./assets/images/campaign-image3.jpg",
                "rewards": [
                    {"type": "weapon", "name": "Cetro do Caos", "icon": "sword"},
                    {"type": "armor", "name": "Armadura Prismática", "icon": "shield"},
                    {"type": "health", "name": "Elixir da Vida", "icon": "heart"},
                    {"type": "tech", "name": "Núcleo de Energia", "icon": "chip"}
                ],
                "is_locked": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        result = campaigns_collection.insert_many(campaigns_data)
        
        print("\nSucesso! Campanhas criadas:")
        print("-" * 50)
        
        for campaign in campaigns_data:
            print(f"  📖 {campaign['title']}")
            print(f"     ID: {campaign['campaign_id']}")
            print()
        
        print(f"Total de campanhas criadas: {len(result.inserted_ids)}")
        
    except Exception as e:
        print(f"\nErro ao popular banco: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)