import re

# Patterns typiques de prompt injection
PATTERNS_INJECTION = [
    r"ignore (previous|all|your) instructions",
    r"forget (everything|all|your|previous)",
    r"you are now",
    r"act as (a |an )?(?!joj)",  # autorise seulement JOJ
    r"disregard (your|all|previous)",
    r"system prompt",
    r"reveal (your|the) (prompt|instructions|system)",
    r"what (are|is) your (instructions|prompt|system)",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
]

# Sujets hors périmètre JOJ
HORS_PERIMETRE = [
    r"\bpolitique\b",
    r"\breligion\b",
    r"\bsexe\b",
    r"\bdrogue\b",
    r"\bweapon\b",
    r"\bbomb\b",
    r"\bhack\b",
    r"\bpirat",
]


def detecter_injection(message: str) -> tuple[bool, str | None]:
    texte = message.lower()
    for pattern in PATTERNS_INJECTION:
        if re.search(pattern, texte):
            return True, f"Tentative d'injection détectée : '{pattern}'"
    return False, None


def detecter_hors_perimetre(message: str) -> tuple[bool, str | None]:
    texte = message.lower()
    for pattern in HORS_PERIMETRE:
        if re.search(pattern, texte):
            return True, "Sujet hors périmètre JOJ"
    return False, None


def sanitiser_entree(message: str) -> str:
    # Supprime les caractères de contrôle et balises
    message = re.sub(r"[\x00-\x1f\x7f]", "", message)
    message = re.sub(r"<[^>]+>", "", message)
    return message.strip()
