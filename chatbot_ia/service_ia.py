from langchain_core.documents import Document
from app.rag.main_rag import search_documents, generate_answer, get_vector_store

FALLBACK_MSG = "Je suis temporairement indisponible. Veuillez réessayer dans quelques instants."
TIMEOUT_SECONDES = 30


async def appeler_ia(message: str, historique: list[dict]) -> tuple[str, bool]:
    """
    Appelle directement le pipeline RAG interne (search + generate).
    Retourne (réponse, est_fallback).
    """
    try:
        vector_store = get_vector_store()
        retrieved_docs: list[tuple[Document, float]] = search_documents(vector_store, message)
        reponse = generate_answer(message, retrieved_docs)
        return reponse, False

    except RuntimeError:
        # Vector store pas encore initialisé
        return FALLBACK_MSG, True

    except Exception:
        return FALLBACK_MSG, True
