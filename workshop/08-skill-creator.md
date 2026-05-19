# 08 — Skill Creator

**Goal:** Install Anthropic's **`skill-creator`** skill and use it to author a new skill *from the plan you wrote in [exercise 05](./05-plan-and-review.md)* — instead of hand-writing `SKILL.md` like we did in [exercise 07](./07-plan-to-skill.md).

## Concepts

- **`skill-creator`** is an official Anthropic skill that builds *other* skills. Give it a workflow, a plan, or a description of what you want repeated, and it produces a properly-shaped `SKILL.md` (correct frontmatter, discoverable description, clear steps, "what NOT to do") and drops it in the right directory.
- **Why this matters.** Exercise 07 walked the manual path so you understand what a skill is. In practice, `skill-creator` is the fast lane: it knows the conventions (third-person `description`, trigger phrases, `Required inputs` + `Preconditions` + `Steps` + `What NOT to do` sections), so you spend your time on the *content* of the playbook, not its shape.
- **It also evaluates.** `skill-creator` can run small evals against a skill — does it actually fire on the prompts you expect? — and suggest description tweaks if your skill is being missed.
- **Where it comes from.** `npx skills` is the agentskills installer. `anthropics/skills@skill-creator` is the official Anthropic registry entry; `-g` installs globally so every project can use it, `-y` accepts prompts.
- **Plan → skill → execution, end to end.** The full loop you've now seen is `/plan` (exercise 05) → `/skill-creator` (this exercise) → natural-language invocation. The plan is one-shot; the skill is the reusable distillation.

## Steps

Run from the `alchemy_game` repo root.

1. **Install the skill globally** and reload so the CLI picks it up:

   ```bash
   npx skills add anthropics/skills@skill-creator -g -y
   ```

   ```bash
   copilot
   ```

   ```text
   > /skills reload
   > /skills list
   ```

   You should see `skill-creator` listed alongside `new-mixture` from exercise 07. Inspect it:

   ```text
   > /skills info skill-creator
   ```

2. **Use it to draft a skill from your existing plan.** Point it at the plan you generated in [exercise 05](./05-plan-and-review.md):

   ```text
   > /skill-creator Read docs/plans/fog-veil-recipe.md and create a project-scoped skill at .github/skills/new-mixture-v2/ that captures this workflow as a reusable playbook. Required inputs: slug, name, ailment_category, ingredients, lore. The skill should also handle re-seeding, extending tests, and opening a PR. Use a different folder name than the existing new-mixture skill so we can compare them side by side.
   ```

   Watch what it does:
   - Reads the plan and pulls out the *repeatable* steps (drops the Fog-Veil-specific bits like the sprite download URL and the `4 → 5` test-count update).
   - Drafts `SKILL.md` with proper frontmatter, a discoverable `description`, and a `What NOT to do` section.
   - Writes the file to `.github/skills/new-mixture-v2/SKILL.md`.

   Compare its output to the hand-written version in [`07-SKILL.md`](./07-SKILL.md) — they should be functionally equivalent. Note what `skill-creator` chose differently (description phrasing, ordering of steps, which preconditions it added).

3. **Trigger it and (optionally) ask `skill-creator` to evaluate.** Reload skills, then ask in plain English:

   ```text
   > /skills reload
   > Add a new mixture called "Sorrowmend Cordial" — ailment_category sorrow, ingredients [root, moonpetal, feather]. Lore: a warm amber draught that softens grief without numbing it.
   ```

   The generated skill should fire. If it doesn't — or if you want to harden the description — ask `skill-creator` to run an eval:

   ```text
   > /skill-creator Evaluate .github/skills/new-mixture-v2/SKILL.md against these trigger phrases: "add a new potion", "make a new brew", "create a recipe for X", "I need a mixture that cures Y". Tell me which fire, which don't, and improve the description to cover the misses.
   ```

## Done when

- [ ] `skill-creator` shows in `/skills list`
- [ ] `.github/skills/new-mixture-v2/SKILL.md` exists and was generated from `docs/plans/fog-veil-recipe.md`
- [ ] The generated skill triggers on "add a new mixture…"-style prompts
- [ ] You've eyeballed the diff between the hand-written `07-SKILL.md` and the auto-generated `new-mixture-v2/SKILL.md` and have an opinion on which is better

## Tips

- **Edit, don't regenerate.** Once `skill-creator` produces a `SKILL.md`, hand-edit it for project-specific quirks rather than re-running with a slightly different prompt. The *shape* is the value `skill-creator` adds; the *content* is yours to refine.
- **Eval before shipping.** Run `skill-creator`'s eval mode once before committing a new skill so your teammates aren't the ones discovering it doesn't fire.
- **It works on existing skills too.** Point `skill-creator` at any `SKILL.md` and ask "improve this description" or "are the steps in the right order?" — useful for cleaning up skills that were written quickly.

## References

- [`anthropics/skills` on GitHub](https://github.com/anthropics/skills) — source for the `skill-creator` skill
- [agentskills.io — skill specification](https://agentskills.io/specification) — the format `skill-creator` is producing
- [Exercise 07 — Plan to Skill](./07-plan-to-skill.md) — the manual version of what this skill automates
