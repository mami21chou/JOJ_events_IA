#fonction de transcription
from transcription.model import model

def Transcrire(chemin_audio):
    #donner l audio au model
    resultat=model(chemin_audio)
    return resultat['text']
    