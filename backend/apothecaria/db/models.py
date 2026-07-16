from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apothecaria.db.session import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    lore: Mapped[str] = mapped_column(Text, default="")
    sprite: Mapped[str] = mapped_column(String(255), default="")


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    ailment_category: Mapped[str] = mapped_column(String(50), index=True)
    lore: Mapped[str] = mapped_column(Text, default="")
    sprite: Mapped[str] = mapped_column(String(255), default="")

    ingredient_links: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredient_links")
    ingredient: Mapped[Ingredient] = relationship(lazy="joined")


class PlayerState(Base):
    __tablename__ = "player_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    money: Mapped[int] = mapped_column(Integer, default=100)
    brews_count: Mapped[int] = mapped_column(Integer, default=0)


class IngredientStore(Base):
    __tablename__ = "ingredient_store"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    price: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer, default=0)


class PlayerIngredient(Base):
    __tablename__ = "player_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingredient_slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class BrewHistory(Base):
    """One row per brew/serve event. Customer fields are snapshotted because
    customers are ephemeral (in-memory) — the customer object may be gone
    by the time anyone queries history.
    """

    __tablename__ = "brew_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ingredient_slugs: Mapped[str] = mapped_column(Text)
    matched_recipe_slug: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    customer_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    customer_ailment_category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    expected_recipe_slug: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    money_delta: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
