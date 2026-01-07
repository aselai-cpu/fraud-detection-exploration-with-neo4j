"""
Neo4j Database Connection Manager
Handles database connections and session management.
"""

from neo4j import GraphDatabase, Session
from typing import Optional
import os
from dotenv import load_dotenv


class Neo4jConnection:
    """Singleton connection manager for Neo4j database"""

    _instance: Optional['Neo4jConnection'] = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._driver is None:
            load_dotenv()
            self._uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            self._user = os.getenv('NEO4J_USER', 'neo4j')
            self._password = os.getenv('NEO4J_PASSWORD', 'password')
            self.connect()

    def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            print(f"Successfully connected to Neo4j at {self._uri}")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            print("Neo4j connection closed")

    def get_session(self) -> Session:
        """Get a database session"""
        if not self._driver:
            self.connect()
        return self._driver.session()

    def verify_connectivity(self) -> bool:
        """Verify database connectivity"""
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 as num")
                return result.single()['num'] == 1
        except Exception as e:
            print(f"Connectivity check failed: {e}")
            return False

    def create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX account_id_idx IF NOT EXISTS FOR (a:Account) ON (a.account_id)",
            "CREATE INDEX customer_id_idx IF NOT EXISTS FOR (c:Customer) ON (c.customer_id)",
            "CREATE INDEX transaction_id_idx IF NOT EXISTS FOR (t:Transaction) ON (t.transaction_id)",
            "CREATE INDEX device_id_idx IF NOT EXISTS FOR (d:Device) ON (d.device_id)",
            "CREATE INDEX ip_address_idx IF NOT EXISTS FOR (ip:IPAddress) ON (ip.ip_address)",
            "CREATE INDEX merchant_id_idx IF NOT EXISTS FOR (m:Merchant) ON (m.merchant_id)",
            "CREATE INDEX fraud_ring_id_idx IF NOT EXISTS FOR (fr:FraudRing) ON (fr.ring_id)",
            "CREATE INDEX transaction_timestamp_idx IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp)",
            "CREATE INDEX transaction_flagged_idx IF NOT EXISTS FOR (t:Transaction) ON (t.is_flagged)",
        ]

        with self.get_session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    print(f"Created index: {index_query[:50]}...")
                except Exception as e:
                    print(f"Index creation warning: {e}")

    def clear_database(self):
        """Clear all data from database (use with caution!)"""
        with self.get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")

    def get_database_stats(self) -> dict:
        """Get database statistics"""
        with self.get_session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as label, count(*) as count
            """)
            stats = {}
            for record in result:
                label = record['label'][0] if record['label'] else 'Unknown'
                stats[label] = record['count']
            return stats
