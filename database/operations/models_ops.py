# database/operations/models_ops.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type
import hashlib
import json
from datetime import datetime

from ..models import (
    Base,
    ModelProvider,
    ApiKey,
    AIModel,
    ProviderType,
    StorageType
)
from .base_ops import BaseOperations

class ProviderOperations(BaseOperations[ModelProvider]):
    """Operations for AI providers"""
    
    def __init__(self, session: Session):
        super().__init__(ModelProvider, session)
    
    def get_by_name(self, name: str) -> Optional[ModelProvider]:
        """Get a provider by name"""
        return self.session.query(self.model).filter(self.model.name == name).first()
    
    def get_enabled_providers(self) -> List[ModelProvider]:
        """Get all enabled providers"""
        return self.session.query(self.model).filter(self.model.enabled == True).all()


class ApiKeyOperations(BaseOperations[ApiKey]):
    """Operations for API keys"""
    
    def __init__(self, session: Session):
        super().__init__(ApiKey, session)
    
    def get_by_provider(self, provider_id: int) -> List[ApiKey]:
        """Get all API keys for a provider"""
        return self.session.query(self.model).filter(self.model.provider_id == provider_id).all()
    
    def get_default_key(self, provider_id: int) -> Optional[ApiKey]:
        """Get the default API key for a provider"""
        return self.session.query(self.model).filter(
            self.model.provider_id == provider_id,
            self.model.is_default == True
        ).first()
    
    def set_as_default(self, key_id: int) -> Optional[ApiKey]:
        """Set an API key as the default for its provider"""
        key = self.get_by_id(key_id)
        if not key:
            return None
        
        # Reset all other keys for this provider
        self.session.query(self.model).filter(
            self.model.provider_id == key.provider_id,
            self.model.id != key_id
        ).update({"is_default": False})
        
        # Set this key as default
        key.is_default = True
        self.session.commit()
        return key


class ModelOperations(BaseOperations[AIModel]):
    """Operations for AI models"""
    
    def __init__(self, session: Session):
        super().__init__(AIModel, session)
    
    def get_by_key(self, model_key: str) -> Optional[AIModel]:
        """Get a model by its API key identifier"""
        return self.session.query(self.model).filter(self.model.model_key == model_key).first()
    
    def get_by_provider(self, provider_id: int) -> List[AIModel]:
        """Get all models for a provider"""
        return self.session.query(self.model).filter(self.model.provider_id == provider_id).all()
    
    def get_available_models(self) -> List[AIModel]:
        """Get all available models"""
        return (
            self.session.query(self.model)
            .join(ModelProvider)
            .filter(self.model.is_available == True, ModelProvider.enabled == True)
            .all()
        )