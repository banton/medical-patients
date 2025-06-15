"""
API Key repository for database operations.

This module provides the repository pattern for API key management,
handling all database operations with proper error handling and
performance optimizations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc

from ..models.api_key import APIKey, DEMO_API_KEY_CONFIG


class APIKeyRepository:
    """Repository for API key database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db
    
    def create_api_key(
        self,
        name: str,
        email: Optional[str] = None,
        is_demo: bool = False,
        max_patients_per_request: int = 1000,
        max_requests_per_day: Optional[int] = None,
        max_requests_per_minute: int = 60,
        max_requests_per_hour: int = 1000,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> APIKey:
        """
        Create a new API key with specified limits.
        
        Args:
            name: Human-readable name for the key
            email: Contact email for the key owner
            is_demo: Whether this is a demo key with restrictions
            max_patients_per_request: Maximum patients per generation request
            max_requests_per_day: Daily request limit (None = unlimited)
            max_requests_per_minute: Per-minute request limit
            max_requests_per_hour: Per-hour request limit
            expires_at: Optional expiration date
            metadata: Additional key metadata
            
        Returns:
            Created APIKey instance
            
        Raises:
            IntegrityError: If key generation fails due to collision
        """
        # Generate secure API key
        key_prefix = "sk_demo_" if is_demo else "sk_live_"
        api_key_value = key_prefix + secrets.token_hex(28)  # 56 chars + prefix = 64 total
        
        # Create API key instance
        api_key = APIKey(
            key=api_key_value,
            name=name,
            email=email,
            is_demo=is_demo,
            max_patients_per_request=max_patients_per_request,
            max_requests_per_day=max_requests_per_day,
            max_requests_per_minute=max_requests_per_minute,
            max_requests_per_hour=max_requests_per_hour,
            expires_at=expires_at,
            key_metadata=metadata or {}
        )
        
        try:
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            return api_key
        except IntegrityError:
            self.db.rollback()
            # Extremely rare case of key collision - retry once
            api_key.key = key_prefix + secrets.token_hex(28)
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            return api_key
    
    def get_by_key(self, api_key: str) -> Optional[APIKey]:
        """
        Retrieve API key by key value.
        
        Args:
            api_key: The API key string to look up
            
        Returns:
            APIKey instance if found, None otherwise
        """
        return self.db.query(APIKey).filter(APIKey.key == api_key).first()
    
    def get_by_id(self, key_id: str) -> Optional[APIKey]:
        """
        Retrieve API key by UUID.
        
        Args:
            key_id: The UUID of the API key
            
        Returns:
            APIKey instance if found, None otherwise
        """
        return self.db.query(APIKey).filter(APIKey.id == key_id).first()
    
    def get_active_key(self, api_key: str) -> Optional[APIKey]:
        """
        Retrieve active, non-expired API key.
        
        Args:
            api_key: The API key string to look up
            
        Returns:
            APIKey instance if active and not expired, None otherwise
        """
        key = self.db.query(APIKey).filter(
            and_(
                APIKey.key == api_key,
                APIKey.is_active == True,
                or_(
                    APIKey.expires_at.is_(None),
                    APIKey.expires_at > datetime.utcnow()
                )
            )
        ).first()
        
        # Check if daily counters need reset
        if key and key.needs_daily_reset():
            key.reset_daily_counters()
            self.db.commit()
        
        return key
    
    def list_keys(
        self,
        active_only: bool = True,
        demo_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[APIKey]:
        """
        List API keys with filtering options.
        
        Args:
            active_only: If True, only return active keys
            demo_only: If True, only demo keys; if False, only live keys; if None, both
            limit: Maximum number of keys to return
            offset: Number of keys to skip
            
        Returns:
            List of APIKey instances
        """
        query = self.db.query(APIKey)
        
        if active_only:
            query = query.filter(APIKey.is_active == True)
        
        if demo_only is not None:
            query = query.filter(APIKey.is_demo == demo_only)
        
        return query.order_by(desc(APIKey.created_at)).offset(offset).limit(limit).all()
    
    def search_keys(self, search_term: str, limit: int = 50) -> List[APIKey]:
        """
        Search API keys by name or email.
        
        Args:
            search_term: Text to search for in name or email
            limit: Maximum number of results
            
        Returns:
            List of matching APIKey instances
        """
        search_pattern = f"%{search_term}%"
        return self.db.query(APIKey).filter(
            or_(
                APIKey.name.ilike(search_pattern),
                APIKey.email.ilike(search_pattern)
            )
        ).order_by(desc(APIKey.last_used_at)).limit(limit).all()
    
    def update_usage(self, api_key: APIKey, patients_generated: int) -> None:
        """
        Update usage statistics for an API key.
        
        Args:
            api_key: The APIKey instance to update
            patients_generated: Number of patients generated in this request
        """
        api_key.record_usage(patients_generated)
        self.db.commit()
    
    def increment_request_count(self, api_key: APIKey) -> None:
        """
        Increment request count for rate limiting tracking.
        
        Args:
            api_key: The APIKey instance to update
        """
        api_key.total_requests += 1
        api_key.daily_requests += 1
        api_key.last_used_at = datetime.utcnow()
        api_key.updated_at = datetime.utcnow()
        self.db.commit()
    
    def deactivate_key(self, key_id: str) -> bool:
        """
        Deactivate an API key.
        
        Args:
            key_id: UUID or key string to deactivate
            
        Returns:
            True if key was deactivated, False if not found
        """
        api_key = self.get_by_id(key_id) or self.get_by_key(key_id)
        if api_key:
            api_key.is_active = False
            api_key.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def activate_key(self, key_id: str) -> bool:
        """
        Reactivate an API key.
        
        Args:
            key_id: UUID or key string to activate
            
        Returns:
            True if key was activated, False if not found
        """
        api_key = self.get_by_id(key_id) or self.get_by_key(key_id)
        if api_key:
            api_key.is_active = True
            api_key.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def delete_key(self, key_id: str) -> bool:
        """
        Permanently delete an API key.
        
        Args:
            key_id: UUID or key string to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        api_key = self.get_by_id(key_id) or self.get_by_key(key_id)
        if api_key:
            self.db.delete(api_key)
            self.db.commit()
            return True
        return False
    
    def update_limits(
        self,
        key_id: str,
        max_patients_per_request: Optional[int] = None,
        max_requests_per_day: Optional[int] = None,
        max_requests_per_minute: Optional[int] = None,
        max_requests_per_hour: Optional[int] = None
    ) -> bool:
        """
        Update limits for an existing API key.
        
        Args:
            key_id: UUID or key string to update
            max_patients_per_request: New patient limit per request
            max_requests_per_day: New daily request limit
            max_requests_per_minute: New per-minute limit
            max_requests_per_hour: New per-hour limit
            
        Returns:
            True if key was updated, False if not found
        """
        api_key = self.get_by_id(key_id) or self.get_by_key(key_id)
        if not api_key:
            return False
        
        if max_patients_per_request is not None:
            api_key.max_patients_per_request = max_patients_per_request
        if max_requests_per_day is not None:
            api_key.max_requests_per_day = max_requests_per_day
        if max_requests_per_minute is not None:
            api_key.max_requests_per_minute = max_requests_per_minute
        if max_requests_per_hour is not None:
            api_key.max_requests_per_hour = max_requests_per_hour
        
        api_key.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def extend_expiration(self, key_id: str, days: int) -> bool:
        """
        Extend the expiration date of an API key.
        
        Args:
            key_id: UUID or key string to update
            days: Number of days to add to expiration
            
        Returns:
            True if key was updated, False if not found
        """
        api_key = self.get_by_id(key_id) or self.get_by_key(key_id)
        if not api_key:
            return False
        
        if api_key.expires_at:
            api_key.expires_at += timedelta(days=days)
        else:
            api_key.expires_at = datetime.utcnow() + timedelta(days=days)
        
        api_key.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated usage statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with usage statistics
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recently used keys
        recent_keys = self.db.query(APIKey).filter(
            APIKey.last_used_at >= since_date
        ).all()
        
        total_requests = sum(key.total_requests for key in recent_keys)
        total_patients = sum(key.total_patients_generated for key in recent_keys)
        
        # Get key counts
        total_keys = self.db.query(APIKey).count()
        active_keys = self.db.query(APIKey).filter(APIKey.is_active == True).count()
        demo_keys = self.db.query(APIKey).filter(APIKey.is_demo == True).count()
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "demo_keys": demo_keys,
            "live_keys": total_keys - demo_keys,
            "recently_used_keys": len(recent_keys),
            "total_requests_all_time": total_requests,
            "total_patients_all_time": total_patients,
            "period_days": days,
        }
    
    def cleanup_expired_keys(self, dry_run: bool = True) -> List[str]:
        """
        Find or remove expired API keys.
        
        Args:
            dry_run: If True, only return keys that would be deleted
            
        Returns:
            List of key names that were/would be deleted
        """
        expired_keys = self.db.query(APIKey).filter(
            and_(
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < datetime.utcnow()
            )
        ).all()
        
        key_names = [key.name for key in expired_keys]
        
        if not dry_run:
            for key in expired_keys:
                self.db.delete(key)
            self.db.commit()
        
        return key_names
    
    def create_demo_key_if_not_exists(self) -> APIKey:
        """
        Create the standard demo key if it doesn't exist.
        
        Returns:
            The demo APIKey instance (existing or newly created)
        """
        demo_key = self.get_by_key(DEMO_API_KEY_CONFIG["key"])
        if demo_key:
            return demo_key
        
        # Create demo key with hardcoded configuration
        demo_key = APIKey(
            key=DEMO_API_KEY_CONFIG["key"],
            name=DEMO_API_KEY_CONFIG["name"],
            email=DEMO_API_KEY_CONFIG["email"],
            is_demo=DEMO_API_KEY_CONFIG["is_demo"],
            max_patients_per_request=DEMO_API_KEY_CONFIG["max_patients_per_request"],
            max_requests_per_day=DEMO_API_KEY_CONFIG["max_requests_per_day"],
            max_requests_per_minute=DEMO_API_KEY_CONFIG["max_requests_per_minute"],
            max_requests_per_hour=DEMO_API_KEY_CONFIG["max_requests_per_hour"],
            key_metadata={"auto_created": True, "public_demo": True}
        )
        
        self.db.add(demo_key)
        self.db.commit()
        self.db.refresh(demo_key)
        return demo_key