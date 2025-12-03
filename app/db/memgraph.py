from neo4j import GraphDatabase
from typing import Any
from app.config import get_settings

# Global driver instance
_driver = None


def get_driver():
    """Get or create the Neo4j/Memgraph driver."""
    global _driver
    if _driver is None:
        settings = get_settings()
        auth = None
        if settings.memgraph_user and settings.memgraph_password:
            auth = (settings.memgraph_user, settings.memgraph_password)
        _driver = GraphDatabase.driver(
            settings.memgraph_uri,
            auth=auth,
        )
    return _driver


def close_db():
    """Close the database connection."""
    global _driver
    if _driver:
        _driver.close()
        _driver = None


class MemgraphDB:
    """Wrapper for Memgraph database operations."""
    
    def __init__(self):
        self.driver = get_driver()
    
    def execute_query(
        self, 
        query: str, 
        parameters: dict[str, Any] | None = None
    ) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_single(
        self, 
        query: str, 
        parameters: dict[str, Any] | None = None
    ) -> dict | None:
        """Execute a query and return single result or None."""
        results = self.execute_query(query, parameters)
        return results[0] if results else None


# Singleton instance
_db_instance = None


def get_db() -> MemgraphDB:
    """Get the database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = MemgraphDB()
    return _db_instance
