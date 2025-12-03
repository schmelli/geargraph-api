# GearGraph API

GraphQL API for the GearGraph knowledge base, powering the GearShack outdoor gear apps.

## Features

- **GraphQL API** with Strawberry + FastAPI
- **Memgraph** graph database backend
- **API Key authentication**
- **Docker deployment**

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app.main:app --reload --port 8080
```

### Docker

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f geargraph-api
```

## API Endpoints

- **GraphQL Playground**: `http://localhost:8080/graphql`
- **Health Check**: `http://localhost:8080/health`

## Authentication

All GraphQL requests require an API key in the header:

```
X-API-Key: your-api-key
```

## Example Queries

### Get all categories
```graphql
query {
  allCategories {
    name
    subcategories {
      name
      productTypes {
        name
      }
    }
  }
}
```

### Search gear with autocomplete
```graphql
query {
  autocompleteGear(query: "hubba", limit: 5) {
    gearId
    name
    brand {
      name
    }
  }
}
```

### Find alternatives
```graphql
query {
  findAlternatives(
    gearId: "xxx"
    filter: { maxWeight: 1500, maxPrice: 300 }
  ) {
    name
    weightGrams
    priceUsd
    brand { name }
  }
}
```

## License

Proprietary - GearShack
