# Code Examples for Refactoring Implementation

## Task 1: Database Consolidation Examples

### Files to Update

```python
# patient_generator/config_manager.py
# BEFORE:
from .database import Database

class ConfigurationManager:
    def __init__(self, database_instance: Database = None):
        self.database = database_instance or Database.get_instance()

# AFTER:
from src.infrastructure.database_adapter import get_enhanced_database

class ConfigurationManager:
    def __init__(self, database_instance=None):
        self.database = database_instance or get_enhanced_database()
```

```python
# patient_generator/database.py
# DELETE THIS FILE ENTIRELY
```

```python
# src/domain/services/patient_generation_service.py
# BEFORE:
from patient_generator.database import Database

class AsyncPatientGenerationService:
    def __init__(self):
        self.db = Database()

# AFTER:
from src.infrastructure.database_adapter import get_enhanced_database

class AsyncPatientGenerationService:
    def __init__(self):
        self.db = get_enhanced_database()
```

### Update Repository Pattern

```python
# src/domain/repositories/api_key_repository.py
# Add proper async support

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class APIKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_key(self, api_key: str) -> Optional[APIKey]:
        """Get API key by key value"""
        stmt = select(APIKey).where(APIKey.key == api_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_demo_key_if_not_exists(self) -> APIKey:
        """Create demo key if it doesn't exist"""
        existing = await self.get_by_key(DEMO_API_KEY_CONFIG["key"])
        if existing:
            return existing
        
        # Create new demo key
        demo_key = APIKey(**DEMO_API_KEY_CONFIG)
        self.session.add(demo_key)
        await self.session.commit()
        return demo_key
```

## Task 2: Generation Pipeline Examples

### In-Memory Temporal Configuration

```python
# patient_generator/flow_simulator.py
# Update constructor and generate_casualty_flow

class PatientFlowSimulator:
    def __init__(self, config_manager: ConfigurationManager, temporal_config: Optional[Dict] = None):
        self.config_manager = config_manager
        self.temporal_config = temporal_config  # NEW: Store temporal config
        self.patients: List[Patient] = []
        # ... rest of init
    
    def generate_casualty_flow(self):
        """Generate casualties - check for temporal configuration"""
        
        # Check in-memory config first
        if self.temporal_config and "warfare_types" in self.temporal_config:
            print(f"Using in-memory temporal config with base_date: {self.temporal_config.get('base_date')}")
            return self.generate_temporal_casualties_from_config(self.temporal_config)
        
        # Fall back to legacy check (can be removed later)
        injuries_path = os.path.join(os.path.dirname(__file__), "injuries.json")
        try:
            with open(injuries_path) as f:
                injuries_config = json.load(f)
            
            if "warfare_types" in injuries_config:
                print("Using file-based temporal generation (deprecated)")
                return self.generate_temporal_casualties()
        except Exception:
            pass
        
        # Default generation
        return self._generate_flow_sequential(self.total_patients_to_generate)
    
    def generate_temporal_casualties_from_config(self, config: Dict[str, Any]):
        """Generate casualties using in-memory temporal config"""
        # Initialize temporal generator
        warfare_patterns_path = os.path.join(os.path.dirname(__file__), "warfare_patterns.json")
        temporal_gen = TemporalPatternGenerator(warfare_patterns_path)
        
        # Generate casualty timeline
        casualty_timeline = temporal_gen.generate_timeline(
            days=config["days_of_fighting"],
            total_patients=config["total_patients"],
            active_warfare_types=config["warfare_types"],
            intensity=config.get("intensity", "medium"),
            tempo=config.get("tempo", "sustained"),
            environmental_conditions=config.get("environmental_conditions", {}),
            special_events=config.get("special_events", {}),
            base_date=config["base_date"],
        )
        
        # Generate patients from timeline
        patients = self._generate_patients_from_timeline(
            casualty_timeline, 
            config.get("injury_mix", config.get("injury_distribution"))
        )
        
        # Simulate flow
        if len(patients) >= 500 and self.num_workers > 1:
            self._simulate_flow_parallel(patients)
        else:
            for patient in patients:
                self._simulate_patient_flow_single(patient)
        
        return patients
```

### Streaming Generation Implementation

```python
# src/domain/services/patient_generation_service.py

class StreamingPatientWriter:
    """Handle streaming output of patients"""
    
    def __init__(self, output_directory: str, formats: List[str]):
        self.output_directory = output_directory
        self.formats = formats
        self.writers = {}
        self.first_write = True
    
    async def __aenter__(self):
        """Initialize writers"""
        for fmt in self.formats:
            if fmt == "json":
                file_path = os.path.join(self.output_directory, "patients.json")
                self.writers[fmt] = await aiofiles.open(file_path, 'w')
                await self.writers[fmt].write('[\n')
            elif fmt == "csv":
                file_path = os.path.join(self.output_directory, "patients.csv")
                self.writers[fmt] = await aiofiles.open(file_path, 'w')
                # Write CSV header
                await self.writers[fmt].write(
                    "patient_id,name,age,gender,nationality,injury,triage,"
                    "front,final_status,last_facility,total_timeline_events,"
                    "injury_timestamp\n"
                )
        return self
    
    async def write_patient(self, patient: Patient):
        """Write a single patient to all formats"""
        for fmt, writer in self.writers.items():
            if fmt == "json":
                if not self.first_write:
                    await writer.write(',\n')
                patient_json = json.dumps(patient.to_dict(), indent=2)
                await writer.write(patient_json)
            elif fmt == "csv":
                # Extract CSV fields
                csv_line = self._patient_to_csv_line(patient)
                await writer.write(csv_line + '\n')
        
        self.first_write = False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close all writers"""
        for fmt, writer in self.writers.items():
            if fmt == "json":
                await writer.write('\n]')
            await writer.close()

# Updated generation method
async def generate_patients_streaming(self, context: GenerationContext):
    """Generate patients with true streaming"""
    
    # Initialize pipeline with temporal config if present
    temporal_config = None
    if any(k in context.config for k in ["warfare_types", "base_date"]):
        temporal_config = {
            "total_patients": context.config.total_patients,
            "days_of_fighting": context.config.get("days_of_fighting", 8),
            "base_date": context.config.get("base_date"),
            "warfare_types": context.config.get("warfare_types"),
            # ... other temporal fields
        }
    
    # Create flow simulator with in-memory config
    flow_simulator = PatientFlowSimulator(
        self.config_manager,
        temporal_config=temporal_config
    )
    
    # Use streaming writer
    async with StreamingPatientWriter(
        context.output_directory, 
        context.output_formats
    ) as writer:
        
        # Generate in chunks
        chunk_size = 1000
        for start_idx in range(0, context.config.total_patients, chunk_size):
            end_idx = min(start_idx + chunk_size, context.config.total_patients)
            
            # Generate chunk of patients
            patients = await self._generate_patient_chunk(
                flow_simulator, start_idx, end_idx
            )
            
            # Process and write each patient
            for patient in patients:
                # Add demographics
                patient = await self._add_demographics(patient, context)
                
                # Add medical conditions
                patient = await self._add_medical_conditions(patient, context)
                
                # Write immediately
                await writer.write_patient(patient)
            
            # Update progress
            if self.progress_callback:
                progress = end_idx / context.config.total_patients
                await self.progress_callback({
                    "progress": progress,
                    "processed_patients": end_idx
                })
            
            # Let other tasks run
            await asyncio.sleep(0)
```

## Task 3: Smart Caching Examples

### Cache Warmup Implementation

```python
# src/core/cache_warmup.py

from typing import List, Dict, Any
import asyncio
from src.core.cache import CacheService
from src.infrastructure.database_adapter import get_enhanced_database

class CacheWarmupService:
    """Service to warm caches on application startup"""
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.db = get_enhanced_database()
    
    async def warm_all_caches(self):
        """Warm all critical caches in parallel"""
        tasks = [
            self._warm_demographics_cache(),
            self._warm_medical_cache(),
            self._warm_configuration_cache(),
            self._warm_computation_patterns()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_name = tasks[i].__name__
                print(f"Failed to warm cache for {task_name}: {result}")
    
    async def _warm_demographics_cache(self):
        """Pre-load common demographics data"""
        # Common nationality/gender combinations
        common_combos = [
            ("USA", "male"), ("USA", "female"),
            ("UK", "male"), ("UK", "female"),
            ("Germany", "male"), ("Germany", "female"),
            ("France", "male"), ("France", "female"),
        ]
        
        for nationality, gender in common_combos:
            # Generate sample demographics
            from patient_generator.demographics import DemographicsGenerator
            gen = DemographicsGenerator()
            
            # Generate 100 samples and cache
            samples = []
            for _ in range(100):
                person = gen.generate_person(nationality, gender)
                samples.append(person)
            
            cache_key = f"demographics:{nationality}:{gender}:samples"
            await self.cache.set(cache_key, samples, ttl=86400)  # 24 hours
    
    async def _warm_medical_cache(self):
        """Pre-load medical condition mappings"""
        from patient_generator.medical import MedicalConditionGenerator
        gen = MedicalConditionGenerator()
        
        # Cache condition lookups
        injury_types = ["BATTLE_TRAUMA", "NON_BATTLE", "DISEASE"]
        triage_categories = ["T1", "T2", "T3"]
        
        for injury in injury_types:
            for triage in triage_categories:
                # Generate sample conditions
                conditions = []
                for _ in range(50):
                    condition = gen.generate_condition(injury, triage)
                    conditions.append(condition)
                
                cache_key = f"medical:conditions:{injury}:{triage}"
                await self.cache.set(cache_key, conditions, ttl=86400)
    
    async def _warm_configuration_cache(self):
        """Cache frequently used configurations"""
        # Get recent configurations
        query = """
            SELECT c.id, c.name, c.config_data, COUNT(j.id) as usage_count
            FROM configurations c
            LEFT JOIN jobs j ON j.config->>'configuration_id' = c.id::text
            WHERE j.created_at > NOW() - INTERVAL '30 days'
            GROUP BY c.id
            ORDER BY usage_count DESC
            LIMIT 20
        """
        
        async with self.db.get_connection() as conn:
            results = await conn.fetch(query)
            
            for row in results:
                cache_key = f"config:{row['id']}:v2"
                config_data = {
                    "id": row['id'],
                    "name": row['name'],
                    **row['config_data']
                }
                await self.cache.set(cache_key, config_data, ttl=86400)
    
    async def _warm_computation_patterns(self):
        """Pre-compute common warfare patterns"""
        warfare_types = ["conventional", "artillery", "urban", "guerrilla"]
        base_distributions = [
            {"Disease": 0.52, "Non-Battle Injury": 0.33, "Battle Injury": 0.15},
            {"Disease": 0.40, "Non-Battle Injury": 0.30, "Battle Injury": 0.30},
        ]
        
        for warfare in warfare_types:
            for base_dist in base_distributions:
                # Compute injury distribution
                cache_key = f"computation:injury_dist:{warfare}:{hash(str(sorted(base_dist.items())))}"
                
                # Simulate computation
                computed_dist = self._compute_warfare_distribution(warfare, base_dist)
                
                await self.cache.set(cache_key, computed_dist, ttl=7200)  # 2 hours
```

### Computation Caching Layer

```python
# src/core/computation_cache.py

import hashlib
import json
from typing import Any, Callable, Optional, TypeVar, Generic
from src.core.cache import CacheService

T = TypeVar('T')

class ComputationCache(Generic[T]):
    """Generic computation caching layer"""
    
    def __init__(self, cache: CacheService, prefix: str = "computation"):
        self.cache = cache
        self.prefix = prefix
    
    def _make_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key from operation and arguments"""
        # Create stable hash from arguments
        key_data = {
            "op": operation,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{self.prefix}:{operation}:{key_hash}"
    
    async def get_or_compute(
        self,
        operation: str,
        compute_func: Callable[..., T],
        *args,
        ttl: int = 3600,
        **kwargs
    ) -> T:
        """Get from cache or compute and store"""
        cache_key = self._make_key(operation, *args, **kwargs)
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Compute
        if asyncio.iscoroutinefunction(compute_func):
            result = await compute_func(*args, **kwargs)
        else:
            result = compute_func(*args, **kwargs)
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=ttl)
        
        return result
    
    async def invalidate(self, operation: str, *args, **kwargs):
        """Invalidate specific cached computation"""
        cache_key = self._make_key(operation, *args, **kwargs)
        await self.cache.delete(cache_key)
    
    async def invalidate_operation(self, operation: str):
        """Invalidate all cached results for an operation"""
        pattern = f"{self.prefix}:{operation}:*"
        await self.cache.invalidate_pattern(pattern)

# Usage example in flow simulator
class CachedFlowSimulator(PatientFlowSimulator):
    def __init__(self, config_manager, temporal_config=None):
        super().__init__(config_manager, temporal_config)
        self.comp_cache = ComputationCache(get_cache_service())
    
    async def _get_warfare_injury_distribution(
        self, 
        warfare_type: str, 
        base_mix: Dict[str, float]
    ) -> Dict[str, float]:
        """Get injury distribution with caching"""
        return await self.comp_cache.get_or_compute(
            "warfare_injury_dist",
            self._compute_injury_distribution,
            warfare_type,
            base_mix,
            ttl=7200  # Cache for 2 hours
        )
```

### Cache Invalidation Strategy

```python
# src/api/v1/dependencies/cache_invalidation.py

from typing import List, Optional
from src.core.cache import get_cache_service

class CacheInvalidator:
    """Handle cache invalidation on data changes"""
    
    def __init__(self):
        self.cache = get_cache_service()
    
    async def invalidate_configuration(self, config_id: str):
        """Invalidate all caches related to a configuration"""
        patterns = [
            f"config:{config_id}:*",
            f"computation:*:{config_id}:*",
            f"job:*:config:{config_id}"
        ]
        
        for pattern in patterns:
            await self.cache.invalidate_pattern(pattern)
    
    async def invalidate_job(self, job_id: str):
        """Invalidate job-related caches"""
        patterns = [
            f"job:{job_id}:*",
            f"job:status:{job_id}"
        ]
        
        for pattern in patterns:
            await self.cache.invalidate_pattern(pattern)
    
    async def invalidate_api_key(self, api_key: str):
        """Invalidate API key caches"""
        # Hash the key for cache lookup
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        patterns = [
            f"api_key:{key_hash}",
            f"api_key:limits:{key_hash}"
        ]
        
        for pattern in patterns:
            await self.cache.invalidate_pattern(pattern)

# Usage in API endpoints
@router.put("/configurations/{config_id}")
async def update_configuration(
    config_id: str,
    updates: ConfigurationUpdate,
    invalidator: CacheInvalidator = Depends()
):
    # Update in database
    result = await config_repo.update(config_id, updates)
    
    # Invalidate caches
    await invalidator.invalidate_configuration(config_id)
    
    return result
```
