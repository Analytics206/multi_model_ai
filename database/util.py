#!/usr/bin/env python
# database/util.py
import argparse
import os
import sys
from pathlib import Path

# Add the project root to the path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db_connection, init_database
from database.seed import seed_database, register_api_key
from database.migration import run_migrations, create_alembic_config
from database.models import StorageType
from utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

def init_db_command():
    """Initialize the database (create tables)"""
    db = get_db_connection()
    db.init_db()
    db.create_tables()
    logger.info("Database initialized successfully")

def seed_db_command():
    """Seed the database with initial data"""
    seed_database()
    logger.info("Database seeded successfully")

def register_api_key_command(provider, key=None, storage_type='database', storage_path=None):
    """Register an API key for a provider"""
    from database.connection import get_db_session
    
    # Convert string storage type to enum
    try:
        st = StorageType(storage_type.lower())
    except ValueError:
        logger.error(f"Invalid storage type: {storage_type}")
        return False
    
    # If key is provided but storage type is not database, warn the user
    if key and st != StorageType.DATABASE:
        logger.warning(f"API key value provided but storage type is {st.value}. The key will not be stored in the database.")
    
    # If storage type is env or file but no path is provided, use default
    if st != StorageType.DATABASE and not storage_path:
        if st == StorageType.ENV:
            storage_path = f"{provider.upper()}_API_KEY"
            logger.info(f"No storage path provided. Using default environment variable: {storage_path}")
        elif st == StorageType.FILE:
            storage_path = f"./{provider.lower()}_api_key.txt"
            logger.info(f"No storage path provided. Using default file path: {storage_path}")
    
    # Register the key
    session = get_db_session()
    try:
        success = register_api_key(
            session,
            provider,
            key_value=key if st == StorageType.DATABASE else None,
            storage_type=st,
            storage_path=storage_path,
            is_default=True
        )
        
        if success:
            logger.info(f"API key for {provider} registered successfully")
        else:
            logger.error(f"Failed to register API key for {provider}")
    finally:
        session.close()

def reset_db_command():
    """Reset the database (drop and recreate tables)"""
    db = get_db_connection()
    
    confirm = input("This will delete all data in the database. Are you sure? (y/N): ")
    if confirm.lower() != 'y':
        logger.info("Database reset cancelled")
        return
    
    db.drop_tables()
    logger.info("Database tables dropped")
    
    db.create_tables()
    logger.info("Database tables recreated")
    
    logger.info("Database reset successfully")

def migrate_db_command(action='upgrade', revision='head'):
    """Run database migrations"""
    success = run_migrations(action=action, revision=revision)
    if success:
        logger.info(f"Migration '{action}' to '{revision}' completed successfully")
    else:
        logger.error(f"Migration '{action}' to '{revision}' failed")

def setup_alembic_command():
    """Set up Alembic for database migrations"""
    success = create_alembic_config()
    if success:
        logger.info("Alembic configuration created successfully")
    else:
        logger.error("Failed to set up Alembic configuration")

def list_providers_command():
    """List all registered providers"""
    from database.connection import get_db_session
    from database.operations import ProviderOperations
    
    session = get_db_session()
    try:
        provider_ops = ProviderOperations(session)
        providers = provider_ops.get_all()
        
        if not providers:
            logger.info("No providers found in the database")
            return
        
        print("\nRegistered Providers:")
        print("-" * 60)
        print(f"{'ID':<4} {'Name':<15} {'Type':<10} {'Enabled':<8} {'API Base URL':<30}")
        print("-" * 60)
        
        for p in providers:
            print(f"{p.id:<4} {p.name:<15} {p.provider_type.value:<10} {'Yes' if p.enabled else 'No':<8} {p.api_base_url or '':<30}")
        
        print("-" * 60)
    finally:
        session.close()

def list_models_command():
    """List all registered models"""
    from database.connection import get_db_session
    from database.operations import ModelOperations
    from sqlalchemy.orm import joinedload
    
    session = get_db_session()
    try:
        # Use raw query with join to get provider name
        models = (
            session.query("ai_models")
            .options(joinedload("provider"))
            .all()
        )
        
        if not models:
            logger.info("No models found in the database")
            return
        
        print("\nRegistered Models:")
        print("-" * 80)
        print(f"{'ID':<4} {'Model Key':<20} {'Display Name':<20} {'Provider':<12} {'Available':<10} {'Max Tokens':<12}")
        print("-" * 80)
        
        for m in models:
            provider_name = m.provider.name if m.provider else "Unknown"
            max_tokens = m.max_tokens or "N/A"
            print(f"{m.id:<4} {m.model_key:<20} {m.display_name:<20} {provider_name:<12} {'Yes' if m.is_available else 'No':<10} {max_tokens:<12}")
        
        print("-" * 80)
    finally:
        session.close()

def check_keys_command():
    """Check registered API keys"""
    from database.connection import get_db_session
    from database.operations import ApiKeyOperations, ProviderOperations
    from sqlalchemy.orm import joinedload
    
    session = get_db_session()
    try:
        # Get all keys with provider information
        keys = (
            session.query("api_keys")
            .options(joinedload("provider"))
            .all()
        )
        
        if not keys:
            logger.info("No API keys found in the database")
            return
        
        print("\nRegistered API Keys:")
        print("-" * 90)
        print(f"{'ID':<4} {'Provider':<15} {'Storage Type':<15} {'Storage Path':<30} {'Default':<8} {'Status':<10}")
        print("-" * 90)
        
        for k in keys:
            provider_name = k.provider.name if k.provider else "Unknown"
            
            # Check if the key is accessible (for ENV and FILE types)
            status = "Unknown"
            if k.storage_type == StorageType.DATABASE:
                status = "Stored" if k.key_value else "Empty"
            elif k.storage_type == StorageType.ENV:
                status = "Available" if k.storage_path and os.environ.get(k.storage_path) else "Missing"
            elif k.storage_type == StorageType.FILE:
                status = "Available" if k.storage_path and os.path.exists(k.storage_path) else "Missing"
            
            print(f"{k.id:<4} {provider_name:<15} {k.storage_type.value:<15} {k.storage_path or 'N/A':<30} {'Yes' if k.is_default else 'No':<8} {status:<10}")
        
        print("-" * 90)
    finally:
        session.close()

def main():
    """Main entry point for the database utility"""
    parser = argparse.ArgumentParser(description='Database utility for AI API Integration')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize the database')
    
    # seed command
    seed_parser = subparsers.add_parser('seed', help='Seed the database with initial data')
    
    # reset command
    reset_parser = subparsers.add_parser('reset', help='Reset the database (drop and recreate tables)')
    
    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run database migrations')
    migrate_parser.add_argument('--action', choices=['upgrade', 'downgrade', 'revision', 'current', 'history'], 
                              default='upgrade', help='Migration action to perform')
    migrate_parser.add_argument('--revision', default='head', help='Target revision for upgrade/downgrade')
    
    # setup-alembic command
    alembic_parser = subparsers.add_parser('setup-alembic', help='Set up Alembic for database migrations')
    
    # list-providers command
    providers_parser = subparsers.add_parser('list-providers', help='List all registered providers')
    
    # list-models command
    models_parser = subparsers.add_parser('list-models', help='List all registered models')
    
    # check-keys command
    keys_parser = subparsers.add_parser('check-keys', help='Check registered API keys')
    
    # register-key command
    register_parser = subparsers.add_parser('register-key', help='Register an API key for a provider')
    register_parser.add_argument('provider', help='Provider name (e.g., OpenAI, Anthropic)')
    register_parser.add_argument('--key', help='API key value (for database storage)')
    register_parser.add_argument('--storage', choices=['database', 'environment', 'file'], 
                               default='database', help='Storage type for the API key')
    register_parser.add_argument('--path', help='Storage path (environment variable name or file path)')
    
    # Parse args and run the appropriate command
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the requested command
    if args.command == 'init':
        init_db_command()
    elif args.command == 'seed':
        seed_db_command()
    elif args.command == 'reset':
        reset_db_command()
    elif args.command == 'migrate':
        migrate_db_command(args.action, args.revision)
    elif args.command == 'setup-alembic':
        setup_alembic_command()
    elif args.command == 'list-providers':
        list_providers_command()
    elif args.command == 'list-models':
        list_models_command()
    elif args.command == 'check-keys':
        check_keys_command()
    elif args.command == 'register-key':
        register_api_key_command(args.provider, args.key, args.storage, args.path)

if __name__ == "__main__":
    main()