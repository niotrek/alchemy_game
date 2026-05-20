"""Apothecaria store MCP server.

Exposes the apothecary store as MCP tools — browse stock, check the balance,
list owned ingredients, and buy — so any MCP client (Claude Code, Copilot CLI)
can shop for the alchemist. Each tool is a thin HTTP call to the running
Apothecaria backend; the purchasing logic lives in the backend, not here.

Run it over stdio with ``python -m apothecaria.mcp.server``.
"""

import httpx
from mcp.server.fastmcp import FastMCP

from apothecaria.config import settings

mcp = FastMCP("apothecaria-store")

_BACKEND_DOWN = (
    "The apothecary backend isn't reachable. Start it with `make backend-dev` " "and try again."
)


def _client() -> httpx.AsyncClient:
    """Open an HTTP client pointed at the Apothecaria backend."""
    return httpx.AsyncClient(base_url=settings.api_base_url, timeout=10.0)


@mcp.tool()
async def list_store() -> str:
    """List every ingredient the apothecary store sells, with its price and stock.

    Call this before buying so you know the valid ingredient slugs, their
    prices in $, and how many units are in stock.
    """
    try:
        async with _client() as http:
            response = await http.get("/api/store")
    except httpx.HTTPError:
        return _BACKEND_DOWN
    items = response.json()
    if not items:
        return "The store has nothing for sale."
    lines = [
        f"- {item['slug']} ({item['name']}): ${item['price']} each, " f"{item['stock']} in stock"
        for item in items
    ]
    return "The apothecary store sells:\n" + "\n".join(lines)


@mcp.tool()
async def get_balance() -> str:
    """Report how much money ($) the alchemist currently has to spend."""
    try:
        async with _client() as http:
            response = await http.get("/api/player")
    except httpx.HTTPError:
        return _BACKEND_DOWN
    return f"The alchemist has ${response.json()['money']}."


@mcp.tool()
async def list_inventory() -> str:
    """List the ingredients the alchemist already owns and how many of each."""
    try:
        async with _client() as http:
            response = await http.get("/api/inventory")
    except httpx.HTTPError:
        return _BACKEND_DOWN
    owned = [
        f"{item['quantity']} × {item['name']}" for item in response.json() if item["quantity"] > 0
    ]
    if not owned:
        return "The alchemist owns no ingredients yet."
    return "The alchemist owns: " + ", ".join(owned)


@mcp.tool()
async def buy_ingredient(ingredient_slug: str, quantity: int) -> str:
    """Buy a quantity of an ingredient from the apothecary store.

    Spends the alchemist's money and adds the ingredient to their inventory.
    ``ingredient_slug`` must be a slug from ``list_store`` (for example
    "moonpetal"); ``quantity`` is how many units to buy.
    """
    try:
        async with _client() as http:
            response = await http.post(
                "/api/store/buy",
                json={"ingredient_slug": ingredient_slug, "quantity": quantity},
            )
    except httpx.HTTPError:
        return _BACKEND_DOWN
    if response.is_success:
        return str(response.json()["message"])
    detail = response.json().get("detail", response.text)
    return f"Could not buy {quantity} {ingredient_slug}: {detail}"


def main() -> None:
    """Run the store MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
