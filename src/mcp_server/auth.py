"""Autorizarea serverului MCP prin cheia generata in /setari.

Fiecare cheie e legata de contul care a generat-o. Cheia in clar nu e salvata
nicieri: in DB avem doar hash-ul cu salt. Verificarea se face la fiecare
request HTTP (Bearer), deci revocarea cheii are efect imediat.
"""

import asyncio

from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.dependencies import get_access_token

from .django_setup import setup_django

setup_django()

from setari.models import McpApiKey


def _key_e_utilizabil(key: McpApiKey) -> bool:
    """O cheie fara cont asociat nu are voie sa acceseze date."""
    return key.user_id is not None


class DatabaseTokenVerifier(TokenVerifier):
    """TokenVerifier FastMCP care verifica cheia impotriva hash-ului din DB."""

    async def verify_token(self, token: str) -> AccessToken | None:
        key = await asyncio.to_thread(McpApiKey.verify, token)
        if key is None or not _key_e_utilizabil(key):
            return None
        return AccessToken(
            token=token,
            client_id=f"pfasimplu-user-{key.user_id}",
            scopes=[],
            claims={
                "user_id": key.user_id,
                "key_prefix": key.prefix,
                "key_name": key.nume,
            },
        )


def current_key_user_id() -> int | None:
    """ID-ul contului asociat cheii curente (claims-urile requestului HTTP)."""
    token = get_access_token()
    if token is None:
        raise ValueError("Requestul MCP nu are o cheie de acces valida.")
    return token.claims.get("user_id")
