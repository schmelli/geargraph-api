import strawberry
from app.schema.types import Query

schema = strawberry.Schema(query=Query)
