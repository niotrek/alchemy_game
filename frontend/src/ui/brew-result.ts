import type { BrewResult, Recipe, ServeResult } from "../api/client";

export type BrewResultOverlay = {
  setRecipes: (recipes: Recipe[]) => void;
  showBrew: (r: BrewResult) => void;
  showServe: (r: ServeResult) => void;
};

const TOAST_MS = 4000;

export function createBrewResult(): BrewResultOverlay {
  const root = document.getElementById("overlay-brew-result")!;
  let timer: number | null = null;
  const spriteBySlug = new Map<string, string>();

  function showHTML(html: string, accent: string): void {
    if (timer !== null) window.clearTimeout(timer);
    root.innerHTML = `<div class="card toast" style="border-color:${accent}">${html}</div>`;
    root.hidden = false;
    timer = window.setTimeout(() => {
      root.hidden = true;
      root.innerHTML = "";
      timer = null;
    }, TOAST_MS);
  }

  return {
    setRecipes: (recipes) => {
      spriteBySlug.clear();
      for (const r of recipes) if (r.sprite) spriteBySlug.set(r.slug, r.sprite);
    },
    showBrew: (r) => {
      const title = r.matched_recipe_name ?? "Unknown brew";
      const quality = `${Math.round(r.quality_score * 100)}% quality`;
      const sprite = r.matched_recipe_slug ? spriteBySlug.get(r.matched_recipe_slug) : null;
      const img = sprite ? `<img class="toast-sprite" src="/sprites/potions/${esc(sprite)}" alt="" />` : "";
      showHTML(
        `<div class="toast-row">${img}<div><h3>${esc(title)}</h3><p>${esc(r.description)}</p><p class="meta">${esc(quality)}</p></div></div>`,
        r.matched_recipe_slug ? "var(--candle-gold)" : "var(--moonlight)",
      );
    },
    showServe: (r) => {
      const accent =
        r.outcome === "delighted"
          ? "var(--candle-gold)"
          : r.outcome === "neutral"
            ? "var(--moonlight)"
            : "#a44";
      const sign = r.money_delta >= 0 ? "+" : "";
      showHTML(
        `<h3>${esc(r.outcome)}</h3><p>${esc(r.customer_response)}</p><p class="meta">$ ${sign}${r.money_delta} → $${r.new_money}</p>`,
        accent,
      );
    },
  };
}

function esc(s: string): string {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );
}
