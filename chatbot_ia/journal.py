import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("chatbot_ia")


def journaliser(utilisateur_id: str, session_id: str, message: str, reponse: str, fallback: bool) -> None:
    logger.info(
        "utilisateur=%s | session=%s | fallback=%s | question=%s | reponse=%s",
        utilisateur_id,
        session_id,
        fallback,
        message[:100],
        reponse[:100],
    )
