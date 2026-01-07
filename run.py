#!/usr/bin/env python3
"""
Fraud Detection System - Main Entry Point
Provides convenient commands to run different parts of the system.
"""

import sys
import argparse
from src.infrastructure.neo4j_connection import Neo4jConnection


def check_neo4j_connection():
    """Check if Neo4j is accessible"""
    try:
        conn = Neo4jConnection()
        if conn.verify_connectivity():
            print("✓ Neo4j connection successful")
            return True
        else:
            print("✗ Neo4j connection failed")
            return False
    except Exception as e:
        print(f"✗ Neo4j connection error: {e}")
        print("\nPlease ensure:")
        print("  1. Neo4j is installed and running")
        print("  2. Connection details in .env are correct")
        print("  3. Port 7687 is accessible")
        return False


def setup_database():
    """Set up database indexes"""
    print("Setting up database indexes...")
    try:
        conn = Neo4jConnection()
        conn.create_indexes()
        print("✓ Database indexes created")
        return True
    except Exception as e:
        print(f"✗ Database setup error: {e}")
        return False


def generate_data():
    """Generate sample data"""
    print("\nGenerating sample fraud detection data...")
    print("This will create:")
    print("  - 100 customers")
    print("  - ~200 accounts")
    print("  - ~1000 transactions")
    print("  - Embedded fraud patterns")
    print()

    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    try:
        from src.data_generator import main as generate_main
        generate_main()
        print("\n✓ Sample data generated successfully")
    except Exception as e:
        print(f"\n✗ Data generation error: {e}")
        import traceback
        traceback.print_exc()


def run_web_app():
    """Start the web application"""
    print("\nStarting Fraud Detection System...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")

    try:
        from src.web.app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"\n✗ Web application error: {e}")
        import traceback
        traceback.print_exc()


def show_stats():
    """Show database statistics"""
    try:
        conn = Neo4jConnection()
        stats = conn.get_database_stats()

        print("\nDatabase Statistics:")
        print("=" * 40)
        for label, count in stats.items():
            print(f"  {label:20} {count:>10,}")
        print("=" * 40)
    except Exception as e:
        print(f"✗ Error getting stats: {e}")


def clear_database():
    """Clear all data from database"""
    print("\n⚠️  WARNING: This will DELETE ALL DATA from the database!")
    confirm = input("Are you sure? Type 'DELETE' to confirm: ")

    if confirm != 'DELETE':
        print("Cancelled.")
        return

    try:
        conn = Neo4jConnection()
        conn.clear_database()
        print("✓ Database cleared")
    except Exception as e:
        print(f"✗ Error clearing database: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Fraud Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py check          # Check Neo4j connection
  python run.py setup          # Set up database indexes
  python run.py generate       # Generate sample data
  python run.py start          # Start web application
  python run.py stats          # Show database statistics
  python run.py clear          # Clear all database data

Quick Start:
  1. python run.py check       # Verify Neo4j is running
  2. python run.py setup       # Create indexes
  3. python run.py generate    # Generate sample data
  4. python run.py start       # Start the application
        """
    )

    parser.add_argument(
        'command',
        choices=['check', 'setup', 'generate', 'start', 'stats', 'clear'],
        help='Command to execute'
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    print("=" * 60)
    print("  Fraud Detection System - Graph DB Knowledge Discovery")
    print("=" * 60)

    if args.command == 'check':
        check_neo4j_connection()

    elif args.command == 'setup':
        if check_neo4j_connection():
            setup_database()

    elif args.command == 'generate':
        if check_neo4j_connection():
            generate_data()

    elif args.command == 'start':
        if check_neo4j_connection():
            run_web_app()

    elif args.command == 'stats':
        if check_neo4j_connection():
            show_stats()

    elif args.command == 'clear':
        if check_neo4j_connection():
            clear_database()


if __name__ == '__main__':
    main()
