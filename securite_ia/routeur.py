from fastapi import APIRouter, HTTPException, status

from .schemas import RequeteChat, ReponseValidation, ReponseChat
from .detection import detecter_injection, detecter_hors_perimetre, sanitiser_entree
from .filtrage import filtrer_sortie
from .rate_limit import verifier_limite
from app.rag.main_rag import search_documents, generate_answer, get_vector_store

routeur = APIRouter(prefix="/securite-ia", tags=["Sécurité IA"])


@routeur.post("/valider-entree", response_model=ReponseValidation)
def valider_entree(requete: RequeteChat):
    """Valide et sanitise le message avant traitement IA."""
    message = sanitiser_entree(requete.message)

    injection, raison = detecter_injection(message)
    if injection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=raison)

    hors_perimetre, raison = detecter_hors_perimetre(message)
    if hors_perimetre:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=raison)

    return ReponseValidation(valide=True)


@routeur.post("/chat-securise", response_model=ReponseChat)
def chat_securise(requete: RequeteChat):
    """Point d'entrée sécurisé pour le chatbot JOJ."""

    # 1. Rate limiting
    autorise, erreur = verifier_limite(requete.utilisateur_id)
    if not autorise:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=erreur)

    # 2. Sanitisation
    message = sanitiser_entree(requete.message)

    # 3. Détection injection
    injection, raison = detecter_injection(message)
    if injection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=raison)

    # 4. Périmètre JOJ
    hors_perimetre, raison = detecter_hors_perimetre(message)
    if hors_perimetre:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=raison)

    # 5. Recherche RAG + génération de la réponse
    vector_store = get_vector_store()
    retrieved_docs = search_documents(vector_store, message)
    reponse_brute = generate_answer(message, retrieved_docs)

    # 6. Filtrage sortie
    reponse_finale, filtre = filtrer_sortie(reponse_brute)

    return ReponseChat(reponse=reponse_finale, filtre=filtre)


@routeur.post("/filtrer-sortie", response_model=ReponseChat)
def filtrer_reponse_ia(reponse: dict):
    """Filtre une réponse IA brute avant envoi à l'utilisateur."""
    texte = reponse.get("texte", "")
    if not texte:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Champ 'texte' manquant")

    reponse_finale, filtre = filtrer_sortie(texte)
    return ReponseChat(reponse=reponse_finale, filtre=filtre)


@routeur.get("/verifier-limite/{utilisateur_id}", response_model=ReponseValidation)
def verifier_rate_limit(utilisateur_id: str):
    """Vérifie si un utilisateur a atteint sa limite de requêtes."""
    autorise, erreur = verifier_limite(utilisateur_id)
    if not autorise:
        return ReponseValidation(valide=False, raison=erreur)
    return ReponseValidation(valide=True)
