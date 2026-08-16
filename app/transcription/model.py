# Chargement du modèle
from transformers import pipeline


model = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-small",
    #Découpe l'audio en morceaux de 30 secondes avant de le donner à Whisper.
    chunk_length_s=30,
    device="cpu"
)