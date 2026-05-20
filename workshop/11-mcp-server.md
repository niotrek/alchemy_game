# 11 — Inside an MCP Server

**Goal:** In [exercise 09](./09-plugins-playwright.md) you *used* an MCP server — the Playwright plugin. Now look *inside* one. This repo ships a small, working MCP server for the apothecary's store; you'll read its code, register it with your CLI, and buy ingredients just by asking the agent.

## Concepts

- **Exercise 09 used an MCP server — this one is ours to read.** The Playwright plugin was someone else's MCP server, a black box. Here the server is `backend/apothecaria/mcp/server.py` — about 100 lines, small enough to read in one sitting.
- **An MCP server is just a process that exposes tools.** It has **no model and no reasoning of its own.** It starts up, advertises a list of tools, and waits. Whatever *client* connects — Copilot CLI, Claude Code — brings the model, and *that model* decides when to call a tool. The server is pure capability; the brain lives in the client.
- **Tools are typed functions with docstrings.** Each `@mcp.tool()` function's name, parameters, and docstring become the contract the model reads to decide what to call. The model never sees the function body — a vague docstring means vague tool use.
- **stdio transport.** The client launches the server as a subprocess; they speak JSON-RPC over stdin/stdout. That is why "registering a server" is nothing more than handing the client a command to run.
- **Thin tools.** The store server holds **no game logic.** Each tool is a small HTTP call to the Apothecaria backend. The buying rules — prices, stock, "can you afford it" — live in the backend (`domain/store.py`), in one place. The MCP server is only an *interface* onto them.
- **Looking ahead — exercise 12.** You'll meet a pydantic-ai *agent* that buys ingredients over the *same* `/api/store` API. Same capability, different container: the agent carries its own model, persona, and reasoning loop, where this MCP server carries none. Holding the API constant is what makes that contrast sharp.

## The code

Four files — read them bottom to top, capability first:

1. **`backend/apothecaria/domain/store.py`** — the capability. `purchase()` checks store stock and the player's money, then moves money, stock, and inventory together; `list_store()` reads what's for sale. No HTTP, no MCP — just the rules.
2. **`backend/apothecaria/api/store.py`** — the HTTP layer. `GET /api/store` and `POST /api/store/buy` wrap the domain functions; a `PurchaseError` becomes a `409`, an unknown ingredient a `404`.
3. **`backend/apothecaria/mcp/server.py`** — the MCP server. `mcp = FastMCP("apothecaria-store")`, then four `@mcp.tool()` functions — `list_store`, `get_balance`, `list_inventory`, `buy_ingredient`. Each is a handful of lines: open an HTTP client, call the backend, return a readable string. Note there is **no model here** — and note the docstrings, which are what the client's model actually reads.
4. **`.mcp.json`** (repo root) — how a client launches the server: `uv run python -m apothecaria.mcp.server`.

Two of the four tools (`get_balance`, `list_inventory`) call endpoints that already existed (`/api/player`, `/api/inventory`) — a tool may call any API. Only `/api/store` was new for this exercise.

## Run & play

Start from the `alchemy_game` repo root.

1. **Fresh database** — so you begin with `$100` to spend:
   ```bash
   make db-reset
   ```

2. **Start the backend** — the MCP server's tools call it, so it must be running:
   ```bash
   make backend-dev
   ```
   Leave it running. Confirm <http://localhost:8000/api/health> returns `{"status":"ok"}`.

3. **Register the MCP server.** In another terminal, from the repo root:

   **Copilot CLI** — start a session and register it, exactly as in [exercise 09](./09-plugins-playwright.md):
   ```bash
   copilot
   ```
   ```text
   > /mcp add apothecaria-store uv run python -m apothecaria.mcp.server
   > /mcp list
   ```
   `/mcp list` should show `apothecaria-store` and its four tools.

   **Claude Code** — the repo ships `.mcp.json`, so the server is already registered. Confirm with `/mcp`.

4. **Buy something — just ask.** Don't name tools; let the model pick:
   ```text
   > What can I buy at the store, and what can I afford? Then buy me 10 moonpetal.
   ```
   Watch the tool calls go by — `list_store`, `get_balance`, then `buy_ingredient`. Your `$` drops, the store's stock drops, your inventory goes up.

5. **Now poke it.** A read-and-run exercise only teaches you something if you break things:
   - **Out of stock** — "buy 9999 moonpetal." Watch the error travel back to the model.
   - **Unknown ingredient** — "buy a unicorn horn." There is no such slug.
   - **Spend beyond your means** — ask for far more than your `$` covers; the refusal returns as "you only have $X."
   - **Edit the contract** — open `mcp/server.py`, rewrite a tool's **docstring** (make `buy_ingredient` sound risky, say), restart the server, and ask again. The model's behaviour shifts because the docstring *is* the interface.

6. **Tear down:** `/exit` ends the Copilot CLI session and the server process with it. Stop the backend with `Ctrl-C`.

## Done when

- [ ] You read `domain/store.py`, `api/store.py`, and `mcp/server.py` and can say which one holds the buying *logic* — and which holds none
- [ ] `/mcp list` (or `/mcp`) shows `apothecaria-store` with its four tools
- [ ] You asked the agent to buy an ingredient and watched `$`, store stock, and inventory all change
- [ ] You triggered at least one error (out of stock / unknown ingredient / can't afford) and saw it return to the model as a readable message

## Tips

- **The server has no model — the client does.** If the agent buys the *wrong* thing, that is the client's model reasoning, not the server. The server only ever does exactly what a tool call asks.
- **Docstrings are the API.** The model reads a tool's name, parameters, and docstring — never its body. This is the single highest-leverage thing to get right in an MCP server.
- **Thin tools age well.** Because the rules live in `domain/store.py`, exercise 12's agent reuses them through the same `/api/store` — nothing is reimplemented, and the two exercises stay genuinely comparable.
- **`make mcp`** runs the server standalone (it just waits on stdio). Normally the *client* launches it; `make mcp` is a quick way to check it starts cleanly.
- **Backend somewhere else?** The server reads `APOTHECARIA_API_BASE_URL` (default `http://localhost:8000`).

## References

- [Model Context Protocol — spec & SDKs](https://modelcontextprotocol.io/)
- [Python MCP SDK — `FastMCP`](https://github.com/modelcontextprotocol/python-sdk)
- [Exercise 09 — Plugins and the Playwright Plugin](./09-plugins-playwright.md) — *using* an MCP server
- Exercise 12 — the pydantic-ai agent — the same capability, built as an agent
