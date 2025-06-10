# API-First Development Patterns

## Overview
Documented patterns established during the Medical Patients Generator API standardization. These patterns should be consistently applied across all API development.

## Core Principles

### 1. API Contract First
- Define Pydantic models before implementation
- Create comprehensive validation rules
- Document with OpenAPI/Swagger examples
- Write failing tests for expected behavior

### 2. Consistent Versioning
- All API endpoints use `/api/v1/` prefix
- Version increments for breaking changes
- Maintain backward compatibility when possible
- Clear deprecation strategy

### 3. Standardized Response Format
- All endpoints return Pydantic models
- Consistent field naming (snake_case)
- ISO 8601 datetime formatting
- Comprehensive error responses

## Request Model Patterns

### Basic Request Pattern
```python
class StandardRequest(BaseModel):
    required_field: str = Field(..., min_length=1, description="Required field")
    optional_field: Optional[str] = Field(None, description="Optional field")
    
    @validator('required_field')
    def validate_required_field(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "required_field": "example value",
                "optional_field": "optional value"
            }
        }
```

### Cross-Field Validation Pattern
```python
@root_validator
def validate_dependencies(cls, values):
    field_a = values.get('field_a')
    field_b = values.get('field_b')
    
    if field_a and not field_b:
        raise ValueError('field_b is required when field_a is provided')
    
    return values
```

### Enum Validation Pattern
```python
class PriorityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class RequestWithEnum(BaseModel):
    priority: PriorityLevel = Field(default=PriorityLevel.NORMAL)
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in PriorityLevel:
            valid_values = [e.value for e in PriorityLevel]
            raise ValueError(f'Invalid priority: {v}. Valid values: {valid_values}')
        return v
```

## Response Model Patterns

### Standard Response Pattern
```python
class StandardResponse(BaseModel):
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Current status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "item_12345",
                "created_at": "2024-01-15T10:30:00Z",
                "status": "active"
            }
        }
```

### List Response Pattern
```python
class ListResponse(BaseModel):
    items: List[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=50, description="Items per page")
    has_next: bool = Field(default=False, description="More pages available")
```

### Error Response Pattern
```python
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error category")
    detail: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

## Router Patterns

### Standard Router Setup
```python
from fastapi import APIRouter, HTTPException, Depends, status
from src.api.v1.models import RequestModel, ResponseModel, ErrorResponse

router = APIRouter(
    prefix="/resource",
    tags=["resource"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    }
)
```

### CRUD Endpoint Pattern
```python
@router.post(
    "/",
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create Resource",
    description="Detailed description of the endpoint functionality",
    response_description="Resource created successfully"
)
async def create_resource(
    request: RequestModel,
    current_user: str = Depends(verify_api_key),
    service: Service = Depends(get_service)
) -> ResponseModel:
    try:
        result = await service.create(request)
        return ResponseModel.from_domain(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resource: {str(e)}"
        )
```

## Validation Patterns

### Field-Level Validation
```python
@validator('email')
def validate_email(cls, v):
    if v and '@' not in v:
        raise ValueError('Invalid email format')
    return v.lower() if v else v

@validator('phone')
def validate_phone(cls, v):
    if v and not v.replace('-', '').replace(' ', '').isdigit():
        raise ValueError('Phone must contain only digits, spaces, and hyphens')
    return v
```

### List Validation
```python
@validator('tags')
def validate_tags(cls, v):
    if not v:
        return v
    
    valid_tags = ['urgent', 'normal', 'low']
    invalid_tags = [tag for tag in v if tag not in valid_tags]
    
    if invalid_tags:
        raise ValueError(f'Invalid tags: {invalid_tags}. Valid tags: {valid_tags}')
    
    return list(set(v))  # Remove duplicates
```

### Complex Object Validation
```python
@validator('configuration')
def validate_configuration(cls, v):
    if not isinstance(v, dict):
        raise ValueError('Configuration must be a dictionary')
    
    required_fields = ['demographics', 'medical', 'count']
    missing_fields = [field for field in required_fields if field not in v]
    
    if missing_fields:
        raise ValueError(f'Configuration missing required fields: {missing_fields}')
    
    if v.get('count', 0) <= 0:
        raise ValueError('Patient count must be greater than 0')
    
    return v
```

## Error Handling Patterns

### Exception Handler Pattern
```python
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )
```

### Service-Level Error Pattern
```python
class ServiceError(Exception):
    """Base service error."""
    pass

class NotFoundError(ServiceError):
    """Resource not found error."""
    pass

class ValidationError(ServiceError):
    """Business logic validation error."""
    pass

# In router:
try:
    result = service.operation()
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

## Testing Patterns

### Request Validation Test Pattern
```python
def test_request_validation_fails_for_invalid_input():
    """Test that invalid input raises appropriate validation errors."""
    with pytest.raises(ValidationError) as exc_info:
        RequestModel(invalid_field="invalid_value")
    
    assert "Invalid format" in str(exc_info.value)

def test_request_validation_passes_for_valid_input():
    """Test that valid input passes validation."""
    request = RequestModel(
        required_field="valid_value",
        optional_field="optional_value"
    )
    assert request.required_field == "valid_value"
```

### API Integration Test Pattern
```python
def test_endpoint_returns_expected_response():
    """Test API endpoint returns properly formatted response."""
    response = requests.post(
        f"{BASE_URL}/api/v1/resource/",
        headers={"X-API-Key": API_KEY},
        json={"field": "value"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Validate response structure
    assert "id" in data
    assert "created_at" in data
    assert "status" in data
    
    # Validate data types
    assert isinstance(data["id"], str)
    assert isinstance(data["status"], str)
```

## Documentation Patterns

### OpenAPI Documentation Pattern
```python
@router.post(
    "/",
    response_model=ResponseModel,
    status_code=201,
    summary="Brief endpoint summary",
    description="""
    Detailed multi-line description explaining:
    - What the endpoint does
    - Required parameters
    - Expected behavior
    - Special considerations
    """,
    response_description="Success response description",
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Validation error occurred",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Validation Error",
                        "detail": "Field 'email' is required",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)
```

## Best Practices

### 1. Model Organization
- Keep request and response models in separate files
- Use clear, descriptive model names
- Group related models together
- Export commonly used models from `__init__.py`

### 2. Validation Strategy
- Validate at the earliest possible point
- Provide clear, actionable error messages
- Use field validators for single-field validation
- Use root validators for cross-field validation
- Normalize data during validation (strip whitespace, lowercase emails)

### 3. Response Consistency
- Always use response models, never raw dictionaries
- Include metadata (timestamps, IDs, status)
- Use consistent field naming conventions
- Provide examples in schema definitions

### 4. Error Handling
- Create specific exception types for different error categories
- Map exceptions to appropriate HTTP status codes
- Include sufficient context in error messages
- Log errors appropriately for debugging

### 5. Testing Strategy
- Test both valid and invalid inputs
- Test edge cases and boundary conditions
- Verify response structure and data types
- Test error conditions and responses
- Use integration tests for complete API workflows

These patterns ensure consistent, maintainable, and well-documented APIs that follow industry best practices.