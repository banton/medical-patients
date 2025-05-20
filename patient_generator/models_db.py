# patient_generator/models_db.py
import uuid
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base # Changed from relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func # For server-side default timestamps

Base = declarative_base()

class ConfigurationTemplateDBModel(Base):
    __tablename__ = "configuration_templates"

    # Using String for ID to allow user-defined or other types of IDs if needed,
    # but UUID default can be handled at application level if desired.
    # For Alembic autogenerate, a server-side default for UUID is harder without specific DB functions.
    # Let's use UUID type but expect application to provide it or use client-side default.
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # For simplicity with Alembic and potential string IDs from API:
    id = Column(String, primary_key=True, index=True) 
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    front_configs = Column(JSONB, nullable=False) 
    facility_configs = Column(JSONB, nullable=False) 
    injury_distribution = Column(JSONB, nullable=False) 
    
    total_patients = Column(Integer, nullable=False)

    version = Column(Integer, nullable=False, server_default='1', default=1)
    # parent_config_id allows tracking derivation from other templates
    parent_config_id = Column(String, ForeignKey('configuration_templates.id'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to parent (self-referential)
    # parent = relationship("ConfigurationTemplateDBModel", remote_side=[id], backref="children")
    # Children relationship can be defined if needed:
    # children = relationship("ConfigurationTemplateDBModel", backref=backref('parent', remote_side=[id]))


class JobDBModel(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False)
    config = Column(JSONB, nullable=False) 
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(JSONB, nullable=True)
    progress = Column(Integer, default=0)
    progress_details = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    output_files = Column(JSONB, nullable=True) 
    file_types = Column(JSONB, nullable=True) 
    total_size = Column(Integer, default=0)
    total_size_formatted = Column(String, nullable=True)

# To ensure Alembic can find these models, you might need to import this module
# (e.g., patient_generator.models_db) in your alembic_migrations/env.py
# and set target_metadata = Base.metadata
