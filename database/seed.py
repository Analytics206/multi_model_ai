# database/seed.py
from sqlalchemy.orm import Session
import os
from datetime import datetime
import json

from .models import (
    ModelProvider, 
    ApiKey, 
    AIModel, 
    PromptTemplate,
    ProviderType,
    StorageType
)
from .operations import (
    ProviderOperations,
    ApiKeyOperations,
    ModelOperations,
    PromptTemplateOperations
)
from .connection import get_db_session
from ..utils.logger import get_logger

logger = get_logger(__name__)

def seed_providers(session: Session) -> None:
    """Seed the database with common AI providers"""
    provider_ops = ProviderOperations(session)
    
    providers = [
        {
            "name": "OpenAI",
            "provider_type": ProviderType.OPENAI,
            "api_base_url": "https://api.openai.com/v1",
            "description": "Provider of GPT models including GPT-3.5 and GPT-4"
        },
        {
            "name": "Anthropic",
            "provider_type": ProviderType.ANTHROPIC,
            "api_base_url": "https://api.anthropic.com/v1",
            "description": "Provider of Claude models"
        },
        {
            "name": "Google",
            "provider_type": ProviderType.GOOGLE,
            "api_base_url": "https://generativelanguage.googleapis.com/v1beta",
            "description": "Provider of Gemini models"
        },
        {
            "name": "Cohere",
            "provider_type": ProviderType.COHERE,
            "api_base_url": "https://api.cohere.ai/v1",
            "description": "Provider of Command models"
        }
    ]
    
    for provider_data in providers:
        # Check if provider already exists
        if not provider_ops.get_by_name(provider_data["name"]):
            provider_ops.create(**provider_data)
            logger.info(f"Added provider: {provider_data['name']}")
    
    logger.info(f"Providers seeded successfully")


def seed_models(session: Session) -> None:
    """Seed the database with common AI models"""
    model_ops = ModelOperations(session)
    provider_ops = ProviderOperations(session)
    
    # Get provider IDs by name
    openai_provider = provider_ops.get_by_name("OpenAI")
    anthropic_provider = provider_ops.get_by_name("Anthropic")
    google_provider = provider_ops.get_by_name("Google")
    cohere_provider = provider_ops.get_by_name("Cohere")
    
    if not all([openai_provider, anthropic_provider, google_provider, cohere_provider]):
        logger.warning("Cannot seed models: One or more providers not found")
        return
    
    models = [
        # OpenAI models
        {
            "model_key": "gpt-4-turbo",
            "display_name": "GPT-4 Turbo",
            "provider_id": openai_provider.id,
            "version": "20240229",
            "capabilities": json.dumps({"chat": True, "function_calling": True, "vision": True}),
            "max_tokens": 128000,
            "prompt_format": "You are a helpful assistant.",
            "input_cost_per_token": 0.01,
            "output_cost_per_token": 0.03
        },
        {
            "model_key": "gpt-4",
            "display_name": "GPT-4",
            "provider_id": openai_provider.id,
            "version": "20231101",
            "capabilities": json.dumps({"chat": True, "function_calling": True}),
            "max_tokens": 8192,
            "prompt_format": "You are a helpful assistant.",
            "input_cost_per_token": 0.03,
            "output_cost_per_token": 0.06
        },
        {
            "model_key": "gpt-3.5-turbo",
            "display_name": "GPT-3.5 Turbo",
            "provider_id": openai_provider.id,
            "version": "20240229",
            "capabilities": json.dumps({"chat": True, "function_calling": True}),
            "max_tokens": 16385,
            "prompt_format": "You are a helpful assistant.",
            "input_cost_per_token": 0.0005,
            "output_cost_per_token": 0.0015
        },
        
        # Anthropic models
        {
            "model_key": "claude-3-opus-20240229",
            "display_name": "Claude 3 Opus",
            "provider_id": anthropic_provider.id,
            "version": "20240229",
            "capabilities": json.dumps({"chat": True, "vision": True}),
            "max_tokens": 200000,
            "prompt_format": "Human: {{prompt}}\n\nAssistant: ",
            "input_cost_per_token": 0.015,
            "output_cost_per_token": 0.075
        },
        {
            "model_key": "claude-3-sonnet-20240229",
            "display_name": "Claude 3 Sonnet",
            "provider_id": anthropic_provider.id,
            "version": "20240229",
            "capabilities": json.dumps({"chat": True, "vision": True}),
            "max_tokens": 200000,
            "prompt_format": "Human: {{prompt}}\n\nAssistant: ",
            "input_cost_per_token": 0.003,
            "output_cost_per_token": 0.015
        },
        {
            "model_key": "claude-3-haiku-20240307",
            "display_name": "Claude 3 Haiku",
            "provider_id": anthropic_provider.id,
            "version": "20240307",
            "capabilities": json.dumps({"chat": True, "vision": True}),
            "max_tokens": 200000,
            "prompt_format": "Human: {{prompt}}\n\nAssistant: ",
            "input_cost_per_token": 0.00025,
            "output_cost_per_token": 0.00125
        },
        
        # Google models
        {
            "model_key": "gemini-1.0-pro",
            "display_name": "Gemini 1.0 Pro",
            "provider_id": google_provider.id,
            "version": "1.0",
            "capabilities": json.dumps({"chat": True, "vision": True}),
            "max_tokens": 30720,
            "prompt_format": "",
            "input_cost_per_token": 0.0001,
            "output_cost_per_token": 0.0001
        },
        {
            "model_key": "gemini-1.5-pro-latest",
            "display_name": "Gemini 1.5 Pro",
            "provider_id": google_provider.id,
            "version": "1.5",
            "capabilities": json.dumps({"chat": True, "vision": True, "audio": True}),
            "max_tokens": 1000000,
            "prompt_format": "",
            "input_cost_per_token": 0.0001,
            "output_cost_per_token": 0.0001
        },
        
        # Cohere models
        {
            "model_key": "command-r-plus",
            "display_name": "Command R+",
            "provider_id": cohere_provider.id,
            "version": "2024-02",
            "capabilities": json.dumps({"chat": True, "rag": True}),
            "max_tokens": 4096,
            "prompt_format": "",
            "input_cost_per_token": 0.0005,
            "output_cost_per_token": 0.0015
        },
        {
            "model_key": "command-r",
            "display_name": "Command R",
            "provider_id": cohere_provider.id,
            "version": "2024-02",
            "capabilities": json.dumps({"chat": True, "rag": True}),
            "max_tokens": 4096,
            "prompt_format": "",
            "input_cost_per_token": 0.0001,
            "output_cost_per_token": 0.0003
        },
    ]
    
    for model_data in models:
        # Check if model already exists
        existing_model = model_ops.get_by_key(model_data["model_key"])
        if not existing_model:
            model_ops.create(**model_data)
            logger.info(f"Added model: {model_data['display_name']}")
        else:
            # Update existing model with new information
            model_ops.update(existing_model.id, **model_data)
            logger.info(f"Updated model: {model_data['display_name']}")
    
    logger.info(f"Models seeded successfully")


def seed_prompt_templates(session: Session) -> None:
    """Seed the database with common prompt templates in MCP format"""
    template_ops = PromptTemplateOperations(session)
    
    templates = [
        {
            "name": "Simple Question",
            "description": "A basic question-answering template",
            "template_content": """
                <mcp>
                <message role="system">
                You are a helpful assistant that provides accurate and concise answers to questions.
                </message>
                <message role="user">
                {{question}}
                </message>
                </mcp>
            """,
            "variables": json.dumps({"question": "The question to be answered"}),
            "tags": "general,question,simple"
        },
        {
            "name": "Creative Writing",
            "description": "Generate creative content based on a prompt",
            "template_content": """
                <mcp>
                <message role="system">
                You are a creative assistant with excellent writing skills. You can write stories, 
                poems, articles, and other creative content based on the given prompt.
                {{#if style}}Write in the style of {{style}}.{{/if}}
                {{#if tone}}Use a {{tone}} tone.{{/if}}
                {{#if length}}The content should be approximately {{length}} words long.{{/if}}
                </message>
                <message role="user">
                {{prompt}}
                </message>
                </mcp>
            """,
            "variables": json.dumps({
                "prompt": "The creative writing prompt",
                "style": "Optional writing style",
                "tone": "Optional tone of the content",
                "length": "Optional approximate word count"
            }),
            "tags": "creative,writing,story,poem,article"
        },
        {
            "name": "Code Generation",
            "description": "Generate code based on requirements",
            "template_content": """
                <mcp>
                <message role="system">
                You are an expert programmer with extensive knowledge in multiple programming languages.
                Provide well-documented, efficient, and clean code based on the requirements.
                {{#if language}}Write code in {{language}}.{{/if}}
                {{#if comments}}Include detailed comments: {{comments}}{{/if}}
                </message>
                <message role="user">
                {{requirements}}
                </message>
                </mcp>
            """,
            "variables": json.dumps({
                "requirements": "The code requirements or specifications",
                "language": "Optional programming language",
                "comments": "Optional level of code comments (minimal, moderate, detailed)"
            }),
            "tags": "code,programming,development"
        },
        {
            "name": "Comparison Analysis",
            "description": "Compare and analyze two or more items",
            "template_content": """
                <mcp>
                <message role="system">
                You are an analytical assistant that provides comprehensive comparisons.
                Compare the items objectively, highlighting similarities, differences, pros, and cons.
                {{#if criteria}}Focus on these criteria: {{criteria}}{{/if}}
                {{#if format}}Organize the comparison in this format: {{format}}{{/if}}
                </message>
                <message role="user">
                Please compare: {{items}}
                </message>
                </mcp>
            """,
            "variables": json.dumps({
                "items": "The items to be compared (comma separated)",
                "criteria": "Optional specific criteria for comparison",
                "format": "Optional output format (table, pros/cons, narrative)"
            }),
            "tags": "comparison,analysis,evaluation"
        },
        {
            "name": "Multi-turn Conversation",
            "description": "Template for handling multi-turn conversations",
            "template_content": """
                <mcp>
                <message role="system">
                {{system_prompt}}
                </message>
                {{#each conversation}}
                <message role="{{this.role}}">
                {{this.content}}
                </message>
                {{/each}}
                </mcp>
            """,
            "variables": json.dumps({
                "system_prompt": "The system instruction for the assistant",
                "conversation": "Array of conversation turns with role and content fields"
            }),
            "tags": "conversation,chat,multi-turn"
        }
    ]
    
    for template_data in templates:
        # Check if template already exists
        existing_template = template_ops.get_by_name(template_data["name"])
        if not existing_template:
            template_ops.create(**template_data)
            logger.info(f"Added prompt template: {template_data['name']}")
        else:
            # Update existing template
            template_ops.update(existing_template.id, **template_data)
            logger.info(f"Updated prompt template: {template_data['name']}")
    
    logger.info(f"Prompt templates seeded successfully")


def register_api_key(session: Session, provider_name: str, key_value: str = None, 
                   storage_type: StorageType = StorageType.DATABASE, 
                   storage_path: str = None, is_default: bool = True) -> bool:
    """
    Register an API key for a provider
    
    Args:
        session: Database session
        provider_name: Name of the provider (OpenAI, Anthropic, etc.)
        key_value: The actual API key (only stored if storage_type is DATABASE)
        storage_type: Type of storage (DATABASE, ENV, FILE)
        storage_path: Path or name for ENV/FILE storage types
        is_default: Whether this should be the default key
        
    Returns:
        Boolean indicating success
    """
    provider_ops = ProviderOperations(session)
    key_ops = ApiKeyOperations(session)
    
    # Find provider
    provider = provider_ops.get_by_name(provider_name)
    if not provider:
        logger.error(f"Provider '{provider_name}' not found")
        return False
    
    # For ENV and FILE types, we need a storage path
    if storage_type != StorageType.DATABASE and not storage_path:
        logger.error(f"Storage path required for {storage_type.value} storage type")
        return False
    
    # Create API key entry
    api_key = ApiKey(
        provider_id=provider.id,
        key_value=key_value if storage_type == StorageType.DATABASE else None,
        storage_type=storage_type,
        storage_path=storage_path,
        is_default=is_default
    )
    
    # If this is the default, unset any other default keys
    if is_default:
        session.query(ApiKey).filter(
            ApiKey.provider_id == provider.id,
            ApiKey.id != getattr(api_key, 'id', None)  # Skip if key has no ID yet
        ).update({"is_default": False})
    
    session.add(api_key)
    session.commit()
    
    logger.info(f"API key registered for {provider_name} (storage: {storage_type.value})")
    return True


def seed_database():
    """Main function to seed the database with initial data"""
    session = get_db_session()
    try:
        # Seed providers first
        seed_providers(session)
        
        # Seed models (depends on providers)
        seed_models(session)
        
        # Seed prompt templates
        seed_prompt_templates(session)
        
        # Example API key registration (for development/testing only)
        # In production, these would be set through the UI or ENV vars
        if os.environ.get("OPENAI_API_KEY"):
            register_api_key(
                session, 
                "OpenAI", 
                storage_type=StorageType.ENV, 
                storage_path="OPENAI_API_KEY"
            )
            
        if os.environ.get("ANTHROPIC_API_KEY"):
            register_api_key(
                session, 
                "Anthropic", 
                storage_type=StorageType.ENV, 
                storage_path="ANTHROPIC_API_KEY"
            )
            
        logger.info("Database seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()