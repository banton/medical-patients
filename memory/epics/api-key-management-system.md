# EPIC-002: API Key Management System

## 🎯 Epic Overview
**Epic ID**: EPIC-002  
**Priority**: High (Priority 1)  
**Status**: Design Complete, Not Implemented  
**Duration**: 2 weeks  

### Description
Implement a comprehensive API key management system to enable multi-tenant access, usage tracking, rate limiting, and provide a public demo API key for the Medical Patients Generator.

### Business Value
- **Multi-Tenancy**: Support multiple clients with isolated access
- **Usage Tracking**: Monitor and bill based on actual usage
- **Public Access**: Demo key allows potential users to test the API
- **Security**: Individual rate limits and access controls per client
- **Analytics**: Detailed usage insights for capacity planning

## 📋 Epic Scope

### In Scope ✅
1. **API Key Infrastructure**
   - Database models for key storage
   - Key generation and validation
   - Usage tracking and limits
   - Expiration support

2. **Public Demo Access**
   - Hardcoded demo key with 50-patient limit
   - Rate-limited access (10 req/min, 100/day)
   - No registration required
   - Prominent display in UI

3. **Management Tools**
   - CLI for key administration
   - Usage statistics and reporting
   - Key lifecycle management
   - Bulk operations support

4. **Security Enhancements**
   - Per-key rate limiting
   - Request/patient count limits
   - Automatic key rotation
   - Audit logging

### Out of Scope ❌
- Web-based admin dashboard (future enhancement)
- Billing system integration
- OAuth/JWT authentication
- Third-party identity providers
- Webhook notifications

## 🏗️ Technical Design

### 1. Database Schema

#### API Keys Table
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_demo BOOLEAN DEFAULT false,
    
    -- Usage limits
    max_patients_per_request INTEGER DEFAULT 1000,
    max_requests_per_day INTEGER,
    max_requests_per_minute INTEGER DEFAULT 60,
    max_requests_per_hour INTEGER DEFAULT 1000,
    
    -- Usage tracking
    total_requests INTEGER DEFAULT 0,
    total_patients_generated INTEGER DEFAULT 0,
    daily_requests INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_api_keys_key (key),
    INDEX idx_api_keys_active (is_active),
    INDEX idx_api_keys_email (email)
);
```

### 2. Core Models

#### API Key Model
```python
# src/domain/models/api_key.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_demo = Column(Boolean, default=False)
    
    # Usage limits
    max_patients_per_request = Column(Integer, default=1000)
    max_requests_per_day = Column(Integer)
    max_requests_per_minute = Column(Integer, default=60)
    max_requests_per_hour = Column(Integer, default=1000)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    total_patients_generated = Column(Integer, default=0)
    daily_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    last_reset_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default=dict)
```

### 3. Enhanced Security Module

#### API Key Context
```python
# src/core/security_enhanced.py
from dataclasses import dataclass
from typing import Optional
import secrets

# Public demo key - hardcoded for easy access
DEMO_API_KEY = "DEMO_MILMED_2025_50_PATIENTS"

@dataclass
class APIKeyContext:
    """Rich context object for API key validation."""
    api_key: APIKey
    is_demo: bool = False
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    
    def check_patient_limit(self, requested: int) -> None:
        """Verify request doesn't exceed patient limit."""
        if requested > self.api_key.max_patients_per_request:
            raise HTTPException(
                status_code=400,
                detail=f"Requested {requested} patients exceeds limit of "
                       f"{self.api_key.max_patients_per_request}"
            )
    
    def check_daily_limit(self) -> None:
        """Verify daily request limit not exceeded."""
        if self.api_key.max_requests_per_day:
            if self.api_key.daily_requests >= self.api_key.max_requests_per_day:
                raise HTTPException(
                    status_code=429,
                    detail="Daily request limit exceeded"
                )

async def verify_api_key(
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> APIKeyContext:
    """Enhanced API key verification with context."""
    # Check for demo key
    if api_key == DEMO_API_KEY:
        return await get_demo_key_context(db, redis)
    
    # Look up key in database
    key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not key_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Check expiration
    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="API key expired"
        )
    
    # Create context with rate limit info
    context = APIKeyContext(
        api_key=key_record,
        is_demo=key_record.is_demo
    )
    
    # Check rate limits if Redis available
    if redis:
        await check_rate_limits(context, redis)
    
    return context
```

### 4. Rate Limiting Middleware

```python
# src/api/v1/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

class APIKeyRateLimiter(BaseHTTPMiddleware):
    """Per-API-key rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)
        
        # Check rate limits in Redis
        redis = request.app.state.redis
        if redis:
            # Per-minute limiting
            minute_key = f"rate:minute:{api_key}:{int(time.time() / 60)}"
            minute_count = await redis.incr(minute_key)
            await redis.expire(minute_key, 60)
            
            # Get limit from context (would be cached)
            limit = await get_api_key_minute_limit(api_key)
            
            if minute_count > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() / 60) * 60 + 60),
                        "Retry-After": str(60 - int(time.time() % 60))
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        if redis and limit:
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - minute_count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() / 60) * 60 + 60)
        
        return response
```

### 5. CLI Management Tool

```python
# scripts/manage_api_keys.py
import click
from tabulate import tabulate
import secrets

@click.group()
def cli():
    """API Key Management Tool"""
    pass

@cli.command()
@click.option('--name', required=True, help='Client name')
@click.option('--email', help='Contact email')
@click.option('--demo', is_flag=True, help='Create demo key')
@click.option('--patient-limit', default=1000, help='Max patients per request')
@click.option('--daily-limit', help='Max requests per day')
@click.option('--expire-days', help='Days until expiration')
def create(name, email, demo, patient_limit, daily_limit, expire_days):
    """Create a new API key."""
    # Generate secure key
    api_key = f"sk_{'demo' if demo else 'live'}_" + secrets.token_hex(28)
    
    with get_db() as db:
        key = APIKey(
            key=api_key,
            name=name,
            email=email,
            is_demo=demo,
            max_patients_per_request=patient_limit,
            max_requests_per_day=daily_limit,
            expires_at=datetime.utcnow() + timedelta(days=expire_days) if expire_days else None
        )
        db.add(key)
        db.commit()
        
        click.echo(f"Created API key: {api_key}")
        click.echo(f"Name: {name}")
        if demo:
            click.echo("Type: DEMO (limited access)")

@cli.command()
@click.option('--active/--all', default=True, help='Show only active keys')
def list(active):
    """List all API keys."""
    with get_db() as db:
        query = db.query(APIKey)
        if active:
            query = query.filter(APIKey.is_active == True)
        
        keys = query.all()
        
        table_data = []
        for key in keys:
            table_data.append([
                key.name,
                key.key[:20] + "...",
                "✓" if key.is_active else "✗",
                "DEMO" if key.is_demo else "LIVE",
                key.total_requests,
                key.total_patients_generated,
                key.last_used_at.strftime("%Y-%m-%d") if key.last_used_at else "Never"
            ])
        
        headers = ["Name", "Key", "Active", "Type", "Requests", "Patients", "Last Used"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@cli.command()
@click.argument('key_id')
def show(key_id):
    """Show detailed information about an API key."""
    with get_db() as db:
        key = db.query(APIKey).filter(
            (APIKey.key == key_id) | (APIKey.id == key_id)
        ).first()
        
        if not key:
            click.echo("API key not found", err=True)
            return
        
        info = [
            ["ID", str(key.id)],
            ["Key", key.key],
            ["Name", key.name],
            ["Email", key.email or "N/A"],
            ["Status", "Active" if key.is_active else "Inactive"],
            ["Type", "DEMO" if key.is_demo else "LIVE"],
            ["Created", key.created_at.strftime("%Y-%m-%d %H:%M:%S")],
            ["Expires", key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"],
            ["", ""],
            ["=== USAGE LIMITS ===", ""],
            ["Max Patients/Request", key.max_patients_per_request],
            ["Max Requests/Day", key.max_requests_per_day or "Unlimited"],
            ["Max Requests/Minute", key.max_requests_per_minute],
            ["Max Requests/Hour", key.max_requests_per_hour],
            ["", ""],
            ["=== USAGE STATS ===", ""],
            ["Total Requests", f"{key.total_requests:,}"],
            ["Total Patients", f"{key.total_patients_generated:,}"],
            ["Today's Requests", key.daily_requests],
            ["Last Used", key.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if key.last_used_at else "Never"],
        ]
        
        click.echo(tabulate(info, tablefmt="plain"))

@cli.command()
@click.argument('key_id')
def deactivate(key_id):
    """Deactivate an API key."""
    with get_db() as db:
        key = db.query(APIKey).filter(
            (APIKey.key == key_id) | (APIKey.id == key_id)
        ).first()
        
        if not key:
            click.echo("API key not found", err=True)
            return
        
        key.is_active = False
        db.commit()
        
        click.echo(f"Deactivated API key: {key.name}")

@cli.command()
@click.argument('key_id')
def activate(key_id):
    """Reactivate an API key."""
    with get_db() as db:
        key = db.query(APIKey).filter(
            (APIKey.key == key_id) | (APIKey.id == key_id)
        ).first()
        
        if not key:
            click.echo("API key not found", err=True)
            return
        
        key.is_active = True
        db.commit()
        
        click.echo(f"Activated API key: {key.name}")

if __name__ == "__main__":
    cli()
```

### 6. Integration Points

#### Router Updates
```python
# src/api/v1/routers/generation.py
@router.post("/generate")
async def generate_patients(
    request: PatientGenerationRequest,
    api_key_context: APIKeyContext = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Generate patients with API key validation."""
    # Check limits
    api_key_context.check_patient_limit(request.count)
    api_key_context.check_daily_limit()
    
    # Generate patients
    patients = await generate_patients_async(request)
    
    # Track usage
    api_key_context.api_key.total_requests += 1
    api_key_context.api_key.daily_requests += 1
    api_key_context.api_key.total_patients_generated += request.count
    api_key_context.api_key.last_used_at = datetime.utcnow()
    db.commit()
    
    return patients
```

#### Frontend Integration
```javascript
// Show demo key prominently
const API_DEMO_BANNER = `
<div class="api-demo-banner">
    <h3>🔑 Try Our API - No Registration Required!</h3>
    <p>Use this demo API key to test up to 50 patients:</p>
    <code class="demo-key">DEMO_MILMED_2025_50_PATIENTS</code>
    <button onclick="copyDemoKey()">📋 Copy Key</button>
    <p class="limits">Limits: 50 patients/request • 10 requests/minute • 100 requests/day</p>
</div>
`;
```

## 📊 Implementation Plan

### Week 1: Core Infrastructure
1. **Day 1-2**: Database setup
   - Create migration for api_keys table
   - Implement SQLAlchemy models
   - Set up repository pattern

2. **Day 3-4**: Security implementation
   - Enhanced API key verification
   - Context object with limits
   - Rate limiting middleware

3. **Day 5**: Testing
   - Unit tests for all components
   - Integration tests for API flow
   - Load testing for rate limits

### Week 2: Management Tools & Integration
1. **Day 1-2**: CLI tool
   - Implement all management commands
   - Add usage reporting
   - Create bash wrapper script

2. **Day 3-4**: API integration
   - Update all routers
   - Add usage tracking
   - Implement limit enforcement

3. **Day 5**: Documentation & deployment
   - API documentation updates
   - Deployment procedures
   - Team training

## 🧪 Testing Strategy

### Unit Tests
```python
def test_api_key_generation():
    """Test secure key generation."""
    key1 = generate_api_key()
    key2 = generate_api_key()
    
    assert len(key1) == 64
    assert key1 != key2
    assert key1.startswith("sk_live_")

def test_demo_key_limits():
    """Test demo key enforces limits."""
    context = APIKeyContext(
        api_key=create_demo_key(),
        is_demo=True
    )
    
    # Should pass
    context.check_patient_limit(50)
    
    # Should fail
    with pytest.raises(HTTPException) as exc:
        context.check_patient_limit(51)
    assert exc.value.status_code == 400
```

### Integration Tests
```python
async def test_rate_limiting():
    """Test per-key rate limiting."""
    api_key = create_test_key(max_requests_per_minute=5)
    
    # Make 5 requests - should succeed
    for i in range(5):
        response = await client.post(
            "/api/v1/generate",
            headers={"X-API-Key": api_key.key},
            json={"count": 10}
        )
        assert response.status_code == 200
    
    # 6th request should fail
    response = await client.post(
        "/api/v1/generate",
        headers={"X-API-Key": api_key.key},
        json={"count": 10}
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers
```

## 📈 Success Metrics

### Technical Metrics
- API key lookup time: <10ms
- Rate limit check time: <5ms
- Zero unauthorized access incidents
- 100% accurate usage tracking

### Business Metrics
- 50+ demo API users in first month
- 10+ production API keys issued
- Usage insights driving capacity planning
- Clear usage patterns for billing

## 🚀 Rollout Strategy

### Phase 1: Internal Testing
1. Deploy to development environment
2. Create test keys for QA team
3. Validate all limits and tracking
4. Performance testing

### Phase 2: Beta Release
1. Select 3-5 beta customers
2. Issue production keys with support
3. Monitor usage patterns
4. Gather feedback

### Phase 3: General Availability
1. Public announcement
2. Demo key promoted on website
3. Self-service key generation (future)
4. Usage-based billing (future)

## 🔧 Configuration

### Environment Variables
```bash
# Demo key configuration (hardcoded in app)
DEMO_KEY_PATIENT_LIMIT=50
DEMO_KEY_DAILY_LIMIT=100
DEMO_KEY_MINUTE_LIMIT=10

# Default limits for new keys
DEFAULT_PATIENT_LIMIT=1000
DEFAULT_DAILY_LIMIT=10000
DEFAULT_MINUTE_LIMIT=60
```

### Redis Configuration
```python
# Rate limiting cache
REDIS_RATE_LIMIT_PREFIX = "rate:"
REDIS_RATE_LIMIT_TTL = 3600  # 1 hour

# Usage tracking cache
REDIS_USAGE_PREFIX = "usage:"
REDIS_USAGE_TTL = 86400  # 24 hours
```

## 🛠️ Operational Procedures

### Daily Operations
1. Monitor demo key usage
2. Check for rate limit violations
3. Review new key requests
4. Update usage statistics

### Key Lifecycle Management
1. **Creation**: Via CLI with approval
2. **Rotation**: Quarterly for security
3. **Deactivation**: Immediate when needed
4. **Deletion**: After 90 days inactive

### Incident Response
1. **Compromised Key**: Immediate deactivation
2. **Rate Limit Bypass**: Block IP, investigate
3. **Usage Anomaly**: Contact customer
4. **System Overload**: Temporary limit reduction

## 📚 Documentation

### API Documentation
- Updated OpenAPI specs with auth
- Example requests with demo key
- Rate limit header documentation
- Error response examples

### User Guides
- "Getting Started with the API"
- "Understanding Rate Limits"
- "Usage Tracking and Billing"
- "API Best Practices"

## 🎯 Definition of Done

### MVP Complete When:
- [ ] Database schema deployed
- [ ] API key validation working
- [ ] Demo key functional with limits
- [ ] CLI tool operational
- [ ] Rate limiting active
- [ ] Usage tracking accurate
- [ ] Documentation updated
- [ ] Team trained

### Future Enhancements:
- [ ] Web dashboard for key management
- [ ] Webhook notifications
- [ ] Usage analytics dashboard
- [ ] Billing system integration
- [ ] OAuth/JWT support

## 🔗 Dependencies

### Technical Dependencies
- PostgreSQL for key storage
- Redis for rate limiting
- SQLAlchemy for ORM
- Click for CLI tool

### Team Dependencies
- Security team review
- Legal approval for ToS
- Marketing for demo key promotion
- Support team training

## 🚨 Risks and Mitigations

### Risk 1: Demo Key Abuse
- **Impact**: Resource exhaustion
- **Mitigation**: Strict limits, monitoring, IP blocking

### Risk 2: Key Compromise
- **Impact**: Unauthorized access
- **Mitigation**: Key rotation, audit logs, immediate deactivation

### Risk 3: Performance Impact
- **Impact**: Slower API responses
- **Mitigation**: Caching, async validation, connection pooling

---

**Epic Status**: Design complete, ready for implementation
**Design Location**: `memory/implementations/api-key-management-system-design.md`
**Next Steps**: Get approval to implement and create feature branch `epic/api-key-management`