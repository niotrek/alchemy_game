export type Ingredient = {
  slug: string;
  name: string;
  lore: string;
  sprite: string;
  quantity: number;
};

export type Recipe = {
  slug: string;
  name: string;
  ailment_category: string;
  lore: string;
  sprite: string;
  ingredient_slugs: string[];
};

export type Customer = {
  id: string;
  name: string;
  persona: string;
  ailment_narrative: string;
  ailment_category: string;
  expected_recipe_slug: string;
  sprite: string;
};

export type BrewResult = {
  matched_recipe_slug: string | null;
  matched_recipe_name: string | null;
  matched_ailment_category: string | null;
  quality_score: number;
  ingredient_slugs: string[];
  description: string;
};

export type ServeResult = {
  outcome: "delighted" | "neutral" | "disappointed" | "confused";
  money_delta: number;
  new_money: number;
  customer_response: string;
};

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(`HTTP ${status}: ${detail}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const client = {
  getInventory: () => request<Ingredient[]>("/api/inventory"),
  getRecipes: () => request<Recipe[]>("/api/recipes"),
  getPlayer: () => request<{ money: number; brews_count: number }>("/api/player"),
  getNextCustomer: () => request<Customer | null>("/api/customers/next"),
  spawnCustomer: () =>
    request<Customer>("/api/customers/spawn", { method: "POST" }),
  brew: (ingredient_slugs: string[]) =>
    request<BrewResult>("/api/brew", {
      method: "POST",
      body: JSON.stringify({ ingredient_slugs }),
    }),
  serve: (customerId: string, ingredient_slugs: string[]) =>
    request<ServeResult>(`/api/customers/${customerId}/serve`, {
      method: "POST",
      body: JSON.stringify({ ingredient_slugs }),
    }),
};
