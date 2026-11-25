"""Entry point pentru build-ul PyInstaller al serverului MCP stdio.

Ruleaza ca script (nu ca modul), deci foloseste importuri absolute.
"""

from mcp_server.local import main


if __name__ == "__main__":
    main()
