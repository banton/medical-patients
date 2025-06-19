# patient_generator/repository.py
"""Configuration repository for managing ConfigurationTemplates in PostgreSQL"""

import json
from typing import List, Optional
import uuid

import psycopg2.extras

from .schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB


class ConfigurationRepository:
    """Repository for managing ConfigurationTemplates in PostgreSQL"""

    def __init__(self, db):
        self.db = db

    def _row_to_pydantic(self, row: Optional[psycopg2.extras.DictRow]) -> Optional[ConfigurationTemplateDB]:
        if row is None:
            return None
        # Pydantic model expects Python dicts for JSONB fields after json.loads
        # The DB stores them as JSONB, psycopg2 DictRow might return them as strings or already parsed
        return ConfigurationTemplateDB(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            front_configs=row["front_configs"],  # Already parsed by psycopg2
            facility_configs=row["facility_configs"],
            injury_distribution=row["injury_distribution"],
            total_patients=row["total_patients"],
            version=row.get("version", 1),
            parent_config_id=row.get("parent_config_id"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_configuration(self, config: ConfigurationTemplateCreate) -> ConfigurationTemplateDB:
        """Create a new configuration template"""
        config_id = str(uuid.uuid4())
        insert_query = """
        INSERT INTO configuration_templates (
            id, name, description, front_configs, facility_configs,
            injury_distribution, total_patients
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        
        # Convert pydantic models to dicts
        front_configs_dict = [fc.model_dump() if hasattr(fc, 'model_dump') else fc.dict() for fc in config.front_configs]
        facility_configs_dict = [fc.model_dump() if hasattr(fc, 'model_dump') else fc.dict() for fc in config.facility_configs]
        
        params = (
            config_id,
            config.name,
            config.description,
            json.dumps(front_configs_dict),
            json.dumps(facility_configs_dict),
            json.dumps(config.injury_distribution),
            config.total_patients,
        )
        row = self.db._execute_query(insert_query, params, fetch_one=True, commit=True)
        return self._row_to_pydantic(row)

    def get_configuration(self, config_id: str) -> Optional[ConfigurationTemplateDB]:
        """Get a configuration template by ID"""
        query = "SELECT * FROM configuration_templates WHERE id = %s"
        row = self.db._execute_query(query, (config_id,), fetch_one=True)
        return self._row_to_pydantic(row)

    def list_configurations(self) -> List[ConfigurationTemplateDB]:
        """List all configuration templates"""
        query = "SELECT * FROM configuration_templates ORDER BY created_at DESC"
        rows = self.db._execute_query(query, (), fetch_all=True)
        return [self._row_to_pydantic(row) for row in rows]

    def update_configuration(self, config_id: str, config: ConfigurationTemplateCreate) -> Optional[ConfigurationTemplateDB]:
        """Update a configuration template"""
        # Convert pydantic models to dicts
        front_configs_dict = [fc.model_dump() if hasattr(fc, 'model_dump') else fc.dict() for fc in config.front_configs]
        facility_configs_dict = [fc.model_dump() if hasattr(fc, 'model_dump') else fc.dict() for fc in config.facility_configs]
        
        update_query = """
        UPDATE configuration_templates
        SET name = %s, description = %s, front_configs = %s, facility_configs = %s,
            injury_distribution = %s, total_patients = %s, updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """
        params = (
            config.name,
            config.description,
            json.dumps(front_configs_dict),
            json.dumps(facility_configs_dict),
            json.dumps(config.injury_distribution),
            config.total_patients,
            config_id,
        )
        row = self.db._execute_query(update_query, params, fetch_one=True, commit=True)
        return self._row_to_pydantic(row)

    def delete_configuration(self, config_id: str) -> bool:
        """Delete a configuration template"""
        delete_query = "DELETE FROM configuration_templates WHERE id = %s"
        self.db._execute_query(delete_query, (config_id,), commit=True)
        return True