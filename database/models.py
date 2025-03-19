# database/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import datetime
import json
from typing import Optional, Dict, Any, List

Base = declarative_base()

class ProviderType(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    CUSTOM = "custom"

class StorageType(enum.Enum):
    DATABASE = "database"
    ENV = "environment"
    FILE = "file"

class ModelProvider(Base):
    """Model for AI providers like OpenAI, Anthropic, Google, etc."""
    __tablename__ = "model_providers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    provider_type = Column(Enum(ProviderType), nullable=False)
    api_base_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="provider", cascade="all, delete-orphan")
    models = relationship("AIModel", back_populates="provider")
    
    def __repr__(self):
        return f"<ModelProvider(name='{self.name}', type='{self.provider_type}')>"

class ApiKey(Base):
    """Storage for API keys with option for encryption/secure storage"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("model_providers.id"), nullable=False)
    key_value = Column(String(255), nullable=True)  # Nullable to support external storage
    storage_type = Column(Enum(StorageType), nullable=False, default=StorageType.DATABASE)
    storage_path = Column(String(255), nullable=True)  # For FILE or ENV variable name
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    provider = relationship("ModelProvider", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey(provider='{self.provider.name if self.provider else None}', storage='{self.storage_type}')>"

class AIModel(Base):
    """AI Model details with provider association"""
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True)
    model_key = Column(String(100), nullable=False)  # API identifier (e.g., "gpt-4")
    display_name = Column(String(100), nullable=False)
    provider_id = Column(Integer, ForeignKey("model_providers.id"), nullable=False)
    version = Column(String(50), nullable=True)
    capabilities = Column(JSON, nullable=True)  # JSON of model capabilities
    max_tokens = Column(Integer, nullable=True)
    prompt_format = Column(Text, nullable=True)  # Template for formatting prompts
    input_cost_per_token = Column(Float, nullable=True)  # Cost in USD per 1K tokens
    output_cost_per_token = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    provider = relationship("ModelProvider", back_populates="models")
    prompt_transformations = relationship("PromptTransformation", back_populates="model")
    api_calls = relationship("ApiCallLog", back_populates="model")
    
    def __repr__(self):
        return f"<AIModel(key='{self.model_key}', provider='{self.provider.name if self.provider else None}')>"

class PromptTemplate(Base):
    """Store MCP (Multi-provider Compatible Prompt) templates"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    template_content = Column(Text, nullable=False)  # MCP format
    variables = Column(JSON, nullable=True)  # Required variables in JSON format
    tags = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transformations = relationship("PromptTransformation", back_populates="template")
    
    def __repr__(self):
        return f"<PromptTemplate(name='{self.name}')>"

class PromptTransformation(Base):
    """Cache for transformed prompts (MCP → provider-specific)"""
    __tablename__ = "prompt_transformations"
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    transformed_content = Column(Text, nullable=False)
    variables_used = Column(JSON, nullable=True)  # Variables used in this transformation
    hash = Column(String(64), nullable=False, index=True)  # Hash for caching
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    template = relationship("PromptTemplate", back_populates="transformations")
    model = relationship("AIModel", back_populates="prompt_transformations")
    
    def __repr__(self):
        return f"<PromptTransformation(template='{self.template.name if self.template else None}', model='{self.model.model_key if self.model else None}')>"

class ApiCallLog(Base):
    """Log of API calls to AI providers"""
    __tablename__ = "api_call_logs"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    request_id = Column(String(100), nullable=False, index=True)  # For tracking parallel requests
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # Might be NULL if failed
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    request_params = Column(JSON, nullable=True)  # Additional parameters sent
    cost_usd = Column(Float, nullable=True)  # Calculated cost
    user_id = Column(String(100), nullable=True)  # Optional user identifier
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    model = relationship("AIModel", back_populates="api_calls")
    
    def __repr__(self):
        return f"<ApiCallLog(model='{self.model.model_key if self.model else None}', request_id='{self.request_id}')>"

class ComparisonSession(Base):
    """Session for comparing multiple model responses"""
    __tablename__ = "comparison_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(100), nullable=True)
    prompt_original = Column(Text, nullable=False)
    models_compared = Column(JSON, nullable=False)  # List of model IDs being compared
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    responses = relationship("ComparisonResponse", back_populates="session", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ComparisonSession(id='{self.session_id}', models={self.models_compared})>"

class ComparisonResponse(Base):
    """Store individual model responses within a comparison session"""
    __tablename__ = "comparison_responses"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("comparison_sessions.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    api_call_id = Column(Integer, ForeignKey("api_call_logs.id"), nullable=True)
    response_text = Column(Text, nullable=False)
    response_metadata = Column(JSON, nullable=True)  # Timing, tokens, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ComparisonSession", back_populates="responses")
    model = relationship("AIModel")
    
    def __repr__(self):
        return f"<ComparisonResponse(session='{self.session_id}', model='{self.model.model_key if self.model else None}')>"

class UserFeedback(Base):
    """User feedback on comparison responses"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("comparison_sessions.id"), nullable=False)
    response_id = Column(Integer, ForeignKey("comparison_responses.id"), nullable=True)  # Nullable for session-level feedback
    rating = Column(Integer, nullable=True)  # e.g., 1-5 stars
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ComparisonSession", back_populates="feedback")
    
    def __repr__(self):
        return f"<UserFeedback(session='{self.session_id}', rating={self.rating})>"