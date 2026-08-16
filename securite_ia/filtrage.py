import re

# Mots-clés du system prompt à ne jamais révéler
MOTS_CLES_SYSTEM = [
    "system prompt",
    "tu es un assistant",
    "you are an assistant",
    "instructions initiales",
    "consignes système",
]

# Contenu sensible à filtrer dans les sorties
CONTENU_SENSIBLE = [
    r"\b(mot de passe|password|secret|token|api.?key)\b",
    r"\b(confidentiel|interne|privé)\b",
]


def filtrer_sortie(reponse: str) -> tuple[str, bool]:
    """Filtre la réponse IA avant de la renvoyer à l'utilisateur."""
    filtre = False

    for mot in MOTS_CLES_SYSTEM:
        if mot.lower() in reponse.lower():
            reponse = "[Contenu masqué pour des raisons de sécurité]"
            return reponse, True

    for pattern in CONTENU_SENSIBLE:
        if re.search(pattern, reponse, re.IGNORECASE):
            reponse = re.sub(pattern, "***", reponse, flags=re.IGNORECASE)
            filtre = True

    return reponse, filtre
