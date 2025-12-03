from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager

from app.config import get_settings
from app.schema import schema
from app.db.memgraph import get_db, close_db
from app.auth.api_key import verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: connection pool is created lazily
    yield
    # Shutdown: close database connections
    close_db()


# Create FastAPI app
app = FastAPI(
    title="GearGraph API",
    description="GraphQL API for outdoor gear knowledge graph",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Health check (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db = get_db()
        result = db.execute_query("RETURN 1 as ok")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)}
        )


# Stats endpoint (no auth required)
@app.get("/stats")
async def stats():
    """Quick stats about the database."""
    try:
        db = get_db()
        result = db.execute_query("""
            MATCH (g:GearItem) WITH count(g) as gear
            MATCH (b:OutdoorBrand) WITH gear, count(b) as brands
            MATCH (i:Insight) WITH gear, brands, count(i) as insights
            RETURN gear, brands, insights
        """)
        if result:
            row = result[0]
            return {
                "gearCount": row["gear"],
                "brandCount": row["brands"],
                "insightCount": row["insights"]
            }
        return {"error": "No data"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# GraphQL endpoint with API key protection
graphql_app = GraphQLRouter(
    schema,
    path="/graphql",
)


# Custom GraphQL route with auth
@app.api_route("/graphql", methods=["GET", "POST", "OPTIONS"])
async def graphql_with_auth(request: Request):
    """GraphQL endpoint with API key authentication."""
    # Skip auth for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await graphql_app.handle_request(request)
    
    # Skip auth for GraphQL Playground (GET requests in browser)
    if request.method == "GET":
        return await graphql_app.handle_request(request)
    
    # Verify API key for actual queries (POST)
    api_key = request.headers.get("X-API-Key")
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    return await graphql_app.handle_request(request)
