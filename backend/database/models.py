# -*- coding: utf-8 -*-
"""
Database models for RamGAP
Using SQLAlchemy ORM - ready for Azure SQL migration
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()


class Project(Base):
    """Project model"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=False)  # Windows username
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    access_list = relationship("ProjectAccess", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'allowed_users': [a.username for a in self.access_list] if self.access_list else []
        }


class ProjectAccess(Base):
    """Project access control - which users can access which projects"""
    __tablename__ = 'project_access'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    username = Column(String(255), nullable=False)  # Windows username
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(String(255), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="access_list")
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'username': self.username,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'granted_by': self.granted_by
        }


class RecentActivity(Base):
    """Track recent user activity - which apps/features were used"""
    __tablename__ = 'recent_activity'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    project_id = Column(Integer, nullable=True)  # Optional: link to project
    activity_type = Column(String(100), nullable=False)  # e.g., 'app', 'project', 'feature'
    activity_name = Column(String(255), nullable=False)
    activity_data = Column(Text, nullable=True)  # JSON data if needed
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'project_id': self.project_id,
            'activity_type': self.activity_type,
            'activity_name': self.activity_name,
            'activity_data': self.activity_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class DataEntry(Base):
    """Generic data entry model - placeholder for future development"""
    __tablename__ = 'data_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    entry_type = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    numeric_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'entry_type': self.entry_type,
            'value': self.value,
            'numeric_value': self.numeric_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PlaxisCalculation(Base):
    """Track Plaxis calculations with full parameter history"""
    __tablename__ = 'plaxis_calculations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    username = Column(String(255), nullable=False)  # Who ran it
    activity_name = Column(String(255), nullable=False)  # User-given name for this activity
    
    # Status: 'started', 'running', 'completed', 'failed'
    status = Column(String(50), nullable=False, default='started')
    
    # Connection parameters
    input_port = Column(Integer, nullable=True)
    output_port = Column(Integer, nullable=True)
    
    # Selected structures (JSON)
    selected_spunts = Column(Text, nullable=True)  # JSON list of spunt names
    selected_anchors = Column(Text, nullable=True)  # JSON list of anchor names
    
    # Selected analyses (JSON)
    capacity_phases = Column(Text, nullable=True)  # JSON list of phase names
    msf_phases = Column(Text, nullable=True)  # JSON list of phase names
    displacement_phases = Column(Text, nullable=True)  # JSON list of phase names
    displacement_component = Column(String(50), nullable=True, default='Ux')
    
    # Results
    output_path = Column(String(500), nullable=True)  # Where results are saved
    output_file = Column(String(500), nullable=True)  # Generated Excel file
    results_json = Column(Text, nullable=True)  # Full results as JSON
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def set_structures(self, spunts: list, anchors: list):
        """Set selected structures as JSON"""
        self.selected_spunts = json.dumps(spunts) if spunts else None
        self.selected_anchors = json.dumps(anchors) if anchors else None
    
    def get_structures(self):
        """Get selected structures from JSON"""
        return {
            'spunts': json.loads(self.selected_spunts) if self.selected_spunts else [],
            'anchors': json.loads(self.selected_anchors) if self.selected_anchors else []
        }
    
    def set_phases(self, capacity: list, msf: list, displacement: list):
        """Set selected phases as JSON"""
        self.capacity_phases = json.dumps(capacity) if capacity else None
        self.msf_phases = json.dumps(msf) if msf else None
        self.displacement_phases = json.dumps(displacement) if displacement else None
    
    def get_phases(self):
        """Get selected phases from JSON"""
        return {
            'capacity': json.loads(self.capacity_phases) if self.capacity_phases else [],
            'msf': json.loads(self.msf_phases) if self.msf_phases else [],
            'displacement': json.loads(self.displacement_phases) if self.displacement_phases else []
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'activity_name': self.activity_name,
            'status': self.status,
            'input_port': self.input_port,
            'output_port': self.output_port,
            'structures': self.get_structures(),
            'phases': self.get_phases(),
            'displacement_component': self.displacement_component,
            'output_path': self.output_path,
            'output_file': self.output_file,
            'results': json.loads(self.results_json) if self.results_json else None,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
