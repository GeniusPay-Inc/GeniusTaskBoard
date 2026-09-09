from fastapi import Header, HTTPException

from app.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Protège les routes d'écriture (ADR-003) : clé partagée pour le back-office
    et les futurs clients machine (passerelle Arduino, autres apps).
    Phase 2 : remplacer/compléter par un JWT par utilisateur pour le back-office."""
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(401, "Clé API manquante ou invalide (en-tête X-API-Key)")
