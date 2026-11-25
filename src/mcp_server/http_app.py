"""Aplicatia ASGI pentru varianta dockerizata (HTTP, Bearer token).

Ruleaza separat de waitress, pe portul 8001; Caddy / clientul OpenCode
o acceseaza la /mcp.
"""

import os

from starlette.requests import Request
from starlette.responses import JSONResponse

from .auth import DatabaseTokenVerifier
from .server import create_server

mcp = create_server(auth=DatabaseTokenVerifier())


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Endpoint public de sanatate (nu e protejat de auth)."""
    return JSONResponse({"status": "ok", "service": "pfasimplu-mcp"})


app = mcp.http_app(path="/mcp")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PFASIMPLU_MCP_PORT", "8001")),
    )
