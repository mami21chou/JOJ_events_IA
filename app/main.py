from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.rag.main_rag import (
    load_documents,
    create_chunks,
    index_chunks_in_qdrant,
    search_documents,
    generate_answer,
)


# ============================================================
# VARIABLES GLOBALES
# ============================================================

vector_store = None


# ============================================================
# INITIALISATION DU RAG
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialise la base vectorielle au démarrage de l'API.
    """

    global vector_store

    print("========================================")
    print(" Démarrage de l'API JOJ Events IA")
    print("========================================")

    try:
        print("📚 Chargement des documents...")
        documents = load_documents()

        print(f"📄 Documents trouvés : {len(documents)}")

        print("✂️ Création des chunks...")
        chunks = create_chunks(documents)

        print(f"🧩 Chunks créés : {len(chunks)}")

        print("🔎 Initialisation de Qdrant...")
        vector_store = index_chunks_in_qdrant(chunks)

        print("✅ Base vectorielle initialisée")
        print("🚀 API JOJ Events IA prête")

    except Exception as erreur:
        print("❌ Erreur lors de l'initialisation du RAG")
        print(erreur)

    yield

    print("🛑 Arrêt de l'API JOJ Events IA")


# ============================================================
# APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="API JOJ Events IA",
    description="Assistant IA RAG pour les JOJ Dakar 2026",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELES
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Question de l'utilisateur",
    )

    historique: list[dict] = Field(
        default_factory=list,
        description="Historique de la conversation",
    )


class ChatResponse(BaseModel):
    reponse: str


# ============================================================
# ROUTE D'ACCUEIL
# ============================================================

@app.get("/")
def accueil():
    return {
        "message": "API JOJ Events IA opérationnelle",
        "documentation": "/docs",
    }


# ============================================================
# ROUTE DE SANTÉ
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "rag": vector_store is not None,
    }


# ============================================================
# CHATBOT
# ============================================================

@app.post("/api/chat/", response_model=ChatResponse)
def chat(request: ChatRequest):

    global vector_store

    # Vérifier que le RAG est disponible
    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="Le service RAG n'est pas encore disponible.",
        )

    try:
        print(f" Question reçue : {request.message}")

        # ----------------------------------------------------
        # 1. Recherche des documents pertinents
        # ----------------------------------------------------

        retrieved_docs = search_documents(
            vector_store,
            request.message,
        )

        print(
            f" Documents pertinents trouvés : "
            f"{len(retrieved_docs)}"
        )

        # ----------------------------------------------------
        # 2. Génération de la réponse
        # ----------------------------------------------------

        answer = generate_answer(
            request.message,
            retrieved_docs,
        )

        print(" Réponse générée")

        return {
            "reponse": answer
        }

    except Exception as erreur:

        print(" Erreur lors du traitement de la question")
        print(erreur)

        raise HTTPException(
            status_code=500,
            detail="Une erreur est survenue lors du traitement de votre question.",
        )