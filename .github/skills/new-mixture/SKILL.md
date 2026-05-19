---
name: new-mixture
description: >-
  Adds a new mixture (recipe, potion, or brew) to the Apothecaria game.
  Use this skill whenever someone asks to add, create, or introduce a new
  mixture, recipe, potion, brew, or draught — even if they don't use those
  exact words. Handles everything from validating ingredients through
  opening a PR.
---

# New Mixture

A mixture is a recipe entry in the apothecary's book. Once added, it
appears in `/api/recipes` and becomes brewable via `/api/brew`. The
game's seed-loader and brewing engine pick up new recipes automatically —
no API, domain, or DB code changes are needed.

## What you need from the user

Collect all five of these before touching any files. If something is
missing, ask — don't guess.

| Field              | Format                         | Example              |
| ------------------ | ------------------------------ | -------------------- |
| **slug**           | `snake_case`, unique           | `fog_veil`           |
| **name**           | Display name                   | Fog Veil             |
| **ailment_category** | Short lowercase tag          | `confusion`          |
| **ingredients**    | List of existing ingredient slugs | `["moonpetal", "sage", "feather"]` |
| **lore**           | One evocative sentence         | "A swirling silver draught…" |

Reuse an existing `ailment_category` when it fits (`sleep`, `fatigue`,
`anxiety`, `wound`, `confusion`, `sorrow`, …). Invent a new one only
when nothing matches.

## Before you start

1. **Working tree is clean.** Run `git status`. If there are uncommitted
   changes, ask the user to commit or stash first — mixing unrelated
   changes makes the PR messy.
2. **`gh` is authenticated.** Run `gh auth status`. If it fails, finish
   through the test step and then tell the user to run `gh auth login`.

## Workflow

### 1 — Validate ingredients

Read `backend/apothecaria/content/ingredients.json` and confirm every
requested slug exists. If any are missing, stop — adding ingredients is a
separate task. Tell the user which ones are missing so they can add them
first.

### 2 — Confirm uniqueness

Read `backend/apothecaria/content/recipes.json` and check two things:

- The new **slug** doesn't already exist.
- The new **ingredient set** (order-independent) doesn't match any
  existing recipe. The brewing engine matches by exact ingredient set, so
  duplicates would collide and one recipe would shadow the other.

### 3 — Add the recipe entry

Append a new JSON object to `backend/apothecaria/content/recipes.json`.
Match the shape and one-line-per-object formatting of existing entries.
Include a `sprite` field set to `<slug>.png` — the actual image can be
added later.

Preserve the trailing newline at end of file.

### 4 — Re-seed the database

```bash
make seed
```

This upserts the new recipe into SQLite. No migration is needed — the
seed loader handles everything.

### 5 — Update tests

Three test files reference recipe counts or slug sets. Update them all:

**`backend/tests/test_api_recipes.py`** — The test that asserts the
total recipe count and the set of slugs needs to include the new recipe.
Add the new slug to the expected set and bump the count.

**`backend/tests/test_seed.py`** — The idempotency test
(`test_seed_is_idempotent_no_duplicates`) asserts the total number of
recipes. Bump the expected count by one.

**`backend/tests/test_brewing.py`** — Add a new test that brews the
exact ingredient list and asserts `matched_recipe_slug`, `matched_recipe_name`,
`matched_ailment_category`, and `quality_score == 1.0`. Follow the
pattern of the existing exact-match tests.

### 6 — Run the test suite

```bash
make test
```

All tests must pass. If anything fails, fix it before continuing.

### 7 — Branch, commit, and open a PR

```bash
git checkout -b add-mixture-<slug>
git add backend/apothecaria/content/recipes.json \
       backend/tests/test_api_recipes.py \
       backend/tests/test_seed.py \
       backend/tests/test_brewing.py
git commit -m "feat(content): add <name> mixture"
git push -u origin add-mixture-<slug>
gh pr create \
  --title "Add <name> mixture" \
  --body "## Summary
Adds **<name>** (\`<slug>\`) for the \`<ailment_category>\` ailment.

## Recipe
- **Ingredients:** <comma-separated slugs>
- **Lore:** <lore>

## Verification
- \`make seed\` upserts the new recipe.
- \`make test\` passes with updated counts and a new brew test.

## Scope
Content-only change. Does not touch API routes, brewing logic, DB
models, or frontend — they pick up new recipes automatically."
```

Substitute all `<placeholders>`. Print the PR URL that `gh` returns.

### 8 — Show the diff

Run `/diff` and give the user a short summary of what changed.

## Files this skill touches

| File | Change |
| ---- | ------ |
| `backend/apothecaria/content/recipes.json` | New recipe object |
| `backend/tests/test_api_recipes.py` | Updated count + slug set |
| `backend/tests/test_seed.py` | Updated recipe count |
| `backend/tests/test_brewing.py` | New exact-match brew test |

## Boundaries

- **Don't** add new ingredients. If the recipe needs one that doesn't
  exist, stop and tell the user.
- **Don't** edit API routes, brewing logic, or DB models — the generic
  machinery handles everything.
- **Don't** add a database migration. The JSON seed is the source of
  truth; `make seed` upserts.
- **Don't** touch the frontend. The recipe list is fetched dynamically.
