#!/usr/bin/env python3
"""
Reset Database and Generate Fresh Data
Clears the Neo4j database and generates new sample data with fraud patterns.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.infrastructure.neo4j_connection import Neo4jConnection
from src.data_generator import FraudDataGenerator


def main():
    print("=" * 60)
    print("Fraud Detection System - Database Reset & Data Generation")
    print("=" * 60)
    print()

    # Step 1: Connect to database
    print("Step 1: Connecting to Neo4j database...")
    connection = Neo4jConnection()

    if not connection.verify_connectivity():
        print("ERROR: Cannot connect to Neo4j database!")
        print("Please ensure Neo4j is running and check your .env configuration.")
        sys.exit(1)

    print("✓ Successfully connected to Neo4j")
    print()

    # Step 2: Clear existing data
    print("Step 2: Clearing existing database...")
    print("WARNING: This will delete ALL data in the database!")

    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    connection.clear_database()
    print("✓ Database cleared")
    print()

    # Step 3: Create indexes
    print("Step 3: Creating database indexes...")
    connection.create_indexes()
    print("✓ Indexes created")
    print()

    # Step 4: Generate data
    print("Step 4: Generating sample data...")
    print("-" * 60)

    generator = FraudDataGenerator(fraud_percentage=0.15)  # 15% fraud rate

    generator.generate_complete_dataset(
        num_customers=100,
        num_transactions=1000
    )

    print("-" * 60)
    print()

    # Step 5: Summary
    print("=" * 60)
    print("DATA GENERATION SUMMARY")
    print("=" * 60)
    print(f"Customers Created:    {len(generator.customers)}")
    print(f"Accounts Created:     {len(generator.accounts)}")
    print(f"Merchants Created:    {len(generator.merchants)}")
    print(f"Devices Created:      {len(generator.devices)}")
    print(f"Fraud Percentage:     15%")
    print()

    # Get database stats
    print("Database Statistics:")
    stats = connection.get_database_stats()
    for label, count in stats.items():
        print(f"  {label}: {count}")

    print()
    print("=" * 60)
    print("✓ Database reset and data generation complete!")
    print()
    print("Next steps:")
    print("1. Start the web application: python -m src.web.app")
    print("2. Navigate to: http://localhost:5000")
    print("3. Click 'Run Fraud Detection' to calculate risk scores")
    print("=" * 60)


if __name__ == "__main__":
    main()
