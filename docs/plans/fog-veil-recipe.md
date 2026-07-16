# Plan: Add "Fog Veil" Recipe

## Problem
Add a new mixture called **Fog Veil** to the apothecary. It must appear in `/api/recipes`, be brewable via `/api/brew`, and persist across server restarts (i.e., seeded into SQLite).

## Recipe Spec
- **slug**: `fog_veil`
- **name**: Fog Veil
- **ailment_category**: `confusion`
- **ingredients**: `["moonpetal", "sage", "feather"]`
- **lore**: "A swirling silver draught that lifts the haze from tangled thoughts."
- **sprite**: `fog_veil.png` (placeholder, follows existing pattern)

## Approach
All three ingredients already exist in `ingredients.json` — no new ingredients needed. The recipe just needs to be added to the content JSON and then tests updated to reflect the new count (5 recipes instead of 4, 5 recipe slugs instead of 4).

No API, domain, DB, or seed code changes are required — the existing generic machinery handles everything.

## Files to Touch

### 1. `backend/apothecaria/content/recipes.json` — **add recipe entry**
Append the Fog Veil object to the JSON array.

### 2. `backend/tests/test_seed.py` — **update counts**
- `test_seed_is_idempotent_no_duplicates`: change expected recipe count from `4` → `5`.

### 3. `backend/tests/test_api_recipes.py` — **update counts and slug set**
- `test_recipes_returns_four`: rename to `test_recipes_returns_five`, change `len(data) == 4` → `5`, add `"fog_veil"` to the expected slug set.

### 4. `backend/tests/test_brewing.py` — **add Fog Veil brew test**
Add a test that brewing `["moonpetal", "sage", "feather"]` returns `matched_recipe_slug == "fog_veil"` with `ailment_category == "confusion"`.

### 5. `frontend/public/sprites/potions/fog_veil.png` — **add sprite**
Download the zip from <https://opengameart.org/content/game-icons-of-fantasy-potions-pack-1> (same CraftPix pack used by all other potions). Extract `PNG/potions (2).png` (purple swirling flask) and copy it to `frontend/public/sprites/potions/fog_veil.png`.

### 6. `frontend/public/sprites/potions/ATTRIBUTION.md` — **update mapping**
Add a line: `- \`fog_veil.png\` ← \`potions (2).png\` (purple swirling flask)`.

## Post-Change Verification
- Run `make seed` to upsert into SQLite.
- Run `make test` to verify all tests pass.

## Notes
- No customer uses `ailment_category: "confusion"` yet. Adding a matching customer is out of scope for this task but would be a natural follow-up.
- No frontend changes needed — the recipe list is fetched dynamically.
