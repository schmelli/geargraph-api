"""GraphQL Resolvers - Database queries for each field."""

from typing import Optional
from app.db.memgraph import get_db
from app.schema import types as t


def resolve_all_brands() -> list[t.Brand]:
    """Fetch all brands from the database."""
    db = get_db()
    results = db.execute_query("""
        MATCH (b:OutdoorBrand)
        RETURN b.name as name,
               b.country as country,
               b.website as website,
               b.yearFounded as year_founded,
               b.description as description,
               b.bestKnownFor as best_known_for
        ORDER BY b.name
    """)
    return [
        t.Brand(
            id=row["name"],  # Using name as ID for now
            name=row["name"],
            country=row.get("country"),
            website=row.get("website"),
            year_founded=row.get("year_founded"),
            description=row.get("description"),
            best_known_for=row.get("best_known_for"),
        )
        for row in results
    ]


def resolve_all_categories() -> list[t.Category]:
    """Fetch category hierarchy from the database."""
    db = get_db()
    
    # Get categories with their product families
    results = db.execute_query("""
        MATCH (c:Category)
        OPTIONAL MATCH (pf:ProductFamily)-[:IN_CATEGORY]->(c)
        RETURN c.name as category,
               collect(DISTINCT pf.productType) as product_types
        ORDER BY c.name
    """)
    
    # For now, we return a flat structure
    # TODO: Implement proper 3-level hierarchy when data supports it
    categories = []
    for row in results:
        product_types = [
            t.ProductType(name=pt) 
            for pt in row.get("product_types", []) 
            if pt is not None
        ]
        categories.append(t.Category(
            name=row["category"],
            subcategories=[
                t.Subcategory(
                    name="All",  # Placeholder
                    product_types=product_types
                )
            ] if product_types else []
        ))
    
    return categories


def resolve_all_gear(
    filter: Optional[t.GearFilter], 
    limit: int, 
    offset: int
) -> list[t.GearItem]:
    """Fetch gear items with optional filtering."""
    db = get_db()
    
    # Build dynamic query based on filters
    where_clauses = []
    params = {"limit": limit, "offset": offset}
    
    if filter:
        if filter.brand_name:
            where_clauses.append("g.brand = $brand_name")
            params["brand_name"] = filter.brand_name
        if filter.product_type:
            where_clauses.append("g.productType = $product_type")
            params["product_type"] = filter.product_type
        if filter.category:
            where_clauses.append("g.category = $category")
            params["category"] = filter.category
        if filter.weight_grams_lt:
            where_clauses.append("g.weight_grams < $weight_lt")
            params["weight_lt"] = filter.weight_grams_lt
        if filter.weight_grams_gt:
            where_clauses.append("g.weight_grams > $weight_gt")
            params["weight_gt"] = filter.weight_grams_gt
        if filter.price_usd_lt:
            where_clauses.append("g.price_usd < $price_lt")
            params["price_lt"] = filter.price_usd_lt
        if filter.price_usd_gt:
            where_clauses.append("g.price_usd > $price_gt")
            params["price_gt"] = filter.price_usd_gt
        if filter.capacity_persons:
            where_clauses.append("g.capacityPersons = $capacity")
            params["capacity"] = filter.capacity_persons
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
        MATCH (g:GearItem)
        {where_clause}
        RETURN g
        ORDER BY g.name
        SKIP $offset
        LIMIT $limit
    """
    
    results = db.execute_query(query, params)
    return [_map_gear_item(row["g"]) for row in results]


def resolve_gear(
    gear_id: Optional[str], 
    name: Optional[str]
) -> Optional[t.GearItem]:
    """Fetch a single gear item by ID or name."""
    db = get_db()
    
    if gear_id:
        result = db.execute_single(
            "MATCH (g:GearItem {gearId: $id}) RETURN g",
            {"id": gear_id}
        )
    elif name:
        result = db.execute_single(
            "MATCH (g:GearItem) WHERE toLower(g.name) = toLower($name) RETURN g",
            {"name": name}
        )
    else:
        return None
    
    if not result:
        return None
    
    gear = _map_gear_item(result["g"])
    
    # Fetch insights for this gear item
    insights_result = db.execute_query("""
        MATCH (g:GearItem {gearId: $id})-[:HAS_TIP]->(i:Insight)
        RETURN i.summary as summary, 
               i.content as content,
               i.category as category,
               i.sourceUrl as source_url
    """, {"id": gear.gear_id})
    
    gear.insights = [
        t.Insight(
            summary=row["summary"],
            content=row["content"],
            category=row.get("category"),
            source_url=row.get("source_url"),
        )
        for row in insights_result
    ]
    
    return gear


def resolve_brand(name: str) -> Optional[t.Brand]:
    """Fetch a single brand by name."""
    db = get_db()
    result = db.execute_single("""
        MATCH (b:OutdoorBrand {name: $name})
        RETURN b.name as name,
               b.country as country,
               b.website as website,
               b.yearFounded as year_founded,
               b.description as description,
               b.bestKnownFor as best_known_for
    """, {"name": name})
    
    if not result:
        return None
    
    return t.Brand(
        id=result["name"],
        name=result["name"],
        country=result.get("country"),
        website=result.get("website"),
        year_founded=result.get("year_founded"),
        description=result.get("description"),
        best_known_for=result.get("best_known_for"),
    )


def resolve_autocomplete_gear(query: str, limit: int) -> list[t.GearItem]:
    """Search gear items by name prefix (case-insensitive)."""
    db = get_db()
    results = db.execute_query("""
        MATCH (g:GearItem)
        WHERE toLower(g.name) CONTAINS toLower($query)
        RETURN g
        ORDER BY 
            CASE WHEN toLower(g.name) STARTS WITH toLower($query) THEN 0 ELSE 1 END,
            g.name
        LIMIT $limit
    """, {"query": query, "limit": limit})
    
    return [_map_gear_item(row["g"]) for row in results]


def resolve_autocomplete_brands(query: str, limit: int) -> list[t.Brand]:
    """Search brands by name prefix (case-insensitive)."""
    db = get_db()
    results = db.execute_query("""
        MATCH (b:OutdoorBrand)
        WHERE toLower(b.name) CONTAINS toLower($query)
        RETURN b.name as name,
               b.country as country,
               b.website as website
        ORDER BY 
            CASE WHEN toLower(b.name) STARTS WITH toLower($query) THEN 0 ELSE 1 END,
            b.name
        LIMIT $limit
    """, {"query": query, "limit": limit})
    
    return [
        t.Brand(
            id=row["name"],
            name=row["name"],
            country=row.get("country"),
            website=row.get("website"),
        )
        for row in results
    ]


def resolve_find_alternatives(
    gear_id: str,
    filter: Optional[t.AlternativeFilter],
    limit: int
) -> list[t.GearItem]:
    """Find alternative gear items based on same product type and optional filters."""
    db = get_db()
    
    # First get the reference gear's product type
    ref = db.execute_single("""
        MATCH (g:GearItem {gearId: $id})
        RETURN g.productType as product_type, g.category as category
    """, {"id": gear_id})
    
    if not ref or not ref.get("product_type"):
        return []
    
    # Build filter conditions
    where_clauses = ["g.gearId <> $id"]
    params = {
        "id": gear_id, 
        "product_type": filter.product_type if filter and filter.product_type else ref["product_type"],
        "limit": limit
    }
    
    if filter:
        if filter.max_weight:
            where_clauses.append("g.weight_grams <= $max_weight")
            params["max_weight"] = filter.max_weight
        if filter.max_price:
            where_clauses.append("g.price_usd <= $max_price")
            params["max_price"] = filter.max_price
        if filter.capacity_persons:
            where_clauses.append("g.capacityPersons = $capacity")
            params["capacity"] = filter.capacity_persons
    
    where_clause = " AND ".join(where_clauses)
    
    results = db.execute_query(f"""
        MATCH (g:GearItem)
        WHERE g.productType = $product_type AND {where_clause}
        RETURN g
        ORDER BY g.weight_grams ASC
        LIMIT $limit
    """, params)
    
    return [_map_gear_item(row["g"]) for row in results]


def resolve_stats() -> t.Stats:
    """Get database statistics."""
    db = get_db()
    result = db.execute_single("""
        MATCH (g:GearItem) WITH count(g) as gear
        MATCH (b:OutdoorBrand) WITH gear, count(b) as brands
        MATCH (i:Insight) WITH gear, brands, count(i) as insights
        RETURN gear, brands, insights
    """)
    
    return t.Stats(
        gear_count=result["gear"] if result else 0,
        brand_count=result["brands"] if result else 0,
        insight_count=result["insights"] if result else 0,
    )


# === Helper Functions ===

def _map_gear_item(node: dict) -> t.GearItem:
    """Map a Memgraph node to a GearItem type."""
    return t.GearItem(
        gear_id=node.get("gearId", node.get("name", "")),
        name=node.get("name", ""),
        brand_name=node.get("brand", node.get("brandName", "")),
        product_type=node.get("productType"),
        category=node.get("category"),
        description=node.get("description"),
        weight_grams=node.get("weight_grams"),
        price_usd=node.get("price_usd"),
        volume_liters=node.get("volumeLiters"),
        capacity_persons=node.get("capacityPersons"),
        temp_rating_f=node.get("tempRatingF"),
        fill_power=node.get("fillPower"),
        r_value=node.get("rValue"),
        lumens=_parse_int(node.get("lumens")),
        fuel_type=node.get("fuelType"),
        waterproof_rating=node.get("waterproofRating"),
        materials=node.get("materials"),
        features=node.get("features"),
        product_url=node.get("productUrl"),
        image_url=node.get("imageUrl"),
    )


def _parse_int(value) -> Optional[int]:
    """Safely parse an integer from various types."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            # Handle strings like "500 lumens"
            return int(''.join(filter(str.isdigit, value)))
        except ValueError:
            return None
    return None
