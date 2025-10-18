from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """User model from which all agents and workflows are associated"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from external auth system
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agents = relationship("UserAgent", back_populates="user", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")

class UserAgent(Base):
    """User-defined agents"""
    __tablename__ = "user_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    agent_id = Column(String, index=True)  # Unique agent ID within the user's namespace
    name = Column(String)
    role = Column(String)
    tools = Column(JSON)  # List of tool names used by the agent
    enable_memory = Column(Boolean, default=True)
    markdown = Column(Boolean, default=True)
    num_history_runs = Column(Integer, default=3)
    agent_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agents")
    workflow_steps = relationship("WorkflowStep", back_populates="agent")

class Workflow(Base):
    """User-defined workflows"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    workflow_id = Column(String, unique=True, index=True)  # UUID for the workflow
    name = Column(String, nullable=False, default="Untitled Workflow")  # New field
    description = Column(Text, nullable=True)  # New field
    current_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    is_drafted = Column(Boolean, default=False)
    approved = Column(Boolean, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    outputs = relationship("WorkflowOutput", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowOutput.step_order")
    context_items = relationship("WorkflowContext", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowStep(Base):
    """Steps in a workflow"""
    __tablename__ = "workflow_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("user_agents.id"), nullable=True)  # Can be null for system agents
    step_order = Column(Integer)
    name = Column(String)  # Agent name
    prompt = Column(Text)
    human_review = Column(Boolean, default=False)
    allow_edit = Column(Boolean, default=False)
    agent_metadata = Column(JSON, nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    agent = relationship("UserAgent", back_populates="workflow_steps", foreign_keys=[agent_id])

class WorkflowOutput(Base):
    """Outputs from each step in a workflow"""
    __tablename__ = "workflow_outputs"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    step_order = Column(Integer)
    agent_name = Column(String)
    output = Column(Text)
    edited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="outputs")

class WorkflowContext(Base):
    """Context items shared between workflow steps"""
    __tablename__ = "workflow_context"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    key = Column(String)
    value = Column(Text)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="context_items")