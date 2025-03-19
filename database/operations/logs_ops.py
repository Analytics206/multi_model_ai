# database/operations/logs_ops.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type
from datetime import datetime

from ..models import (
    Base,
    ApiCallLog,
    ComparisonSession,
    ComparisonResponse,
    UserFeedback
)
from .base_ops import BaseOperations

class ApiCallLogOperations(BaseOperations[ApiCallLog]):
    """Operations for API call logs"""
    
    def __init__(self, session: Session):
        super().__init__(ApiCallLog, session)
    
    def get_by_request_id(self, request_id: str) -> List[ApiCallLog]:
        """Get all API calls for a request ID"""
        return self.session.query(self.model).filter(self.model.request_id == request_id).all()
    
    def get_by_model(self, model_id: int, limit: int = 100) -> List[ApiCallLog]:
        """Get recent API calls for a model"""
        return (
            self.session.query(self.model)
            .filter(self.model.model_id == model_id)
            .order_by(self.model.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[ApiCallLog]:
        """Get recent API calls for a user"""
        return (
            self.session.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.timestamp.desc())
            .limit(limit)
            .all()
        )


class ComparisonSessionOperations(BaseOperations[ComparisonSession]):
    """Operations for comparison sessions"""
    
    def __init__(self, session: Session):
        super().__init__(ComparisonSession, session)
    
    def get_by_session_id(self, session_id: str) -> Optional[ComparisonSession]:
        """Get a session by its unique session ID"""
        return self.session.query(self.model).filter(self.model.session_id == session_id).first()
    
    def get_by_user(self, user_id: str, limit: int = 20) -> List[ComparisonSession]:
        """Get recent comparison sessions for a user"""
        return (
            self.session.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_with_responses(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session with all its responses"""
        session = self.get_by_session_id(session_id)
        if not session:
            return None
        
        # Get all responses for this session
        responses = (
            self.session.query(ComparisonResponse)
            .filter(ComparisonResponse.session_id == session.id)
            .all()
        )
        
        # Format result
        result = {
            "session": session,
            "responses": responses
        }
        
        return result


class ComparisonResponseOperations(BaseOperations[ComparisonResponse]):
    """Operations for comparison responses"""
    
    def __init__(self, session: Session):
        super().__init__(ComparisonResponse, session)
    
    def get_by_session(self, session_id: int) -> List[ComparisonResponse]:
        """Get all responses for a session"""
        return (
            self.session.query(self.model)
            .filter(self.model.session_id == session_id)
            .all()
        )


class UserFeedbackOperations(BaseOperations[UserFeedback]):
    """Operations for user feedback"""
    
    def __init__(self, session: Session):
        super().__init__(UserFeedback, session)
    
    def get_by_session(self, session_id: int) -> List[UserFeedback]:
        """Get all feedback for a session"""
        return (
            self.session.query(self.model)
            .filter(self.model.session_id == session_id)
            .all()
        )