import { ApiError, client } from "./api/client";
import type { Customer } from "./api/client";
import { makeWsClient } from "./api/ws-client";
import { session } from "./state/session";
import { initScene } from "./scene/scene";
import { createCauldron } from "./scene/cauldron";
import { createShelf, type Jar } from "./scene/shelf";
import { createDoor } from "./scene/door";
import { animateToCauldron } from "./scene/animations";
import { createCustomerDialog } from "./ui/customer-dialog";
import { createGrimoirePanel } from "./ui/grimoire-panel";
import { createBrewResult } from "./ui/brew-result";
import { createInventoryBar } from "./ui/inventory-bar";
import { showToast } from "./ui/toast";
import "./styles/main.css";

const scene = initScene();
const cauldron = createCauldron(scene.cauldronContainer);
const door = createDoor(scene.customerContainer);

const customerDialog = createCustomerDialog();
const grimoirePanel = createGrimoirePanel();
const brewResult = createBrewResult();
const inventoryBar = createInventoryBar();

let shelfJars: Jar[] = [];
const ingredientColors = new Map<string, string>();

void boot();

async function boot(): Promise<void> {
  try {
    const [inventory, recipes, player] = await Promise.all([
      client.getInventory(),
      client.getRecipes(),
      client.getPlayer(),
    ]);
    const shelf = createShelf(scene.shelfContainer, inventory);
    shelfJars = shelf.jars;
    grimoirePanel.setRecipes(recipes);
    brewResult.setRecipes(recipes);
    session.setMoney(player.money);

    inventory.forEach((i) => {
      ingredientColors.set(i.slug, defaultLiquidColorFor(i.slug));
    });

    enableJarPicking();
    wireOverlays();
    connectWs();
  } catch (err) {
    const msg = err instanceof ApiError ? err.detail : String(err);
    showToast(`Failed to start: ${msg}`, "error");
  }
}

function defaultLiquidColorFor(slug: string): string {
  let h = 2166136261;
  for (let i = 0; i < slug.length; i++) {
    h ^= slug.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const hue = Math.abs(h) % 360;
  return hslToHex(hue, 55, 40);
}

function hslToHex(h: number, s: number, l: number): string {
  s /= 100;
  l /= 100;
  const k = (n: number) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) =>
    Math.round(255 * (l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1))))).toString(16).padStart(2, "0");
  return `#${f(0)}${f(8)}${f(4)}`;
}

function enableJarPicking(): void {
  const tooltip = document.getElementById("overlay-tooltip")!;

  for (const jar of shelfJars) {
    jar.el.addEventListener("click", () => addJarToCauldron(jar));
    jar.el.addEventListener("pointerenter", (event) => {
      tooltip.textContent = jar.ingredient.name;
      tooltip.hidden = false;
      tooltip.style.left = `${event.clientX + 14}px`;
      tooltip.style.top = `${event.clientY + 14}px`;
    });
    jar.el.addEventListener("pointermove", (event) => {
      tooltip.style.left = `${event.clientX + 14}px`;
      tooltip.style.top = `${event.clientY + 14}px`;
    });
    jar.el.addEventListener("pointerleave", () => {
      tooltip.hidden = true;
    });
  }
}

function addJarToCauldron(jar: Jar): void {
  animateToCauldron(jar.el, scene.cauldronContainer, scene.flyLayer, jar.spriteUrl, () => {
    session.addIngredient(jar.ingredient.slug);
    cauldron.setLiquidColor(blendedCauldronColor());
  });
}

function blendedCauldronColor(): string {
  const slugs = session.get().cauldronContents;
  if (slugs.length === 0) return "#2a3a3a";
  let r = 0, g = 0, b = 0, n = 0;
  for (const s of slugs) {
    const hex = ingredientColors.get(s);
    if (!hex) continue;
    const m = hex.replace("#", "");
    r += parseInt(m.slice(0, 2), 16);
    g += parseInt(m.slice(2, 4), 16);
    b += parseInt(m.slice(4, 6), 16);
    n++;
  }
  if (n === 0) return "#2a3a3a";
  const toHex = (v: number) => Math.round(v / n).toString(16).padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function wireOverlays(): void {
  inventoryBar.onBrew(async () => {
    const slugs = session.get().cauldronContents;
    if (slugs.length === 0) return;
    try {
      const r = await client.brew(slugs);
      brewResult.showBrew(r);
      await refreshJarQuantities();
    } catch (err) {
      showToast(errorText(err), "error");
    }
  });

  inventoryBar.onClear(() => {
    session.clearCauldron();
    cauldron.resetColor();
  });

  inventoryBar.onGrimoire(() => grimoirePanel.toggle());

  customerDialog.onServe(async () => {
    const c = session.get().currentCustomer;
    if (!c) return;
    const slugs = session.get().cauldronContents;
    if (slugs.length === 0) {
      showToast("Add ingredients before serving");
      return;
    }
    try {
      const r = await client.serve(c.id, slugs);
      brewResult.showServe(r);
      session.setMoney(r.new_money);
      session.setCurrentCustomer(null);
      session.clearCauldron();
      cauldron.resetColor();
      customerDialog.hide();
      door.hideCustomer();
      await refreshJarQuantities();
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        showToast("That customer has left the shop");
        session.setCurrentCustomer(null);
        customerDialog.hide();
        door.hideCustomer();
      } else {
        showToast(errorText(err), "error");
      }
    }
  });
}

async function refreshJarQuantities(): Promise<void> {
  try {
    const inventory = await client.getInventory();
    const bySlug = new Map(inventory.map((i) => [i.slug, i.quantity]));
    for (const jar of shelfJars) {
      const qty = bySlug.get(jar.ingredient.slug);
      if (qty !== undefined) jar.updateQuantity(qty);
    }
  } catch {
    // silent — quantities will refresh on next action
  }
}

function connectWs(): void {
  const ws = makeWsClient();
  ws.onStatus((connected) => {
    if (!connected) showToast("Live updates paused — game still works");
  });
  ws.on((event) => {
    if (event.type === "customer.arrived") {
      const c: Customer = {
        id: event.id,
        name: event.name,
        persona: event.persona,
        ailment_narrative: event.ailment_narrative,
        ailment_category: event.ailment_category,
        expected_recipe_slug: "",
        sprite: event.sprite,
      };
      if (!session.get().currentCustomer) {
        session.setCurrentCustomer(c);
        customerDialog.show(c);
        door.showCustomer(c.sprite);
      }
    }
  });
  ws.connect();
}

function errorText(err: unknown): string {
  if (err instanceof ApiError) return err.detail || `HTTP ${err.status}`;
  return err instanceof Error ? err.message : String(err);
}
