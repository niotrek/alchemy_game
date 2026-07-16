import { session } from "../state/session";

export type InventoryBar = {
  onBrew: (cb: () => void) => void;
  onClear: (cb: () => void) => void;
  onGrimoire: (cb: () => void) => void;
};

export function createInventoryBar(): InventoryBar {
  const root = document.getElementById("overlay-inventory-bar")!;
  let brewCb: (() => void) | null = null;
  let clearCb: (() => void) | null = null;
  let grimoireCb: (() => void) | null = null;

  function render(): void {
    const s = session.get();
    root.innerHTML = `
      <div class="card bar">
        <div class="bar-section">
          <span class="label">$</span>
          <span class="money">${s.money}</span>
        </div>
        <div class="bar-section flex-grow">
          <span class="label">Cauldron</span>
          <span class="contents">${
            s.cauldronContents.length === 0
              ? "<em>empty</em>"
              : s.cauldronContents.map(esc).join(" + ")
          }</span>
        </div>
        <div class="bar-section actions">
          <button id="bar-grimoire-btn" class="btn">Grimoire</button>
          <button id="bar-clear-btn" class="btn" ${s.cauldronContents.length === 0 ? "disabled" : ""}>Clear</button>
          <button id="bar-brew-btn" class="btn primary" ${s.cauldronContents.length === 0 ? "disabled" : ""}>Brew</button>
        </div>
      </div>
    `;
    document.getElementById("bar-brew-btn")!.addEventListener("click", () => brewCb?.());
    document.getElementById("bar-clear-btn")!.addEventListener("click", () => clearCb?.());
    document.getElementById("bar-grimoire-btn")!.addEventListener("click", () => grimoireCb?.());
  }

  session.subscribe(() => render());
  render();

  return {
    onBrew: (cb) => {
      brewCb = cb;
    },
    onClear: (cb) => {
      clearCb = cb;
    },
    onGrimoire: (cb) => {
      grimoireCb = cb;
    },
  };
}

function esc(s: string): string {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );
}
