import strawberry
from typing import Optional
from app.schema.resolvers import (
    resolve_all_brands,
    resolve_all_categories,
    resolve_all_gear,
    resolve_gear,
    resolve_brand,
    resolve_autocomplete_gear,
    resolve_autocomplete_brands,
    resolve_find_alternatives,
    resolve_stats,
)


# === Scalar Types ===

@strawberry.type
class Brand:
    id: str
    name: str
    country: Optional[str] = None
    website: Optional[str] = None
    year_founded: Optional[int] = None
    description: Optional[str] = None
    best_known_for: Optional[str] = None


@strawberry.type
class ProductType:
    name: str


@strawberry.type
class Subcategory:
    name: str
    product_types: list[ProductType]


@strawberry.type
class Category:
    name: str
    subcategories: list[Subcategory]


@strawberry.type
class Insight:
    summary: str
    content: str
    category: Optional[str] = None
    source_url: Optional[str] = None


@strawberry.type
class GearItem:
    gear_id: str
    name: str
    brand_name: str
    product_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    
    # Common specs
    weight_grams: Optional[int] = None
    price_usd: Optional[float] = None
    
    # Category-specific specs
    volume_liters: Optional[float] = None          # Backpacks
    capacity_persons: Optional[int] = None         # Tents
    temp_rating_f: Optional[int] = None            # Sleeping bags
    fill_power: Optional[int] = None               # Down products
    r_value: Optional[float] = None                # Sleeping pads
    lumens: Optional[int] = None                   # Headlamps
    fuel_type: Optional[str] = None                # Stoves
    waterproof_rating: Optional[str] = None        # Jackets
    
    # Lists
    materials: Optional[list[str]] = None
    features: Optional[list[str]] = None
    
    # URLs
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    
    # Nested (resolved separately)
    brand: Optional[Brand] = None
    insights: Optional[list[Insight]] = None


@strawberry.type
class Stats:
    gear_count: int
    brand_count: int
    insight_count: int


# === Input Types (Filters) ===

@strawberry.input
class GearFilter:
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    weight_grams_lt: Optional[int] = None
    weight_grams_gt: Optional[int] = None
    price_usd_lt: Optional[float] = None
    price_usd_gt: Optional[float] = None
    capacity_persons: Optional[int] = None


@strawberry.input
class AlternativeFilter:
    max_weight: Optional[int] = None
    max_price: Optional[float] = None
    capacity_persons: Optional[int] = None
    product_type: Optional[str] = None


# === Query Root ===

@strawberry.type
class Query:
    
    @strawberry.field
    def all_brands(self) -> list[Brand]:
        """Get all outdoor brands."""
        return resolve_all_brands()
    
    @strawberry.field
    def all_categories(self) -> list[Category]:
        """Get the full category hierarchy."""
        return resolve_all_categories()
    
    @strawberry.field
    def all_gear(
        self, 
        filter: Optional[GearFilter] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[GearItem]:
        """Get gear items with optional filtering and pagination."""
        return resolve_all_gear(filter, limit, offset)
    
    @strawberry.field
    def gear(
        self, 
        gear_id: Optional[str] = None, 
        name: Optional[str] = None
    ) -> Optional[GearItem]:
        """Get a single gear item by ID or name."""
        return resolve_gear(gear_id, name)
    
    @strawberry.field
    def brand(self, name: str) -> Optional[Brand]:
        """Get a single brand by name."""
        return resolve_brand(name)
    
    @strawberry.field
    def autocomplete_gear(
        self, 
        query: str, 
        limit: int = 10
    ) -> list[GearItem]:
        """Autocomplete search for gear items."""
        return resolve_autocomplete_gear(query, limit)
    
    @strawberry.field
    def autocomplete_brands(
        self, 
        query: str, 
        limit: int = 10
    ) -> list[Brand]:
        """Autocomplete search for brands."""
        return resolve_autocomplete_brands(query, limit)
    
    @strawberry.field
    def find_alternatives(
        self,
        gear_id: str,
        filter: Optional[AlternativeFilter] = None,
        limit: int = 10
    ) -> list[GearItem]:
        """Find alternative gear items based on product type and filters."""
        return resolve_find_alternatives(gear_id, filter, limit)
    
    @strawberry.field
    def stats(self) -> Stats:
        """Get database statistics."""
        return resolve_stats()
