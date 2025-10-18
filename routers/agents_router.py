import uuid
from configuration import OKTAConfig
from utilities.token_validator import validate_token
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Dict, Any, Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.request_response_models import CreateAgentRequest, InvokeAgentPayload
import services.agents_service as agent_service
import utilities.pg_sql_db_util as db_util

router = APIRouter()

@router.post("/create_agent")
async def create_agent(
    request: CreateAgentRequest,
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(db_util.get_db)
):
    """Create a new agent with custom configuration"""

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=request.user_id
    )

    try:
        # verify user
        db_user = db_util.get_user_by_external_id(db, request.user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        agent_id = request.name.lower().replace(" ", "_")
        
        # Create the agent with the provided configuration
        agent = agent_service.create_new_agent(
            name=request.name,
            role=request.role,
            tool_names=request.tools,
            enable_memory=request.enable_memory,
            markdown=request.markdown,
            num_history_runs=request.num_history_runs,
            metadata=request.metadata or {},
            user_id=db_user.id
        )
        
        return {
            "agent_id": agent_id,
            "name": request.name,
            "role": request.role,
            "tools": request.tools,
            "status": "created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    

@router.get("/.well-known/agent.json")
async def agent_json(name: str):
    try:
        card = agent_service.get_agent_card_and_skills(name)
        return JSONResponse(content=card.dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.post("/invoke")
async def invoke_agent(payload: InvokeAgentPayload, db: Session = Depends(db_util.get_db)) -> Any:
    agent_name = payload.agent_name
    prompt = payload.prompt
    context = payload.context
    user_id = payload.user_id
    workflow_id = payload.workflow_id or str(uuid.uuid4())

    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    agent_service.load_user_agents(db_user.id)
    
    response = await agent_service.run_agent_with_context(
        agent_name=agent_name,
        prompt=prompt,
        context=context or {},
        workflow_id=workflow_id,
        user_id=db_user.id
    )

    output_content = response.content if hasattr(response, 'content') else str(response)
    return {"result": output_content}


@router.delete("/delete/{agent_id}")
async def delete_agent(
    agent_id: str, 
    user_id: str = Query(...), 
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(db_util.get_db)
):
    """Delete a user-defined agent"""

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
        
        # Delete agent
        success = agent_service.delete_user_agent(db_user.id, agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        return {"message": f"Agent '{agent_id}' successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/available_agents")
async def get_available_agents(
    user_id: str = Query(...), 
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(db_util.get_db)
):
    """List all available agents in the system including user-defined agents"""

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
        
        # Get all agents (system + user)
        agents = agent_service.get_all_available_agents(db_user.id)
        return {"agents": agents}
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "agents": []}

@router.get("/user_agents")
async def get_user_agents(
    user_id: str = Query(...), 
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(db_util.get_db)
):
    """List only user-defined agents"""

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
        
        # Load user agents if not loaded yet
        agent_service.load_user_agents(db_user.id)
        
        # Get user agents from database
        db_agents = db_util.get_user_agents(db, db_user.id)
        
        # Format the response
        agents = []
        for agent in db_agents:
            agents.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "tools": agent.tools,
                "enable_memory": agent.enable_memory,
                "markdown": agent.markdown,
                "num_history_runs": agent.num_history_runs,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            })
        
        return {"agents": agents}
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "agents": []}
    

@router.get("/available_tools")
async def get_available_tools(authorization: Optional[str] = Header(None)):
    """List all available tools that can be used with custom agents"""

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=None
    )

    try:
        tools = agent_service.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        return {"error": str(e), "tools": []}
    