"""Autorizarea serverului MCP prin cheia generata in /setari.

Fiecare cheie e legata de contul care a generat-o (in modul desktop e fara
user). Cheia in clar nu e salvata nicieri: in DB avem doar hash-ul cu salt.
Verificarea se face la fiecare request HTTP (Bearer) si la fiecare tool call
in modul stdio, deci revocarea cheii are efect imediat.
"""

import asyncio
import os

from django.conf import settings
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.dependencies import get_access_token

from .django_setup import setup_django

setup_django()

from setari.models import McpApiKey  # noqa: E402  (după django.setup())

LOCAL_TOKEN_ENV = "PFASIMPLU_MCP_TOKEN"


def _key_e_utilizabil(key: McpApiKey) -> bool:
    """In modul multi-user o cheie fara user nu are voie sa acceseze date."""
    return not settings.MULTI_USER or key.user_id is not None


class DatabaseTokenVerifier(TokenVerifier):
    """TokenVerifier FastMCP care verifica cheia impotriva hash-ului din DB."""

    async def verify_token(self, token: str) -> AccessToken | None:
        key = await asyncio.to_thread(McpApiKey.verify, token)
        if key is None or not _key_e_utilizabil(key):
            return None
        return AccessToken(
            token=token,
            client_id=f"pfasimplu-user-{key.user_id or 'desktop'}",
            scopes=[],
            claims={
                "user_id": key.user_id,
                "key_prefix": key.prefix,
                "key_name": key.nume,
            },
        )


def verify_local_token() -> McpApiKey:
    """Verifica cheia din mediul procesului stdio si o returneaza.

    OpenCode (sau alt client) o poate trimite prin `--env PFASIMPLU_MCP_TOKEN=...`.
    Lipsa cheii / o cheie gresita opreste serverul la pornire.
    """
    token = os.environ.get(LOCAL_TOKEN_ENV, "").strip()
    if not token:
        raise ValueError(
            f"Lipseste cheia MCP. Genereaza una in /setari si pune-o in "
            f"variabila de mediu {LOCAL_TOKEN_ENV}."
        )
    key = McpApiKey.verify(token)
    if key is None or not _key_e_utilizabil(key):
        raise ValueError(
            f"Cheia MCP din {LOCAL_TOKEN_ENV} nu este valida sau a fost revocata. "
            "Genereaza una noua in /setari."
        )
    return key


def current_key_user_id() -> int | None:
    """ID-ul contului asociat cheii curente, indiferent de transport.

    - HTTP: FastMCP pune claims-urile verificate in contextul requestului;
    - stdio: reluam verificarea cheii din mediu (revocare imediata).
    """
    token = get_access_token()
    if token is not None:
        return token.claims.get("user_id")
    key = verify_local_token()
    return key.user_id
