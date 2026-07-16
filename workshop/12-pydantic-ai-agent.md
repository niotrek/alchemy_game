# 12 — Inside an Agent

**Goal:** In [exercise 11](./11-mcp-server.md) you looked inside an MCP server — pure capability, no brain of its own. Now meet an **agent**: the *same* buying capability, wrapped in a program that carries its own brain. You'll read its code, register a model for it, run it, and chat with it through a small web UI.

## Concepts

- **An MCP server is capability; an agent is a program.** The exercise 11 server could not act on its own — Copilot CLI brought the model and decided when to call a tool. This agent brings its **own** model, its own persona, and its own reasoning loop. You start it with `agent.run(goal)` and it does the rest. No Copilot CLI in sight.
- **Same capability, different container.** The agent buys ingredients over the *same* `/api/store` API the MCP server used. Hold the capability constant, and the only thing left to compare is the container — and that *is* the lesson:

  | | MCP server (ex 11) | pydantic-ai agent (ex 12) |
  |---|---|---|
  | Has an LLM? | No — the client's model | **Yes — its own** |
  | Has a persona? | No | **Yes (`system_prompt`)** |
  | Runs a reasoning loop? | No | **Yes** |
  | Who decides to call a tool? | Whatever client connects | **The agent's own model** |
  | How it is invoked | A host launches it; it serves and waits | **`agent.run(goal)` — it's a program** |

- **An agent = model + persona + tools + a loop.** `agents/shopper.py` is one `Agent(...)`: a model (GitHub Models), a `system_prompt` that gives it a personality, four tools, and pydantic-ai's built-in loop that lets the model call tools until it has an answer.
- **The persona is real behaviour.** The MCP server did exactly what a tool call said — nothing more. This agent has a `system_prompt` that makes it thrifty: push it to overspend and it will push back on its own. That restraint is the persona, not the tools.
- **The UI is just a shell.** `agents/chat.py` is a thin Chainlit wrapper around `agent.run()`. The agent would run the same from a script, a cron job, or a web backend — Chainlit is one face, not the agent.

## The code

Two files:

1. **`backend/apothecaria/agents/shopper.py`** — the agent. A model from GitHub Models, a `system_prompt` (the shopping-apprentice persona), and four `@agent.tool_plain` tools — `list_store`, `get_balance`, `list_inventory`, `buy_ingredient`. **Open it side by side with `mcp/server.py` from exercise 11.** The tool bodies are nearly identical — the same `httpx` calls to `/api/store`. What's new is the model and the persona: that is the whole difference between an MCP server and an agent.
2. **`backend/apothecaria/agents/chat.py`** — the Chainlit chat UI. It reads your message, calls `agent.run()`, shows each tool call as a collapsible step, and prints the reply. About 65 lines — a shell, not the lesson.

> *Aside:* an agent can also *consume* an MCP server as one of its toolsets — that's composition, a different topic. This exercise keeps the two side by side so the contrast stays clean.

## Setup — give the agent a model

The agent needs its own LLM. We use **GitHub Models** — you already have a GitHub account for Copilot CLI.

1. **Create a token.** Open <https://github.com/settings/personal-access-tokens/new> (a fine-grained personal access token). Give it a name and an expiry; you don't need to grant any repository access. Under **Permissions → Account permissions**, find **Models** and set it to **Read-only**. Click **Generate token** and copy it.
2. **Put it in `.env`.** From the `alchemy_game` repo root:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your token after `GITHUB_API_KEY=`:
   ```
   GITHUB_API_KEY=github_pat_xxxxxxxxxxxx
   ```
   `.env` is git-ignored — your token stays on your machine.

## Run & play

Start from the `alchemy_game` repo root.

1. **Fresh database** — so you begin with `$100` to spend:
   ```bash
   make db-reset
   ```

2. **Start the backend** — the agent's tools call it, so it must be running:
   ```bash
   make backend-dev
   ```
   Leave it running. Confirm <http://localhost:8000/api/health> returns `{"status":"ok"}`.

3. **Start the agent** — in another terminal:
   ```bash
   make agent
   ```
   Chainlit opens a chat in your browser at <http://localhost:8001>. (Port 8001 — the backend already holds 8000.)

4. **Chat with it.** Don't name tools; give it a goal:
   ```text
   What can I afford right now? Then stock me up for healing potions.
   ```
   Watch the steps unfold: the agent calls `list_store`, `get_balance`, maybe `list_inventory`, then `buy_ingredient` — its *own* model driving its *own* loop. Your `$`, the store's stock, and your inventory all change.

5. **Now poke it.** This is where the agent-vs-server difference shows:
   - **The persona pushes back.** Tell it "spend every coin on eye-of-newt, I don't care." Watch it stay thrifty or buy only what's sensible — that restraint lives in the `system_prompt`. The MCP server had no persona; it would just have run the buy.
   - **Rewrite the persona.** Open `shopper.py`, edit the `system_prompt` — make the apprentice reckless and extravagant. Save (the `-w` flag reloads the app), start a new chat, and watch its character change.
   - **Give it a vague goal.** "I want to brew something cheerful" — watch the loop browse and reason across several tool calls before it buys.
   - **Trigger an error.** Ask it to buy "a dragon scale" — there is no such ingredient. The error returns to the model, which explains it to you in chat.

6. **Tear down:** `Ctrl-C` in both terminals.

## Done when

- [ ] You can name three things the agent has that the exercise 11 MCP server did not: its own model, a persona, and a reasoning loop
- [ ] You chatted with the agent and watched it call tools and change your `$`, store stock, and inventory
- [ ] You edited the `system_prompt` and saw the agent's behaviour shift
- [ ] You triggered an error and saw the agent explain it in chat

## Tips

- **The brain moved.** In exercise 11 the model lived in Copilot CLI; the server had none. Here the model lives *inside* `shopper.py`. That one move — bringing your own model — is what turns capability into an agent.
- **`system_prompt` is the personality.** It's the first thing to edit when an agent behaves wrong. The tools decide what's *possible*; the system prompt decides what the agent *does*.
- **Same `/api/store`, on purpose.** The agent reuses exercise 11's API exactly — no buying logic was rewritten. That's what makes the two exercises a fair comparison.
- **Rate limits.** GitHub Models' free tier is rate-limited. If the agent stalls, wait a moment and ask again.
- **The UI is swappable.** Chainlit is ~65 lines in `chat.py`. The same agent would run from a cron job or a FastAPI endpoint — the agent is the program; the UI is just a shell.

## References

- [Exercise 11 — Inside an MCP Server](./11-mcp-server.md) — the same capability, with no model of its own
- [pydantic-ai — agents, tools, and models](https://ai.pydantic.dev/)
- [GitHub Models](https://docs.github.com/en/github-models)
- [Chainlit](https://docs.chainlit.io/)
