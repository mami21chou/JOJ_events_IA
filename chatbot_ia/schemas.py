from pydantic import BaseModel, Field


class MessageEntrant(BaseModel):
    utilisateur_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)


class ReponseChat(BaseModel):
    session_id: str
    reponse: str
    fallback: bool = False


class MessageContexte(BaseModel):
    role: str   # "user" ou "assistant"
    contenu: str
