import asyncio
import contextlib
import random
import time

import pytest

from apothecaria.domain.customer_queue import (
    CustomerStore,
    arrival_loop,
    load_templates,
    make_customer,
    pick_next_template,
)
from apothecaria.domain.models import CustomerInstance, CustomerTemplate


def test_load_templates_returns_six():
    templates = load_templates()
    assert len(templates) == 6
    assert all(isinstance(t, CustomerTemplate) for t in templates)
    slugs = {t.slug for t in templates}
    assert "weary_traveler" in slugs
    assert "muddled_scholar" in slugs


def test_pick_next_template_seeded_rng_is_deterministic():
    templates = load_templates()
    t1 = pick_next_template(random.Random(42), templates=templates)
    t2 = pick_next_template(random.Random(42), templates=templates)
    assert t1.slug == t2.slug


def test_make_customer_returns_unique_ids():
    template = load_templates()[0]
    a = make_customer(template)
    b = make_customer(template)
    assert a.id != b.id
    assert a.template_slug == template.slug


def test_store_add_and_get():
    store = CustomerStore()
    customer = make_customer(load_templates()[0])
    store.add(customer)
    assert store.get(customer.id) == customer
    assert store.size() == 1


def test_store_remove():
    store = CustomerStore()
    customer = make_customer(load_templates()[0])
    store.add(customer)
    store.remove(customer.id)
    assert store.get(customer.id) is None
    assert store.size() == 0


def test_store_get_oldest_returns_earliest_arrival():
    store = CustomerStore()
    a = make_customer(load_templates()[0])
    time.sleep(0.001)
    b = make_customer(load_templates()[1])
    store.add(b)
    store.add(a)
    oldest = store.get_oldest()
    assert oldest is not None and oldest.id == a.id


def test_get_oldest_empty_returns_none():
    store = CustomerStore()
    assert store.get_oldest() is None


@pytest.mark.asyncio
async def test_arrival_loop_calls_on_arrival_and_adds_to_store():
    store = CustomerStore()
    received: list[CustomerInstance] = []

    async def on_arrival(c) -> None:
        received.append(c)

    task = asyncio.create_task(
        arrival_loop(0.05, store=store, on_arrival=on_arrival, rng=random.Random(0))
    )
    try:
        await asyncio.sleep(0.16)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    assert len(received) >= 1
    assert store.size() == len(received)
