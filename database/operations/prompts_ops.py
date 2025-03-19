# database/operations/prompts_ops.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type
import hashlib
import json
from datetime import datetime, timedelta

from ..models import (
    Base,
    PromptTemplate,
    PromptTransformation
)
from .base_ops import BaseOperations

class PromptTemplateOperations(BaseOperations[PromptTemplate]):
    """Operations for prompt templates"""
    
    def __init__(self, session: Session):
        super().__init__(PromptTemplate, session)
    
    def get_by_name(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name"""
        return self.session.query(self.model).filter(self.model.name == name).first()
    
    def get_by_tags(self, tags: List[str]) -> List[PromptTemplate]:
        """Get templates by tags (using LIKE for each tag)"""
        query = self.session.query(self.model)
        for tag in tags:
            query = query.filter(self.model.tags.like(f"%{tag}%"))
        return query.all()


class PromptTransformationOperations(BaseOperations[PromptTransformation]):
    """Operations for prompt transformations"""
    
    def __init__(self, session: Session):
        super().__init__(PromptTransformation, session)
    
    def get_by_hash(self, hash_value: str) -> Optional[PromptTransformation]:
        """Get a transformation by its hash"""
        return self.session.query(self.model).filter(self.model.hash == hash_value).first()
    
    def get_valid_transformation(self, template_id: int, model_id: int, variables: Dict[str, Any]) -> Optional[PromptTransformation]:
        """Get a valid (non-expired) transformation for a template/model/variables combination"""
        # Create a hash based on template, model and variables
        hash_data = f"{template_id}:{model_id}:{json.dumps(variables, sort_keys=True)}"
        hash_value = hashlib.sha256(hash_data.encode()).hexdigest()
        
        # Try to find a valid transformation
        now = datetime.utcnow()
        transformation = (
            self.session.query(self.model)
            .filter(
                self.model.hash == hash_value,
                self.model.template_id == template_id,
                self.model.model_id == model_id,
                (self.model.expires_at.is_(None) | (self.model.expires_at > now))
            )
            .first()
        )
        
        return transformation
    
    def create_transformation(self, template_id: int, model_id: int, transformed_content: str, variables: Dict[str, Any], ttl_hours: int = 24) -> PromptTransformation:
        """Create a new prompt transformation with expiration"""
        # Create a hash based on template, model and variables
        hash_data = f"{template_id}:{model_id}:{json.dumps(variables, sort_keys=True)}"
        hash_value = hashlib.sha256(hash_data.encode()).hexdigest()
        
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours) if ttl_hours > 0 else None
        
        # Create the transformation
        transformation = PromptTransformation(
            template_id=template_id,
            model_id=model_id,
            transformed_content=transformed_content,
            variables_used=variables,
            hash=hash_value,
            expires_at=expires_at
        )
        
        self.session.add(transformation)
        self.session.commit()
        return transformation