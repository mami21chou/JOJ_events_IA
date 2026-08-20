from fastapi import APIRouter, HTTPException, status

from .schemas import MessageEntrant, ReponseChat
from .contexte import ajouter_message, obtenir_historique, effacer_session
from .service_ia import appeler_ia
from .journal import journaliser

routeur = APIRouter(prefix="/api/chatbot", tags=["Chatbot IA"])


@routeur.post("/message/", response_model=ReponseChat)
async def envoyer_message(entrant: MessageEntrant):
    """Flux complet : question → contexte → IA → réponse."""

    # 1. Récupère l'historique de la session
    historique = obtenir_historique(entrant.session_id)

    # 2. Appel au service IA
    reponse, fallback = await appeler_ia(entrant.message, historique)

    # 3. Sauvegarde dans le contexte
    ajouter_message(entrant.session_id, "user", entrant.message)
    ajouter_message(entrant.session_id, "assistant", reponse)

    # 4. Log de l'interaction
    journaliser(entrant.utilisateur_id, entrant.session_id, entrant.message, reponse, fallback)

    return ReponseChat(session_id=entrant.session_id, reponse=reponse, fallback=fallback)


@routeur.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def effacer_contexte(session_id: str):
    """Supprime l'historique d'une session."""
    effacer_session(session_id)
