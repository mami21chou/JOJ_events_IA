from typing import List, Optional  #typing.List Indique qu'on a une liste de quelque chose
from fastembed import TextEmbedding # Bibliotheque qui cree  les embeddings en local
from app.core.config import settings # notre configuration
from functools import lru_cache

@lru_cache
def get_embedding_model():
    """Charge et met en cache le modèle d'embeddings"""
    print(f" Chargement du modèle : {settings.EMBEDDING_MODEL}")
    return TextEmbedding(model_name=settings.EMBEDDING_MODEL)





