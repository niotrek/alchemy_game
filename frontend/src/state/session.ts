import type { Customer } from "../api/client";

export type Session = {
  currentCustomer: Customer | null;
  cauldronContents: string[];
  money: number;
  ingredientQuantities: Record<string, number>;
};

type Listener = (state: Readonly<Session>) => void;

const state: Session = {
  currentCustomer: null,
  cauldronContents: [],
  money: 0,
  ingredientQuantities: {},
};

const listeners = new Set<Listener>();

export const session = {
  get(): Readonly<Session> {
    return state;
  },
  setCurrentCustomer(c: Customer | null): void {
    state.currentCustomer = c;
    notify();
  },
  addIngredient(slug: string): void {
    state.cauldronContents.push(slug);
    if (state.ingredientQuantities[slug] !== undefined) {
      state.ingredientQuantities[slug]--;
    }
    notify();
  },
  clearCauldron(): void {
    // Restore quantities for ingredients that were never brewed
    for (const slug of state.cauldronContents) {
      if (state.ingredientQuantities[slug] !== undefined) {
        state.ingredientQuantities[slug]++;
      }
    }
    state.cauldronContents = [];
    notify();
  },
  clearCauldronAfterBrew(): void {
    // Don't restore quantities — backend already consumed them
    state.cauldronContents = [];
    notify();
  },
  setMoney(value: number): void {
    state.money = value;
    notify();
  },
  setQuantities(quantities: Record<string, number>): void {
    state.ingredientQuantities = quantities;
    notify();
  },
  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    listener(state);
    return () => listeners.delete(listener);
  },
};

function notify(): void {
  listeners.forEach((l) => l(state));
}
