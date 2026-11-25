"""Instanta FastMCP. Aceeasi lista de tool-uri e folosita de ambele transporturi."""

from fastmcp import FastMCP

from .tools import register_tools


def create_server(*, auth=None, middleware=None) -> FastMCP:
    mcp = FastMCP(
        name="PFASimplu",
        instructions=(
            "Server MCP pentru aplicatia de contabilitate PFASimplu. "
            "Ofera citirea setarilor, listarea incasarilor/cheltuielilor/facturilor/"
            "documentelor, un sumar anual cu taxe estimate si adaugarea de incasari "
            "si cheltuieli. Nu exista tool-uri de stergere. "
            "Tool-urile ruleaza in contextul contului care a generat cheia MCP, "
            "deci acceseaza doar datele acelui cont."
        ),
        auth=auth,
        middleware=middleware,
    )
    register_tools(mcp)
    return mcp
