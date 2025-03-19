# database/__init__.py
from .connection import (
    get_db_connection, 
    get_db_session, 
    init_database
)
from .models import (
    Base,
    ModelProvider,
    ApiKey,
    AIModel,
    PromptTemplate,
    PromptTransformation,
    ApiCallLog,
    ComparisonSession,
    ComparisonResponse,
    UserFeedback,
    ProviderType,
    StorageType
)
from .operations import (
    BaseOperations,
    ProviderOperations,
    ApiKeyOperations,
    ModelOperations,
    PromptTemplateOperations,
    PromptTransformationOperations,
    ApiCallLogOperations,
    ComparisonSessionOperations,
    ComparisonResponseOperations,
    UserFeedbackOperations
)
from .seed import (
    seed_database,
    seed_providers,
    seed_models,
    seed_prompt_templates,
    register_api_key
)
from .migration import (
    run_migrations,
    create_alembic_config
)

__all__ = [
    # Connection
    'get_db_connection', 'get_db_session', 'init_database',
    
    # Models
    'Base', 'ModelProvider', 'ApiKey', 'AIModel', 'PromptTemplate',
    'PromptTransformation', 'ApiCallLog', 'ComparisonSession',
    'ComparisonResponse', 'UserFeedback', 'ProviderType', 'StorageType',
    
    # Operations
    'BaseOperations', 'ProviderOperations', 'ApiKeyOperations', 'ModelOperations',
    'PromptTemplateOperations', 'PromptTransformationOperations', 'ApiCallLogOperations',
    'ComparisonSessionOperations', 'ComparisonResponseOperations', 'UserFeedbackOperations',
    
    # Seed
    'seed_database', 'seed_providers', 'seed_models', 'seed_prompt_templates', 'register_api_key',
    
    # Migration
    'run_migrations', 'create_alembic_config'
]