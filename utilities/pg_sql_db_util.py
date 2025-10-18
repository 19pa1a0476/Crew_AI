import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configuration import PGVectorConfig
from sqlalchemy.orm import Session
from sqlalchemy import and_
import models.database_models as models
from typing import Dict, List, Any
from models.request_response_models import WorkflowStep, WorkflowState

# Use the same database connection string from PGVectorConfig
SQLALCHEMY_DATABASE_URL = PGVectorConfig.VECTOR_DB_CONNECTION_STRING

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# User CRUD operations
def get_user_by_external_id(db: Session, external_id: str):
    return db.query(models.User).filter(models.User.external_id == external_id).first()

def create_user(db: Session, username: str, external_id: str):
    db_user = models.User(username=username, external_id=external_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(db: Session, username: str, external_id: str):
    username = "shyam" if not username else username
    external_id = "123456789" if not external_id else external_id
    user = get_user_by_external_id(db, external_id)
    if not user:
        user = create_user(db, username, external_id)
    return user

# Agent CRUD operations
def create_user_agent(db: Session, user_id: int, agent_id: str, name: str, role: str, 
                      tools: List[str], enable_memory: bool = True, 
                      markdown: bool = True, num_history_runs: int = 3, 
                      metadata: Dict[str, Any] = None):
    db_agent = models.UserAgent(
        user_id=user_id,
        agent_id=agent_id,
        name=name,
        role=role,
        tools=tools,
        enable_memory=enable_memory,
        markdown=markdown,
        num_history_runs=num_history_runs,
        agent_metadata=metadata or {}
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def get_user_agent_by_id(db: Session, user_id: int, agent_id: str):
    return db.query(models.UserAgent).filter(
        and_(models.UserAgent.user_id == user_id, models.UserAgent.agent_id == agent_id)
    ).first()

def get_user_agents(db: Session, user_id: int):
    return db.query(models.UserAgent).filter(models.UserAgent.user_id == user_id).all()

def delete_user_agent(db: Session, user_id: int, agent_id: str):
    agent = get_user_agent_by_id(db, user_id, agent_id)
    if agent:
        db.delete(agent)
        db.commit()
        return True
    return False


# Workflow CRUD operations
def create_workflow(db: Session, workflow_id: str, user_id: int, workflow_steps: List[WorkflowStep], 
                   name: str = "Untitled Workflow", description: str = None, is_drafted: bool = False):
    """Create a new workflow or update an existing one with steps"""
    
    # Check if the workflow already exists
    existing_workflow = get_workflow(db, workflow_id)
    
    if existing_workflow:
        # Update existing workflow
        existing_workflow.name = name
        existing_workflow.description = description
        existing_workflow.is_drafted = is_drafted
        existing_workflow.current_index = 0  # Reset index for drafts
        existing_workflow.is_completed = False
        
        # Delete existing steps, outputs and context to avoid duplicates
        db.query(models.WorkflowStep).filter(models.WorkflowStep.workflow_id == existing_workflow.id).delete()
        db.query(models.WorkflowOutput).filter(models.WorkflowOutput.workflow_id == existing_workflow.id).delete()
        db.query(models.WorkflowContext).filter(models.WorkflowContext.workflow_id == existing_workflow.id).delete()
        
        db_workflow = existing_workflow
    else:
        # Create new workflow
        db_workflow = models.Workflow(
            user_id=user_id,
            workflow_id=workflow_id,
            name=name,
            description=description,
            current_index=0,
            is_completed=False,
            is_drafted=is_drafted
        )
        db.add(db_workflow)
    
    # Flush to ensure we have an ID
    db.flush()
    
    # Create workflow steps
    for idx, step in enumerate(workflow_steps):
        # Try to get user agent ID if it's a user-defined agent
        agent_id = None
        db_agent = db.query(models.UserAgent).filter(
            and_(models.UserAgent.user_id == user_id, 
                 models.UserAgent.agent_id == step.name.lower().replace(" ", "_"))
        ).first()
        
        if db_agent:
            agent_id = db_agent.id
            
        db_step = models.WorkflowStep(
            workflow_id=db_workflow.id,
            agent_id=agent_id,
            step_order=idx,
            name=step.name,
            prompt=step.prompt,
            human_review=step.human_review,
            allow_edit=step.allow_edit,
            agent_metadata=step.metadata or {}
        )
        db.add(db_step)
    
    # Initialize workflow context with step metadata
    for idx, step in enumerate(workflow_steps):
        if step.metadata:
            # Use a consistent naming scheme: step_X_metadata
            step_prefix = f"step_{idx+1}_metadata_"
            for key, value in step.metadata.items():
                context_key = f"{step_prefix}{key}"
                db_context = models.WorkflowContext(
                    workflow_id=db_workflow.id,
                    key=context_key,
                    value=str(value)
                )
                db.add(db_context)
    
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def delete_workflow(db: Session, workflow_id: str):
    """Delete a workflow and all its associated data"""
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        # The cascade will handle deleting associated steps, outputs, and context
        db.delete(db_workflow)
        db.commit()
        return True
    return False


def get_workflow(db: Session, workflow_id: str):
    return db.query(models.Workflow).filter(models.Workflow.workflow_id == workflow_id).first()


def get_user_workflows(db: Session, user_id: int):
    workflows = db.query(models.Workflow).filter(models.Workflow.user_id == user_id).all()
    return [
        {
            "workflow_id": w.workflow_id,
            "name": w.name,  # Include name
            "description": w.description,  # Include description
            "current_step": w.current_index + 1,
            "total_steps": len(w.steps),
            "is_completed": w.is_completed,
            "is_drafted": w.is_drafted,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "updated_at": w.updated_at.isoformat() if w.updated_at else None
        }
        for w in workflows
    ]

def update_workflow_status(db: Session, workflow_id: str, current_index: int, is_completed: bool = False):
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        db_workflow.current_index = current_index
        db_workflow.is_completed = is_completed
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    return None

def update_workflow_approval(db: Session, workflow_id: str, approved: bool, feedback: str = None):
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        db_workflow.approved = approved
        if feedback:
            db_workflow.feedback = feedback
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    return None

def clear_workflow_approval(db: Session, workflow_id: str):
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        db_workflow.approved = None
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    return None

# Workflow Output CRUD operations
def add_workflow_output(db: Session, workflow_id: str, agent_name: str, output: str):
    db_workflow = get_workflow(db, workflow_id)

    if db_workflow:
        # Get the next step order
        step_order = len(db_workflow.outputs)
        
        db_output = models.WorkflowOutput(
            workflow_id=db_workflow.id,
            step_order=step_order,
            agent_name=agent_name,
            output=output,
            edited=False
        )
        db.add(db_output)
        
        # Add to context
        output_key = f"output_from_{agent_name}"
        update_workflow_context(db, workflow_id, output_key, output)
        
        db.commit()
        db.refresh(db_output)
        return db_output
    return None

def update_workflow_output(db: Session, workflow_id: str, step_order: int, output: str, edited: bool = True):
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        for db_output in db_workflow.outputs:
            if db_output.step_order == step_order:
                db_output.output = output
                db_output.edited = edited
                
                # Update in context
                agent_name = db_output.agent_name
                output_key = f"output_from_{agent_name}"
                update_workflow_context(db, workflow_id, output_key, output)
                
                db.commit()
                db.refresh(db_output)
                return db_output
    return None

# Workflow Context CRUD operations
def get_workflow_context(db: Session, workflow_id: str) -> Dict[str, Any]:
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        context = {}
        for item in db_workflow.context_items:
            context[item.key] = item.value
        return context
    return {}

def update_workflow_context(db: Session, workflow_id: str, key: str, value: str):
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        # Check if the key exists
        db_context = db.query(models.WorkflowContext).filter(
            and_(models.WorkflowContext.workflow_id == db_workflow.id,
                 models.WorkflowContext.key == key)
        ).first()
        
        if db_context:
            db_context.value = value
        else:
            db_context = models.WorkflowContext(
                workflow_id=db_workflow.id,
                key=key,
                value=value
            )
            db.add(db_context)
        
        db.commit()
        if db_context.id:  # Only refresh if it has an ID (was added to DB)
            db.refresh(db_context)
        return db_context
    return None

# Helper function to convert DB models to Python objects
def workflow_to_workflow_state(db_workflow):
    """Convert a DB Workflow to a WorkflowState object for compatibility"""

    # Create WorkflowStep objects from DB steps
    steps = []
    for db_step in sorted(db_workflow.steps, key=lambda s: s.step_order):
        step = WorkflowStep(
            name=db_step.name,
            prompt=db_step.prompt,
            human_review=db_step.human_review,
            allow_edit=db_step.allow_edit,
            agent_metadata=db_step.metadata or {}
        )
        steps.append(step)
    
    # Create WorkflowState
    workflow_state = WorkflowState(steps)
    workflow_state.current_index = db_workflow.current_index
    workflow_state.approved = db_workflow.approved
    workflow_state.feedback = db_workflow.feedback or ""
    workflow_state.is_drafted = db_workflow.is_drafted
    
    # Populate outputs
    for db_output in sorted(db_workflow.outputs, key=lambda o: o.step_order):
        workflow_state.outputs.append({
            "agent": db_output.agent_name,
            "output": db_output.output,
            "edited": db_output.edited
        })
    
    # Populate context
    for context_item in db_workflow.context_items:
        workflow_state.context[context_item.key] = context_item.value
        
    return workflow_state



def delete_workflow_analytics(workflow_id: str):
    db_config = {
        "dbname": PGVectorConfig.VECTORDB_NAME,
        "user": PGVectorConfig.VECTORDB_USER,
        "password": PGVectorConfig.VECTORDB_PASS,
        "host": PGVectorConfig.VECTORDB_HOST,
        "port": PGVectorConfig.VECTORDB_PORT
    }
    
    # Connect to analytics database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Delete all agent sessions that contain this workflow_id
        cursor.execute(
            "DELETE FROM ai.agent_sessions WHERE session_id LIKE %s",
            (f"%+{workflow_id}",)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error deleting analytics data: {str(e)}")
    finally:
        cursor.close()
        conn.close()