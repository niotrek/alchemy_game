import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apothecaria.api import brew as brew_api
from apothecaria.api import customers as customers_api
from apothecaria.api import inventory as inventory_api
from apothecaria.api import player as player_api
from apothecaria.api import recipes as recipes_api
from apothecaria.api import ws as ws_api
from apothecaria.config import settings
from apothecaria.db.seed import seed_database
from apothecaria.db.session import engine, init_db
from apothecaria.domain.customer_queue import CustomerStore, arrival_loop
from apothecaria.domain.models import CustomerInstance
from apothecaria.events.broadcaster import broadcaster


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    with engine.connect() as conn:
        seed_database(conn)

    store = CustomerStore()
    app.state.customer_store = store

    async def on_arrival(customer: CustomerInstance) -> None:
        await broadcaster.publish(
            {
                "type": "customer.arrived",
                "id": customer.id,
                "name": customer.name,
                "persona": customer.persona,
                "ailment_narrative": customer.ailment_narrative,
                "ailment_category": customer.ailment_category,
                "sprite": customer.sprite,
            }
        )

    task = asyncio.create_task(
        arrival_loop(
            interval_seconds=settings.customer_arrival_seconds,
            store=store,
            on_arrival=on_arrival,
        )
    )
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Apothecaria", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_api.router)
app.include_router(recipes_api.router)
app.include_router(customers_api.router)
app.include_router(brew_api.router)
app.include_router(player_api.router)
app.include_router(ws_api.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
