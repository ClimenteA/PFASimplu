"""Scurtatura: `python -m mcp_server local` (stdio)."""

import sys

from .local import main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        from .http_app import app
        import os
        import uvicorn

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.environ.get("PFASIMPLU_MCP_PORT", "8001")),
        )
    else:
        main()
