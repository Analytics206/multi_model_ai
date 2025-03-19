# Database Module for Multi-Model AI API Integration System

This module implements the database schema and operations for the Multi-Model AI Integration system. It provides all the necessary components to store and manage AI model information, API keys, prompt templates, transformations, and interaction logs.

## Structure

- `__init__.py` - Module exports
- `connection.py` - Database connection management
- `models.py` - SQLAlchemy models for all entities
- `operations.py` - CRUD operations for each model
- `seed.py` - Seed data functions for development and testing
- `migration.py` - Database migration utilities using Alembic
- `util.py` - Command-line utility tool for managing the database

## Database Schema

The system uses the following tables:

1. **model_providers** - Information about AI providers (OpenAI, Anthropic, etc.)
2. **api_keys** - API keys for each provider with different storage options
3. **ai_models** - Details about specific AI models and their capabilities
4. **prompt_templates** - Multi-provider Compatible Prompt (MCP) templates
5. **prompt_transformations** - Cached transformed prompts for specific models
6. **api_call_logs** - Log of all API calls to AI providers
7. **comparison_sessions** - Sessions for comparing multiple model responses
8. **comparison_responses** - Individual model responses within a comparison session
9. **user_feedback** - User feedback on comparison responses

## Key Features

- **Secure API Key Management**: Store API keys in the database, environment variables, or files
- **Provider and Model Management**: Track different AI providers and their available models
- **Prompt Template Storage**: Store MCP-formatted prompts for transformation
- **Prompt Transformation Caching**: Cache transformed prompts to reduce processing time
- **Comparison System**: Track and compare responses from multiple models
- **Comprehensive Logging**: Log all API interactions for auditing and analysis
- **User Feedback Collection**: Gather user feedback on model responses

## Usage

### Database Initialization

```python
from database import init_database

# Initialize the database and create tables
init_database()
```

### Working with Models and Providers

```python
from database import get_db_session, ProviderOperations, ModelOperations

session = get_db_session()
try:
    # Get all available models from enabled providers
    model_ops = ModelOperations(session)
    available_models = model_ops.get_available_models()
    
    for model in available_models:
        print(f"{model.display_name} ({model.provider.name})")
finally:
    session.close()
```

### Managing API Keys

```python
from database import get_db_session, ApiKeyOperations, StorageType, register_api_key

session = get_db_session()
try:
    # Register an API key from environment variable
    register_api_key(
        session, 
        "OpenAI", 
        storage_type=StorageType.ENV, 
        storage_path="OPENAI_API_KEY"
    )
    
    # Get the default API key for a provider
    key_ops = ApiKeyOperations(session)
    default_key = key_ops.get_default_key(provider_id=1)
finally:
    session.close()
```

### Working with Prompt Templates and Transformations

```python
from database import get_db_session, PromptTemplateOperations, PromptTransformationOperations

session = get_db_session()
try:
    # Get a template by name
    template_ops = PromptTemplateOperations(session)
    template = template_ops.get_by_name("Simple Question")
    
    # Get a cached transformation or create a new one
    transform_ops = PromptTransformationOperations(session)
    variables = {"question": "What is the capital of France?"}
    
    # Try to get an existing transformation
    transformation = transform_ops.get_valid_transformation(
        template_id=template.id, 
        model_id=1,
        variables=variables
    )
    
    if not transformation:
        # Create a new transformation (normally done by the prompt engine)
        transformed_content = "What is the capital of France?"  # Simplified example
        transformation = transform_ops.create_transformation(
            template_id=template.id,
            model_id=1,
            transformed_content=transformed_content,
            variables=variables
        )
finally:
    session.close()
```

### Command-line Database Management

The `util.py` script provides command-line utilities for managing the database:

```bash
# Initialize the database
python -m database.util init

# Seed the database with initial data
python -m database.util seed

# Reset the database (drop and recreate tables)
python -m database.util reset

# List all registered providers
python -m database.util list-providers

# List all registered models
python -m database.util list-models

# Check registered API keys
python -m database.util check-keys

# Register an API key for a provider
python -m database.util register-key OpenAI --storage environment --path OPENAI_API_KEY
```

## Database Migration

This module supports database migrations using Alembic. To set up migrations:

```bash
# Set up Alembic for migrations
python -m database.util setup-alembic

# Create a new migration
python -m database.util migrate --action revision --revision "add_new_column"

# Apply migrations
python -m database.util migrate
```