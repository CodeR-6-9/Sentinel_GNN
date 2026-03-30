"""
Neo4j Database Connection Management

Context manager for Neo4j CARD database interactions with graceful fallback.
"""

import os
import logging
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# NEO4J CONNECTION MANAGEMENT
# ============================================================================

class Neo4jConnection:
    """Context manager for Neo4j database connections."""
    
    def __init__(self):
        """Initialize Neo4j credentials from environment variables."""
        # Fetch from .env; if missing, it will still try localhost as a last resort
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    def __enter__(self):
        """Establish connection on context entry."""
        try:
            if "+s" in self.uri:
                self.driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password), 
                    connection_timeout=5.0
                )
            else:
                # Standard local Neo4j usually doesn't use encryption
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    encrypted=False,
                    connection_timeout=5.0
                )
            
            self.driver.verify_connectivity()
            print(f"  ✅ Neo4j Connection Verified: {self.uri}")
            
        except (ServiceUnavailable, AuthError) as e:
            print(f"  ❌ Neo4j Connection Failed: {e}")
            logger.error(f"Neo4j connection failed: {e}")
            self.driver = None
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection on context exit."""
        if self.driver:
            self.driver.close()
    
    def query(self, cypher: str, parameters: dict = None) -> list[dict]:
        """Execute Cypher query and return results."""
        if not self.driver:
            logger.warning("Neo4j driver unavailable; returning empty results")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return []