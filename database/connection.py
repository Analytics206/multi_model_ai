# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from typing import Dict, Any, Optional

# Use relative imports for flexibility
try:
    from ..config import get_config
    from .models import Base
    from ..utils.logger import get_logger
except (ImportError, ValueError):
    # When running the module directly
    import sys
    from pathlib import Path
    
    # Add the project root to the path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from config import get_config
    from database.models import Base
    from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    """
    Database connection manager that handles SQLite and PostgreSQL connections
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = get_config().database
        self.engine = None
        self.session_factory = None
        self.Session = None
        self._initialized = True
        
    def init_db(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the database connection"""
        if config:
            self.config = config
        
        # Get DB connection string from config
        if self.config.get("type") == "postgres":
            # PostgreSQL connection
            conn_str = f"postgresql://{self.config.get('username')}:{self.config.get('password')}@{self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}"
        else:
            # Default to SQLite
            db_path = self.config.get("path", "database/ai_integration.db")
            conn_str = f"sqlite:///{db_path}"
            
        # Create engine and session factory
        self.engine = create_engine(
            conn_str, 
            echo=self.config.get("echo", False),
            pool_pre_ping=True
        )
        
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create scoped session for thread safety
        self.Session = scoped_session(self.session_factory)
        logger.info(f"Database initialized with {self.config.get('type', 'sqlite')} backend")
    
    def create_tables(self) -> None:
        """Create all tables defined in models"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self) -> None:
        """Drop all tables - USE WITH CAUTION"""
        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            self.init_db()
        return self.Session()
    
    def close_session(self, session) -> None:
        """Close a database session"""
        session.close()
    
    def dispose(self) -> None:
        """Dispose the engine connection pool"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")


# Singleton instance for database connection
db_connection = DatabaseConnection()

def get_db_connection() -> DatabaseConnection:
    """Get the database connection singleton"""
    return db_connection

def get_db_session():
    """Get a new database session"""
    return db_connection.get_session()

def init_database():
    """Initialize database and create tables"""
    db_connection.init_db()
    db_connection.create_tables()
    logger.info("Database initialized and tables created")