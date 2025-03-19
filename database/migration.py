# database/migration.py
from alembic import command
from alembic.config import Config
import os
import sys
from pathlib import Path
import argparse

from ..utils.logger import get_logger

logger = get_logger(__name__)

def run_migrations(alembic_cfg_path: str = "alembic.ini", action: str = "upgrade", revision: str = "head"):
    """
    Run Alembic migrations
    
    Args:
        alembic_cfg_path: Path to alembic.ini configuration file
        action: Migration action to perform (upgrade, downgrade, revision, etc.)
        revision: Target revision for upgrade/downgrade actions
    """
    try:
        # Ensure the alembic config file exists
        if not os.path.exists(alembic_cfg_path):
            logger.error(f"Alembic config file not found at {alembic_cfg_path}")
            return False
            
        # Create an Alembic configuration object
        alembic_cfg = Config(alembic_cfg_path)
        
        # Perform the requested migration action
        if action == "upgrade":
            logger.info(f"Upgrading database to revision {revision}")
            command.upgrade(alembic_cfg, revision)
        elif action == "downgrade":
            logger.info(f"Downgrading database to revision {revision}")
            command.downgrade(alembic_cfg, revision)
        elif action == "revision":
            # Create a new migration revision
            message = f"Auto-generated migration {revision}"
            logger.info(f"Creating new migration: {message}")
            command.revision(alembic_cfg, message=message, autogenerate=True)
        elif action == "current":
            # Show current revision
            logger.info("Getting current database revision")
            command.current(alembic_cfg)
        elif action == "history":
            # Show migration history
            logger.info("Showing migration history")
            command.history(alembic_cfg)
        else:
            logger.error(f"Unsupported migration action: {action}")
            return False
            
        logger.info(f"Migration action '{action}' completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

def create_alembic_config():
    """
    Create initial Alembic configuration if it doesn't exist
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    migrations_dir = project_root / "migrations"
    alembic_ini = project_root / "alembic.ini"
    
    # Check if already exists
    if alembic_ini.exists():
        logger.info("Alembic configuration already exists")
        return
    
    try:
        # Create migrations directory if it doesn't exist
        if not migrations_dir.exists():
            migrations_dir.mkdir(parents=True)
            logger.info(f"Created migrations directory at {migrations_dir}")
        
        # Create a basic alembic.ini file
        with open(alembic_ini, 'w') as f:
            f.write("""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to migrations/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:migrations/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or colons.
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep.

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = sqlite:///database/ai_integration.db


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")
        logger.info(f"Created Alembic configuration at {alembic_ini}")
        
        # Initialize Alembic
        alembic_cfg = Config(str(alembic_ini))
        command.init(alembic_cfg, str(migrations_dir))
        logger.info(f"Initialized Alembic environment at {migrations_dir}")
        
        # Update the env.py file to import our models
        env_py = migrations_dir / "env.py"
        if env_py.exists():
            env_content = env_py.read_text()
            
            # Insert imports for our models
            import_line = "from database.models import Base"
            if import_line not in env_content:
                modified_content = env_content.replace(
                    "target_metadata = None",
                    f"import sys\nimport os\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n{import_line}\ntarget_metadata = Base.metadata"
                )
                env_py.write_text(modified_content)
                logger.info("Updated env.py with model imports")
        
        logger.info("Alembic setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create Alembic configuration: {str(e)}")
        return False

def main():
    """Command-line interface for database migrations"""
    parser = argparse.ArgumentParser(description='Database migration tool')
    parser.add_argument('--action', choices=['upgrade', 'downgrade', 'revision', 'current', 'history', 'init'], 
                        default='upgrade', help='Migration action to perform')
    parser.add_argument('--revision', default='head', help='Target revision for upgrade/downgrade')
    parser.add_argument('--message', help='Migration message (for revision creation)')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        # Initialize Alembic configuration
        create_alembic_config()
    else:
        # Run the specified migration action
        revision = args.revision
        if args.action == 'revision' and args.message:
            revision = args.message
            
        run_migrations(action=args.action, revision=revision)

if __name__ == "__main__":
    main()