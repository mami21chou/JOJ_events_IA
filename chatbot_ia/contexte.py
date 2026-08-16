from .schemas import MessageContexte

# { session_id: [MessageContexte] }
_sessions: dict[str, list[MessageContexte]] = {}

LIMITE_HISTORIQUE = 10  # nombre max de messages conservés par session


def ajouter_message(session_id: str, role: str, contenu: str) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append(MessageContexte(role=role, contenu=contenu))

    # Garde seulement les N derniers messages
    if len(_sessions[session_id]) > LIMITE_HISTORIQUE:
        _sessions[session_id] = _sessions[session_id][-LIMITE_HISTORIQUE:]


def obtenir_historique(session_id: str) -> list[dict]:
    messages = _sessions.get(session_id, [])
    return [{"role": m.role, "content": m.contenu} for m in messages]


def effacer_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
