# -*- coding: utf-8 -*-
"""
ORM Models
==========
All SQLAlchemy ORM models for the application. This is the single
source of truth for the database schema.

Activity-specific models can be added at the bottom of this file or
in activities/<name>/models.py (and imported here for discovery).

Usage:
    from core.models import Base, Project, PlaxisCalculation
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import json

Base = declarative_base()


# ---------------------------------------------------------------------------
# Project management
# ---------------------------------------------------------------------------

class Project(Base):
    """A RamGAP project that groups activities together."""
    __tablename__ = 'projects'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by  = Column(String(255), nullable=False)  # Windows username
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active   = Column(Boolean, default=True)

    access_list = relationship(
        'ProjectAccess', back_populates='project', cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id':           self.id,
            'name':         self.name,
            'description':  self.description,
            'created_by':   self.created_by,
            'created_at':   self.created_at.isoformat() if self.created_at else None,
            'updated_at':   self.updated_at.isoformat() if self.updated_at else None,
            'is_active':    self.is_active,
            'allowed_users': [a.username for a in self.access_list] if self.access_list else [],
        }


class ProjectAccess(Base):
    """Access-control record: which users can access which project."""
    __tablename__ = 'project_access'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    username   = Column(String(255), nullable=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    granted_by = Column(String(255), nullable=True)

    project = relationship('Project', back_populates='access_list')

    def to_dict(self):
        return {
            'id':         self.id,
            'project_id': self.project_id,
            'username':   self.username,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'granted_by': self.granted_by,
        }


class RecentActivity(Base):
    """Log entry for a user action (app opened, activity started, etc.)."""
    __tablename__ = 'recent_activity'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(255), nullable=False)
    project_id    = Column(Integer, nullable=True)
    activity_type = Column(String(100), nullable=False)
    activity_name = Column(String(255), nullable=False)
    activity_data = Column(Text, nullable=True)  # optional JSON payload
    timestamp     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':            self.id,
            'username':      self.username,
            'project_id':    self.project_id,
            'activity_type': self.activity_type,
            'activity_name': self.activity_name,
            'activity_data': self.activity_data,
            'timestamp':     self.timestamp.isoformat() if self.timestamp else None,
        }


# ---------------------------------------------------------------------------
# Plaxis activity
# ---------------------------------------------------------------------------

class PlaxisCalculation(Base):
    """Record of a Plaxis result-extraction job with full input/output history."""
    __tablename__ = 'plaxis_calculations'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    project_id    = Column(Integer, ForeignKey('projects.id'), nullable=True)
    username      = Column(String(255), nullable=False)
    activity_name = Column(String(255), nullable=False)

    # Status: 'started' | 'running' | 'completed' | 'failed'
    status = Column(String(50), nullable=False, default='started')

    # Connection parameters
    input_port  = Column(Integer, nullable=True)
    output_port = Column(Integer, nullable=True)

    # Selected structures (JSON lists)
    selected_spunts  = Column(Text, nullable=True)
    selected_anchors = Column(Text, nullable=True)

    # Selected analysis phases (JSON lists)
    capacity_phases      = Column(Text, nullable=True)
    msf_phases           = Column(Text, nullable=True)
    displacement_phases  = Column(Text, nullable=True)
    displacement_component = Column(String(50), nullable=True, default='Ux')

    # Output
    output_path   = Column(String(500), nullable=True)
    output_file   = Column(String(500), nullable=True)
    results_json  = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    started_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # --- helpers ---

    def set_structures(self, spunts: list, anchors: list):
        self.selected_spunts  = json.dumps(spunts)  if spunts  else None
        self.selected_anchors = json.dumps(anchors) if anchors else None

    def get_structures(self):
        return {
            'spunts':  json.loads(self.selected_spunts)  if self.selected_spunts  else [],
            'anchors': json.loads(self.selected_anchors) if self.selected_anchors else [],
        }

    def set_phases(self, capacity: list, msf: list, displacement: list):
        self.capacity_phases     = json.dumps(capacity)     if capacity     else None
        self.msf_phases          = json.dumps(msf)          if msf          else None
        self.displacement_phases = json.dumps(displacement) if displacement else None

    def get_phases(self):
        return {
            'capacity':     json.loads(self.capacity_phases)     if self.capacity_phases     else [],
            'msf':          json.loads(self.msf_phases)          if self.msf_phases          else [],
            'displacement': json.loads(self.displacement_phases) if self.displacement_phases else [],
        }

    def to_dict(self):
        return {
            'id':                    self.id,
            'project_id':            self.project_id,
            'activity_name':         self.activity_name,
            'status':                self.status,
            'input_port':            self.input_port,
            'output_port':           self.output_port,
            'structures':            self.get_structures(),
            'phases':                self.get_phases(),
            'displacement_component': self.displacement_component,
            'output_path':           self.output_path,
            'output_file':           self.output_file,
            'results':               json.loads(self.results_json) if self.results_json else None,
            'error_message':         self.error_message,
            'started_at':            self.started_at.isoformat()   if self.started_at   else None,
            'completed_at':          self.completed_at.isoformat() if self.completed_at else None,
        }


# ---------------------------------------------------------------------------
# GeoTolk activity
# ---------------------------------------------------------------------------

class GeoTolkSession(Base):
    """A GeoTolk interpretation session grouping one or more file interpretations."""
    __tablename__ = 'geotolk_sessions'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    project_id    = Column(Integer, ForeignKey('projects.id'), nullable=True)
    activity_name = Column(String(255), nullable=False)
    username      = Column(String(255), nullable=False)

    # Status: 'active' | 'completed'
    status          = Column(String(50), nullable=False, default='active')
    total_files     = Column(Integer, default=0)
    completed_files = Column(Integer, default=0)

    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    interpretations = relationship(
        'GeoTolkInterpretation', back_populates='session', cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id':              self.id,
            'project_id':      self.project_id,
            'activity_name':   self.activity_name,
            'status':          self.status,
            'total_files':     self.total_files,
            'completed_files': self.completed_files,
            'created_at':      self.created_at.isoformat()   if self.created_at   else None,
            'completed_at':    self.completed_at.isoformat() if self.completed_at else None,
        }


class GeoTolkInterpretation(Base):
    """
    Layer interpretation for a single SND file.
    Stored for future ML training.
    """
    __tablename__ = 'geotolk_interpretations'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('geotolk_sessions.id'), nullable=False)

    filename  = Column(String(500), nullable=False)
    max_depth = Column(Float, nullable=True)

    # JSON summary of parsed measurements (not full arrays)
    parsed_data = Column(Text, nullable=True)

    # Layer interpretation: [{"type": "leire|sand|fjell|annet", "start": 0.0, "end": 5.0}, ...]
    layers = Column(Text, nullable=True)

    # ML prediction (same format as layers)
    ml_prediction = Column(Text, nullable=True)
    ml_confidence = Column(Float, nullable=True)

    # Status: 'pending' | 'interpreted' | 'verified'
    status = Column(String(50), nullable=False, default='pending')

    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    interpreted_at = Column(DateTime, nullable=True)

    session = relationship('GeoTolkSession', back_populates='interpretations')

    # --- helpers ---

    def set_layers(self, layers: list):
        self.layers = json.dumps(layers) if layers else None

    def get_layers(self):
        return json.loads(self.layers) if self.layers else []

    def set_parsed_data(self, data: dict):
        summary = {
            'max_depth':  data.get('max_depth'),
            'num_points': len(data.get('depth', [])),
            'spyling':    data.get('spyling', []),
            'slag':       data.get('slag', []),
        }
        self.parsed_data = json.dumps(summary)

    def get_parsed_data(self):
        return json.loads(self.parsed_data) if self.parsed_data else {}

    def to_dict(self):
        return {
            'id':            self.id,
            'session_id':    self.session_id,
            'filename':      self.filename,
            'max_depth':     self.max_depth,
            'parsed_data':   self.get_parsed_data(),
            'layers':        self.get_layers(),
            'ml_prediction': json.loads(self.ml_prediction) if self.ml_prediction else None,
            'ml_confidence': self.ml_confidence,
            'status':        self.status,
            'created_at':    self.created_at.isoformat()     if self.created_at     else None,
            'interpreted_at': self.interpreted_at.isoformat() if self.interpreted_at else None,
        }


# ---------------------------------------------------------------------------
# Modeling activity
# ---------------------------------------------------------------------------

class ModelingActivity(Base):
    """
    A modeling activity linked to a project.
    Stores an Excel input file and GH optimization results (JSON, MD, IFC).
    Files are stored in Azure Blob Storage; only blob names are kept here.
    """
    __tablename__ = 'modeling_activities'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    name       = Column(String(255), nullable=False)
    username   = Column(String(255), nullable=False)

    # 'active' | 'has_excel' | 'has_results'
    status = Column(String(50), nullable=False, default='active')

    # Blob Storage references
    excel_blob_name = Column(String(500), nullable=True)
    excel_filename  = Column(String(255), nullable=True)
    ifc_blob_name   = Column(String(500), nullable=True)
    ifc_filename    = Column(String(255), nullable=True)

    # Optimization results stored as text
    run_report_json = Column(Text, nullable=True)   # full run-report.json content
    run_summary_md  = Column(Text, nullable=True)   # run-summary.md content

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':             self.id,
            'project_id':     self.project_id,
            'name':           self.name,
            'username':       self.username,
            'status':         self.status,
            'has_excel':      bool(self.excel_blob_name),
            'has_ifc':        bool(self.ifc_blob_name),
            'has_results':    bool(self.run_report_json),
            'excel_filename': self.excel_filename,
            'ifc_filename':   self.ifc_filename,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'updated_at':     self.updated_at.isoformat() if self.updated_at else None,
        }
