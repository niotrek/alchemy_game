from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IngredientSeed(BaseModel):
    """Schema for one row in content/ingredients.json."""

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    lore: str = ""
    sprite: str = ""


class RecipeSeed(BaseModel):
    """Schema for one row in content/recipes.json."""

    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    ailment_category: str = Field(min_length=1)
    lore: str = ""
    sprite: str = ""
    ingredients: list[str] = Field(min_length=1)


class CustomerTemplate(BaseModel):
    """One customer archetype loaded from content/customers.json."""

    slug: str
    name: str
    persona: str
    ailment_narrative: str
    ailment_category: str
    expected_recipe_slug: str
    patience_seconds: int = 60
    sprite: str = ""


class CustomerInstance(BaseModel):
    """A live customer in the in-memory store. Ephemeral — no DB persistence."""

    id: str
    template_slug: str
    name: str
    persona: str
    ailment_narrative: str
    ailment_category: str
    expected_recipe_slug: str
    sprite: str = ""
    arrived_at: datetime


class BrewResult(BaseModel):
    matched_recipe_slug: str | None
    matched_recipe_name: str | None
    matched_ailment_category: str | None
    quality_score: float = Field(ge=0.0, le=1.0)
    ingredient_slugs: list[str]
    description: str


class Outcome(StrEnum):
    DELIGHTED = "delighted"
    NEUTRAL = "neutral"
    DISAPPOINTED = "disappointed"
    CONFUSED = "confused"


class ServiceResult(BaseModel):
    outcome: Outcome
    money_delta: int
    new_money: int
    customer_response: str


class StoreSeed(BaseModel):
    """Schema for one row in content/store.json."""

    ingredient_slug: str = Field(min_length=1)
    price: int = Field(ge=1)
    stock: int = Field(ge=0)


class StoreItemView(BaseModel):
    """One purchasable item: an ingredient with its store price and stock."""

    slug: str
    name: str
    price: int
    stock: int


class PurchaseResult(BaseModel):
    """The outcome of a completed purchase from the store."""

    ingredient_slug: str
    ingredient_name: str
    quantity: int
    unit_price: int
    total_cost: int
    new_money: int
    new_quantity_owned: int
    remaining_stock: int
    message: str
