# database/operations/base_ops.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic

from ..models import Base

T = TypeVar('T', bound=Base)

class BaseOperations(Generic[T]):
    """Generic base class for database operations"""
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session
        
    def create(self, **kwargs) -> T:
        """Create a new record"""
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.commit()
        return obj
        
    def get_by_id(self, id: int) -> Optional[T]:
        """Get a record by ID"""
        return self.session.query(self.model).filter(self.model.id == id).first()
        
    def get_all(self) -> List[T]:
        """Get all records"""
        return self.session.query(self.model).all()
        
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        obj = self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.commit()
        return obj
        
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False