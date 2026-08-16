from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os

from .service import transcrire_audio

routeur = APIRouter(
    prefix="/api/transcription",
    tags=["Transcription"]
)


@routeur.post("/")
async def transcrire(file: UploadFile = File(...)):

    # Vérifier que le fichier est bien un audio
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier audio."
        )

    # Créer un fichier temporaire
    suffix = os.path.splitext(file.filename or "")[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        contenu = await file.read()
        temp_file.write(contenu)
        chemin_audio = temp_file.name

    try:
        # Envoyer l'audio à Whisper
        texte = transcrire_audio(chemin_audio)

        return {
            "transcription": texte
        }

    finally:
        # Supprimer le fichier temporaire après traitement
        if os.path.exists(chemin_audio):
            os.remove(chemin_audio)