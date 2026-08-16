from functools import lru_cache
from pathlib import Path
from contextlib import asynccontextmanager
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from app.core.config import settings
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI
import warnings
from app.prompts.instructions import SYSTEM_PROMPT

warnings.filterwarnings("ignore", category=DeprecationWarning)

def load_documents() -> list[Document]:
    """Reads all Markdown files from settings.DATA_PATH as LangChain Document objects."""
    documents = []
    data_path = Path(settings.DATA_PATH)

    for file_path in data_path.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            documents.append(
                Document(
                    page_content=content,
                    metadata={"source": str(file_path), "filename": file_path.name}
                )
            )
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return documents

def create_chunks(documents: list[Document]) -> list[Document]:
    """Splits Document objects into chunked Document objects with preserved metadata."""
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    # Automatically splits content and carries over metadata (e.g., source)
    return text_splitter.split_documents(documents)

@lru_cache
def get_embedding_model():
    return FastEmbedEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )

"""
Ce module charge le modèle d'embeddings local FastEmbed et gère l'injection
automatique des chunks de documents (avec leurs métadonnées) dans la base
de données vectorielle Qdrant Cloud.
"""
def index_chunks_in_qdrant(chunks: list[Document]) -> QdrantVectorStore:
    """Vectorise une liste de chunks et les stocke dans Qdrant Cloud.

    Cette fonction instancie le modèle d'embeddings FastEmbed, convertit le contenu
    textuel de chaque document en vecteur numérique, puis envoie le tout
    (vecteurs + contenu + métadonnées de source) vers la collection Qdrant configurée.

  """
    # 1. Initialisation du modèle d'embeddings léger FastEmbed (exécution CPU en local, 0 FCFA)
    embedding_model = get_embedding_model()

    # 2. Vectorisation et ingestion dans Qdrant Cloud
    # - Inférence locale des vecteurs via FastEmbed
    # - Association automatique des métadonnées (source, filename, etc.)
    # - Envoi réseau optimisé par lots (batching) vers Qdrant
    vector_store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )

    # 3. Retourne le Vector Store prêt pour le Retriever (Phase 2 du RAG)
    return vector_store

def search_documents(vector_store: QdrantVectorStore, question: str):
    # Récupère un pool plus large pour filtrer les doublons
    results = vector_store.similarity_search_with_score(
        question,
        k=settings.TOP_K_RESULTS * 3
    )

    filtered_results = []
    seen_contents = set()

    for doc, score in results:
        # Nettoyage des espaces pour bien comparer les contenus
        cleaned_content = doc.page_content.strip()
        
        if score >= settings.MIN_RELEVANCE_SCORE and cleaned_content not in seen_contents:
            filtered_results.append((doc, score))
            seen_contents.add(cleaned_content)
            
            if len(filtered_results) == settings.TOP_K_RESULTS:
                break

    return filtered_results


   



def generate_answer(
    question: str, retrieved_docs: list[tuple[Document, float]]
) -> str:
    """
    Génère la réponse avec le LLM Principal (Groq - Llama 3.2 Vision).
    En cas de saturation (Rate Limit 429), bascule sur le LLM de Secours (Hugging Face).
    """
    # 1. Mise en forme du contexte récupéré
    if retrieved_docs:
        context = "\n\n---\n\n".join(
            [
                f"Source: {doc.metadata.get('filename', 'Inconnu')}\n{doc.page_content}"
                for doc, _ in retrieved_docs
            ]
        )
    else:
        context = "Aucune information pertinente trouvée dans la base de connaissances."

    # 2. Construction du template de prompt
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT + "\n\n# CONTEXTE RAG FOURNI :\n{context}"),
            ("human", "{question}"),
        ]
    )

    # 3. Exécution : Groq (Principal) -> Fallback Hugging Face (Secours)
    try:
        print("⚡ Envoi de la requête au LLM Principal (Groq)...")
        llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
        )
        chain = prompt_template | llm
        response = chain.invoke({"context": context, "question": question})
        return response.content

    except Exception as e:
        print(f" Erreur Groq ({e}). Bascule sur le LLM de secours (Hugging Face)...")
        try:
            llm_endpoint = HuggingFaceEndpoint(
                repo_id=settings.HF_MODEL,
                huggingfacehub_api_token=settings.HF_API_KEY,
                temperature=settings.GROQ_TEMPERATURE,
                max_new_tokens=settings.GROQ_MAX_TOKENS,
            )
            fallback_llm = ChatHuggingFace(llm=llm_endpoint)
            chain = prompt_template | fallback_llm
            response = chain.invoke({"context": context, "question": question})
            return response.content
        except Exception as fallback_err:
            return f"Service temporairement indisponible. Erreur : {fallback_err}"


# ---------------------------------------------------------------------------
# Point d'entrée FastAPI
# ---------------------------------------------------------------------------

# Stockage global du vector_store initialisé au démarrage
_vector_store: QdrantVectorStore | None = None


def get_vector_store() -> QdrantVectorStore:
    """Retourne le vector store initialisé au démarrage de l'app."""
    if _vector_store is None:
        raise RuntimeError("Le vector store n'est pas encore initialisé.")
    return _vector_store


def connect_to_qdrant() -> QdrantVectorStore:
    """
    Se connecte à la collection Qdrant existante sans réinsérer les données.
    À utiliser au démarrage de l'app quand les données sont déjà indexées.
    """
    embedding_model = get_embedding_model()
    return QdrantVectorStore.from_existing_collection(
        embedding=embedding_model,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION_NAME,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connexion au vector store Qdrant existant au démarrage."""
    global _vector_store
    print("Démarrage : connexion à la collection Qdrant existante...")
    _vector_store = connect_to_qdrant()
    print("Vector store prêt.")
    yield
    print("Arrêt de l'application.")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)

# Montage du routeur securite_ia (validation, rate limit, filtrage, chat sécurisé)
from securite_ia import routeur  # noqa: E402
app.include_router(routeur)

# Montage du routeur chatbot_ia (endpoint /api/chatbot/message/)
from chatbot_ia import routeur as routeur_chatbot  # noqa: E402
app.include_router(routeur_chatbot)


@app.get("/health", tags=["Santé"])
def health_check():
    """Vérifie que l'API est opérationnelle."""
    return {"status": "ok", "service": settings.API_TITLE}
