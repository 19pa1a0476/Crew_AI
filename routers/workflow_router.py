import uuid
from typing import Optional
from sqlalchemy.orm import Session
from configuration import OKTAConfig
import utilities.pg_sql_db_util as db_util
from utilities.token_validator import validate_token
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Header
from services.workflow_service import WorkflowManager, execute_workflow
from models.request_response_models import StartWorkflowRequest, WorkflowStep, ReviewRequest, WorkflowResponse
from services.agents_service import (
    load_user_agents
)


router = APIRouter()
manager = WorkflowManager()

@router.post("/draft_workflow")
async def draft_workflow(
    request: StartWorkflowRequest, 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=request.user_id
    )

    db_user = db_util.get_user_by_external_id(db, request.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Load user agents
    load_user_agents(db_user.id)
    
    # Convert request steps to workflow steps
    workflow_steps = []
    for step in request.steps:
        metadata = step.metadata or {}
        workflow_steps.append(WorkflowStep(
            name=step.name,
            prompt=step.prompt,
            human_review=step.human_review,
            allow_edit=step.allow_edit,
            metadata=metadata
        ))
    
    if(request.workflow_id):
        workflow_id = request.workflow_id
    else:
        workflow_id = str(uuid.uuid4())
    
    # Create workflow with name and description
    manager.create_workflow(
        workflow_id=workflow_id,
        steps=workflow_steps,
        user_id=db_user.id,
        name=request.name,
        description=request.description,
        is_drafted=True
    )
    
    return {
        "workflow_id": workflow_id,
        "name": request.name,
        "status": "Drafted"
    }


@router.post("/start_workflow")
async def start_workflow(
    request: StartWorkflowRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=request.user_id
    )

    db_user = db_util.get_user_by_external_id(db, request.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Load user agents
    load_user_agents(db_user.id)
    
    # Convert request steps to workflow steps
    workflow_steps = []
    for step in request.steps:
        metadata = step.metadata or {}
        workflow_steps.append(WorkflowStep(
            name=step.name,
            prompt=step.prompt,
            human_review=step.human_review,
            allow_edit=step.allow_edit,
            metadata=metadata
        ))
    

    if(request.workflow_id):
        workflow_id = request.workflow_id
    else:
        workflow_id = str(uuid.uuid4())
    
    # Create workflow with name and description
    manager.create_workflow(
        workflow_id=workflow_id,
        steps=workflow_steps,
        user_id=db_user.id,
        name=request.name,
        description=request.description,
        is_drafted=False
    )
    
    background_tasks.add_task(execute_workflow, manager, workflow_id, db_user.id)
    return {
        "workflow_id": workflow_id,
        "name": request.name,
        "status": "started"
    }


@router.post("/review/{workflow_id}")
async def review_workflow(
    workflow_id: str, 
    review: ReviewRequest, 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    """Merged endpoint for reviewing AND editing workflow outputs"""

    # Verify user
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=review.user_id
    )

    db_user = db_util.get_user_by_external_id(db, review.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    workflow = manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Handle edited output if provided
    if review.edited_output is not None:
        current_step = workflow.steps[workflow.current_index]
        if not (current_step.human_review and current_step.allow_edit):
            raise HTTPException(status_code=400, 
                             detail="Editing is only allowed for steps with human_review and allow_edit enabled")
        
        manager.set_edited_output(workflow_id, review.edited_output)
    
    # Process review
    workflow.approved = review.approved
    if review.feedback:
        manager.set_feedback(workflow_id, review.feedback)
    
    # Update approval in database
    with db_util.SessionLocal() as db:
        db_util.update_workflow_approval(db, workflow_id, review.approved, review.feedback)
    
    workflow.event.set()
    return {"message": "Review processed successfully"}



@router.get("/workflow_output/{workflow_id}")
async def get_output(
    workflow_id: str, 
    user_id: str = Query(...), 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    workflow = manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get the current context
    context = manager.get_context(workflow_id)
    
    # Add information about which outputs can be edited
    output_with_edit_info = []
    for i, output in enumerate(workflow.outputs):
        output_copy = output.copy()
        
        # If this is the current step and it allows editing, mark it
        if i == workflow.current_index and i < len(workflow.steps):
            step = workflow.steps[i]
            output_copy["can_edit"] = step.human_review and step.allow_edit
        else:
            output_copy["can_edit"] = False
            
        output_with_edit_info.append(output_copy)
    
    return {
        "outputs": output_with_edit_info,
        "current_step": workflow.current_index + 1 if workflow else 0,
        "total_steps": len(workflow.steps) if workflow else 0,
        "context": context
    }


@router.get("/workflow_status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str, 
    user_id: str = Query(...), 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    workflow = manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get current step to check if editing is allowed
    current_step = None
    allow_edit = False
    if workflow.current_index < len(workflow.steps):
        current_step = workflow.steps[workflow.current_index]
        allow_edit = current_step.human_review and current_step.allow_edit
    
    return {
        "current_step": workflow.current_index + 1,
        "total_steps": len(workflow.steps),
        "completed": workflow.current_index >= len(workflow.steps),
        "drafted": workflow.is_drafted,
        "awaiting_review": current_step.human_review if current_step else False,
        "allow_edit": allow_edit
    }


@router.get("/user_workflows")
async def get_user_workflows(
    user_id: str = Query(...), 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    """List workflows created by the user with name and description"""

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    try:
        db_user = db_util.get_user_by_external_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        workflows = db_util.get_user_workflows(db, db_user.id)
        return {"workflows": workflows}
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "workflows": []}
    

@router.delete("/workflow/{workflow_id}")
async def delete_workflow(
    workflow_id: str, 
    user_id: str = Query(...), 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Delete a workflow and all its associated data
    
    This endpoint will:
    1. Delete the workflow from the database (cascade will handle steps, outputs, context)
    2. Remove any workflow analytics data
    3. Remove the workflow from in-memory storage if present
    """

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    try:
        # Get user
        db_user = db_util.get_user_by_external_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if workflow exists and belongs to this user
        db_workflow = db_util.get_workflow(db, workflow_id)
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        if db_workflow.user_id != db_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this workflow")
                

        db_util.delete_workflow_analytics(workflow_id)
        
        # Delete workflow from database
        result = db_util.delete_workflow(db, workflow_id)
        
        # Remove from in-memory cache if exists
        if workflow_id in manager.workflows:
            del manager.workflows[workflow_id]
        
        return {"message": f"Workflow '{workflow_id}' and all associated data successfully deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")
    

@router.get("/workflow_design/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_design(
    workflow_id: str,
    user_id: str = Query(..., description="ID of the user requesting the workflow"),
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Retrieve details of a workflow by its workflow_id for the specified user.
    """
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    db_workflow = db_util.get_workflow(db, workflow_id)
    if not db_workflow:
        raise HTTPException(status_code=404, detail=f"Workflow with id {workflow_id} not found")
    
    # Verify the workflow belongs to the user
    if db_workflow.user.external_id != user_id:
        raise HTTPException(status_code=403, detail="User not authorized to access this workflow")
    
    # Convert database steps to WorkflowStep models
    steps = [
        WorkflowStep(
            name=step.name,
            prompt=step.prompt,
            human_review=step.human_review,
            allow_edit=step.allow_edit,
            metadata=step.agent_metadata or {}
        )
        for step in sorted(db_workflow.steps, key=lambda s: s.step_order)
    ]
    
    # Return structured response
    return WorkflowResponse(
        workflow_id=db_workflow.workflow_id,
        name=db_workflow.name,
        description=db_workflow.description,
        steps=steps,
        is_drafted=db_workflow.is_drafted,
        created_at=db_workflow.created_at.isoformat() if db_workflow.created_at else None,
        updated_at=db_workflow.updated_at.isoformat() if db_workflow.updated_at else None
    )
