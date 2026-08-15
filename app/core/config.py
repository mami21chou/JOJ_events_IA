from functools import lru_cache
import os
from typing import Optional  #Pour montreer qu'une valeur peut etre vide
from pydantic_settings import BaseSettings  #pour la validation: Créer une classe de configuration avec validation
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_TITLE: str= "JOJ Events - IA Service"
    API_DESCRIPTION: str = "Assistant Rag multimodal pour les JOJ Dakar 2026"

    # Groq (LLM Principal)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS"))

    # Hugging Face (Fallback) moteur de secours. Si Groq est saturé, on utilise HF
    HF_API_KEY: Optional[str] = os.getenv("HF_API_KEY")
    HF_MODEL: str = os.getenv("HF_MODEL")

    # Base de  donnees vectorielles
    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME")

    # transforme le texte en vecteurs
    
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL")

    


    # Rag
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP"))  
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS")) #Nombre de documents récupérés
    MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE")) #Score minimum de pertinence 

    #Securite
    MAX_QUESTION_LENGTH: int = int(os.getenv("MAX_QUESTION_LENGTH")) #Empêche les questions trop longues (attaque par déni de service).

    # Donnees
    DATA_PATH: str = os.getenv("DATA_PATH")

 #Créer une instance globale
@lru_cache
def get_settings():
    return Settings()

settings = get_settings()