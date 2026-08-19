import os
import secrets
from typing import Optional

def get_configured_api_key() -> Optional[str]:
    """
    Returns the configured MCP API Key from environment variables.
    If MCP_API_KEY is not set or empty, returns None (allowing local/private mode).
    """
    key = os.environ.get("MCP_API_KEY", "").strip()
    return key if key else None

def verify_token(token: Optional[str]) -> bool:
    """
    Verifies if a provided token is valid against the configured MCP_API_KEY.
    If no MCP_API_KEY is configured in the environment, local access is permitted.
    """
    expected_key = get_configured_api_key()
    if not expected_key:
        return True # Local / unauthenticated development mode
    
    if not token:
        return False
        
    # Support 'Bearer <token>' prefix or raw token
    if token.startswith("Bearer "):
        token = token[7:].strip()
        
    return secrets.compare_digest(token, expected_key)
