from time import time
from collections import defaultdict

# { utilisateur_id: [timestamps des requêtes] }
_historique: dict[str, list[float]] = defaultdict(list)

LIMITE_PAR_MINUTE = 10
FENETRE_SECONDES = 60


def verifier_limite(utilisateur_id: str) -> tuple[bool, str | None]:
    """Retourne (autorisé, message_erreur)."""
    maintenant = time()
    historique = _historique[utilisateur_id]

    # Purger les anciennes entrées hors fenêtre
    _historique[utilisateur_id] = [
        t for t in historique if maintenant - t < FENETRE_SECONDES
    ]

    if len(_historique[utilisateur_id]) >= LIMITE_PAR_MINUTE:
        return False, f"Limite atteinte : {LIMITE_PAR_MINUTE} requêtes/minute"

    _historique[utilisateur_id].append(maintenant)
    return True, None
