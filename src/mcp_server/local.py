"""Transport stdio pentru aplicatia locala (desktop / sursa).

Cheia se trimite prin variabila de mediu PFASIMPLU_MCP_TOKEN si se verifica
impotriva hash-ului din DB la pornire si la fiecare apel de tool.
"""

import asyncio
import sys

from fastmcp.server.middleware import Middleware, MiddlewareContext

from .auth import verify_local_token
from .server import create_server


class VerificaCheieLocala(Middleware):
    """Revocarea cheii are efect imediat si in modul stdio."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        await asyncio.to_thread(verify_local_token)
        return await call_next(context)


def main() -> None:
    try:
        verify_local_token()
    except ValueError as exc:
        print(f"Eroare MCP: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    create_server(middleware=[VerificaCheieLocala()]).run(transport="stdio")


if __name__ == "__main__":
    main()
