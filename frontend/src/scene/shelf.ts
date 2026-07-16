import type { Ingredient } from "../api/client";
import { session } from "../state/session";

export type Jar = {
  el: HTMLElement;
  ingredient: Ingredient;
  spriteUrl: string;
};

export type Shelf = {
  jars: Jar[];
};

const ROWS = 1;
const COLS = 6;

function jarBodyColors(slug: string): { body: string; bodyDark: string } {
  let h = 2166136261;
  for (let i = 0; i < slug.length; i++) {
    h ^= slug.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const hue = Math.abs(h) % 360;
  return {
    body: `hsla(${hue}, 45%, 55%, 0.55)`,
    bodyDark: `hsla(${hue}, 50%, 25%, 0.75)`,
  };
}

function makeJar(ing: Ingredient): Jar {
  const el = document.createElement("button");
  el.className = "jar";
  el.type = "button";
  el.dataset.slug = ing.slug;
  el.setAttribute("aria-label", ing.name);

  const { body, bodyDark } = jarBodyColors(ing.slug);
  el.style.setProperty("--jar-body", body);
  el.style.setProperty("--jar-body-dark", bodyDark);

  const cork = document.createElement("div");
  cork.className = "jar-cork";
  const bodyDiv = document.createElement("div");
  bodyDiv.className = "jar-body";
  const label = document.createElement("div");
  label.className = "jar-label";

  const spriteUrl = `/sprites/ingredients/${ing.sprite || `${ing.slug}.png`}`;
  const sprite = document.createElement("img");
  sprite.className = "jar-sprite";
  sprite.src = spriteUrl;
  sprite.alt = "";

  el.append(bodyDiv, cork, sprite, label);
  return { el, ingredient: ing, spriteUrl };
}

export function createShelf(container: HTMLElement, ingredients: Ingredient[]): Shelf {
  container.replaceChildren();
  const jars: Jar[] = [];
  const items = ingredients.slice(0, ROWS * COLS);

  for (let r = 0; r < ROWS; r++) {
    const row = document.createElement("div");
    row.className = "shelf-row";
    const jarRow = document.createElement("div");
    jarRow.className = "shelf-jars";
    const board = document.createElement("div");
    board.className = "shelf-board";

    for (let c = 0; c < COLS; c++) {
      const i = r * COLS + c;
      if (i >= items.length) break;
      const jar = makeJar(items[i]);
      jarRow.appendChild(jar.el);
      jars.push(jar);
    }
    row.append(jarRow, board);
    container.appendChild(row);
  }

  session.subscribe((state) => {
    for (const jar of jars) {
      const qty = state.ingredientQuantities[jar.ingredient.slug];
      const label = jar.el.querySelector(".jar-label") as HTMLElement;
      label.textContent = qty !== undefined ? String(qty) : "";
    }
  });

  return { jars };
}
