from app.config import get_settings


def verify_api_key(api_key: str | None) -> bool:
    """Verify the provided API key against the configured key."""
    if not api_key:
        return False
    
    settings = get_settings()
    return api_key == settings.api_key
