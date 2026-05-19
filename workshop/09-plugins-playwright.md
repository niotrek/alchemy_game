# 09 — Plugins and the Playwright Plugin

**Goal:** Extend Copilot CLI with a **Playwright plugin** so it can drive a real browser — then ask it to open the `alchemy_game` frontend, brew a potion, and screenshot the result.

## Concepts

- **What plugins are** — plugins extend Copilot CLI's *toolkit* at runtime. The base CLI can read/write files and run shell commands; a plugin adds **new tools** the model can call when relevant — browser control, database access, image generation, Linear, Slack, etc.
- **MCP — the standard interface for plugin tools.** Most Copilot CLI plugins are **MCP servers** (Model Context Protocol). An MCP server is a small process that exposes a set of tools over a standard protocol. You point Copilot at the server, it lists the tools at startup, and from then on the model can invoke them like the built-in ones.
- **The Playwright plugin** — exposes browser automation: navigate to URLs, click elements, fill forms, snapshot the DOM, take screenshots. Once it's wired up, you can ask copilot "open the app and brew a potion" and it will literally drive a Chromium window for you.---

- **Plugins vs everything else you've seen so far:**

  | Mechanism                                          | What it adds                  | When to reach for it             |
  | -------------------------------------------------- | ----------------------------- | -------------------------------- |
  | **Instructions** ([ex 03](./03-custom-instructions.md)) | Style/convention rules      | "Always docstring in reST"       |
  | **Skills** ([ex 07](./07-plan-to-skill.md))        | Project-specific playbooks    | "Add a new mixture"              |
  | **Agents** ([ex 05](./05-plan-and-review.md))      | A different way of *thinking* | `/plan`, `/review`               |
  | **Plugins (MCP servers)** *(this exercise)*        | **New tools** the AI can call | Browser, DB, Slack, Linear, etc. |

  Rule of thumb: instructions and skills change *how* Copilot writes code; plugins change **what it can do**.

## Steps

Run from the `alchemy_game` repo root. Start the game in another terminal first, so the Playwright plugin has a live URL to drive:

```bash
make dev
```

Confirm it's up at [http://localhost:5173](http://localhost:5173).

1. **Install the Playwright MCP server.** The official package is `@playwright/mcp` on npm. Either install it globally or run it on-demand with `npx`:
  ```bash
   npm install -g @playwright/mcp
   # or run on-demand (no install):
   # npx -y @playwright/mcp@latest --help
  ```
   On first run, Playwright also downloads a Chromium binary (~150 MB). That happens once.

2. **Register the plugin with Copilot CLI.** In a fresh session, tell the CLI how to launch the MCP server:
  ```bash
   copilot
  ```
  ```text
   > /mcp add playwright npx -y @playwright/mcp@latest
  ```
   `/mcp add <name> <command>` registers an MCP server: the **name** is yours to pick (we'll use `playwright`), the **command** is what the CLI runs to spawn the server process.

3. **Confirm the plugin is loaded** and inspect what it gives you:
  ```text
   > /mcp list
  ```
   You should see `playwright` and a list of the tools it exposes (`browser_navigate`, `browser_click`, `browser_snapshot`, `browser_take_screenshot`, etc.). For detail:
  ```text
   > /mcp info playwright
  ```

4. **Drive the frontend with a plain-English prompt.** Don't name tools — let the model pick:
  ```text
   > Open the alchemy game at http://localhost:5173 in the browser. Wait for the first customer to arrive, read what they're asking for, brew the matching potion using the ingredients in the workshop, and take a screenshot of the result. Tell me what happened at each step.
  ```
   A Chromium window should pop up. Watch Copilot click through the UI — and watch the streamed reasoning: "I see a customer named X asking for Y. I'll select these ingredients and click Brew. The result is Z."

5. **Confirm the plugin actually drove the work.** Ask the CLI directly:
  ```text
   > Which tools did you use for that last task?
  ```
   It should mention `playwright`/`browser_*` tools. If it didn't, the plugin probably isn't registered correctly — re-run `/mcp list` and check.

6. **Tear it down when done:**
  ```text
   > /exit
  ```
   The MCP server process exits with the session.

## Done when

- [ ] `/mcp list` shows `playwright` and the browser tools it exposes
- [ ] You watched Copilot open a real Chromium window and click through the frontend
- [ ] A screenshot of the game state was saved (check the agent's reply for the path)
- [ ] Asking "which tools did you use" returns `playwright`/`browser_*` tools, not just file reads

## Tips

- **`/mcp` is per-session by default.** `/mcp add` registers the plugin only for this session. To make it permanent, add the server to your project's MCP config (`.github/copilot/mcp.json` or similar) or to your global `~/.copilot/mcp.json`, so every session loads it automatically.
- **One plugin, many tools.** The Playwright plugin exposes ~20 browser actions. The model picks the right one from your prompt — "click the brew button" → `browser_click`; "what's on the page now?" → `browser_snapshot`. You don't name tools explicitly.
- **Plugins compose with skills.** A skill from [exercise 07](./07-plan-to-skill.md) can end with "and verify the change in the browser" and lean on the Playwright plugin for the verification step — write the skill once, get end-to-end coverage for free.
- **Headless when you're not watching.** Most browser MCP servers accept a `--headless` flag in the launch command (e.g. `npx -y @playwright/mcp@latest --headless`). Useful for CI; keep headed mode locally so you can see what the agent is doing.
- **Other plugins worth knowing:** Filesystem MCP (sandboxed file ops), GitHub MCP (issues/PRs), Slack MCP, Linear MCP, Postgres MCP. The [MCP registry](https://github.com/modelcontextprotocol/servers) is a good place to browse.

## References

- [Model Context Protocol (MCP) — spec & SDKs](https://modelcontextprotocol.io/)
- [Playwright MCP server — official repo](https://github.com/microsoft/playwright-mcp)
- [`modelcontextprotocol/servers` — community MCP servers](https://github.com/modelcontextprotocol/servers)
- [Copilot CLI command reference](https://docs.github.com/en/copilot/reference/cli-command-reference) — `/mcp`
- [About GitHub Copilot Extensions](https://docs.github.com/en/copilot/concepts/about-github-copilot-extensions)
