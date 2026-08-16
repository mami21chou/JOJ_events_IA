from pydantic import BaseModel, Field


class RequeteChat(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    utilisateur_id: str = Field(..., min_length=1, max_length=100)


class ReponseValidation(BaseModel):
    valide: bool
    raison: str | None = None


class ReponseChat(BaseModel):
    reponse: str
    filtre: bool = False
