import json
import uuid
from sqlalchemy.orm import Session
import utilities.pg_sql_db_util as db_util
from typing import Optional, AsyncGenerator, Dict, Any
from configuration import OKTAConfig, MCPServerConfig
from utilities.token_validator import validate_token
import utilities.sol_std_db_util as std_db_util
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Header
from services.solution_std_service import AGENT_LIBRARY
from utilities.studio_agents.one_drive_agent import onedrive_agent
from utilities.studio_agents.conversational_ai_agent import conversational_ai_agent
from utilities.studio_agents.unit_test_agent import unit_test_generator_agent
from utilities.studio_agents.repo_miner_agent import repo_miner_agent
from utilities.studio_agents.sql_master_agent import sql_master_agent
from utilities.studio_agents.code_nexus_agent import code_nexus_agent
from utilities.studio_agents.code_converter_agent import code_conversion_agent
from utilities.studio_agents.code_doc_agent import code_doc_agent
from utilities.studio_agents.synthetic_test_agent import synthetic_data_agent
from utilities.studio_agents.test_script_generator import test_script_generator_agent
from utilities.studio_agents.brd_generator_agent import brd_generator_agent
from utilities.studio_agents.user_story_agent import user_story_agent
from utilities.studio_agents.test_cases_generator import testcase_generator_agent
from utilities.studio_agents.code_reviewer_agent import code_reviewer_agent
from utilities.studio_agents.impact_analyzer_agent import impact_analyzer_agent
from utilities.studio_agents.mermaid_agent import mermaid_agent
from utilities.studio_agents.xdata_analytics_agent import xdata_analytics_agent
from utilities.studio_agents.log_analyzer_agent import log_analyzer_agent
from services.solution_std_service import (
    get_toolkit_config, setup_agents_and_tools, 
    register_agent, setup_team)
from models.request_response_models import (
    ToolkitConfigPayload, ChatCompletionRequest,
    UserAgentConfigPayload)
from utilities.tools_library import TOOLKIT_LIBRARY
from utilities.tool_credential_validator import ToolCredentialValidator


router = APIRouter()

# Agent Registration
register_agent(agent=brd_generator_agent)
register_agent(agent=code_conversion_agent)
register_agent(agent=code_doc_agent)
register_agent(agent=code_nexus_agent)
register_agent(agent=code_reviewer_agent)
register_agent(agent=conversational_ai_agent)
register_agent(agent=impact_analyzer_agent)
register_agent(agent=mermaid_agent)
register_agent(agent=onedrive_agent)
register_agent(agent=repo_miner_agent)
register_agent(agent=sql_master_agent)
register_agent(agent=synthetic_data_agent)
register_agent(agent=test_script_generator_agent)
register_agent(agent=testcase_generator_agent)
register_agent(agent=unit_test_generator_agent)
register_agent(agent=user_story_agent)
register_agent(agent=xdata_analytics_agent)
register_agent(agent=log_analyzer_agent)

@router.get("/available-agents")
def get_available_agents(
    authorization: Optional[str] = Header(None)
):
    """
    Returns a dictionary of all available agents from AGENT_LIBRARY.
    Format: { agent_id: agent_name }
    """
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=None
    )

    return {
        agent_id: data.get("agent_name", agent_id)
        for agent_id, data in AGENT_LIBRARY.items()
    }


@router.get("/toolkit-config/{user_id}/{agent_id}")
def get_agent_toolkit_schema(
    agent_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(std_db_util.get_db)
):
    """
    Returns the config schema details for all tools associated with the given agent,
    with saved values from DB for a given user.
    """
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    result = get_toolkit_config(agent_id=agent_id, user_id=user_id, db=db)
    return result


@router.post("/toolkit-config/{agent_id}")
def configure_agent_toolkit(
    payload: ToolkitConfigPayload, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(db_util.get_db)
):
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=payload.user_id
    )
    
    db_user = db_util.get_user_by_external_id(db, payload.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    validation_errors = []

    for tool_name, tool_config in payload.config.items():
        if tool_name in TOOLKIT_LIBRARY:
            try:
                # Convert list format to dict format
                if isinstance(tool_config, list):
                    actual_config = {}
                    for item in tool_config:
                        if hasattr(item, 'key') and hasattr(item, 'value'):
                            actual_config[item.key] = item.value
                        elif isinstance(item, dict) and "key" in item and "value" in item:
                            actual_config[item["key"]] = item["value"]
                        elif isinstance(item, dict):
                            actual_config.update(item)
                else:
                    actual_config = tool_config

                is_valid, message = ToolCredentialValidator.validate_tool_credentials(
                    tool_name, 
                    actual_config
                )
                
                if not is_valid:
                    validation_errors.append(f"{tool_name}: {message}")
                    continue
                
            except Exception as e:
                print(f"Exception for {tool_name}: {str(e)}")
                validation_errors.append(f"{tool_name}: {str(e)}")
        else:
            validation_errors.append(f"{tool_name}: Unknown tool not in library")
    
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed for tools: {', '.join(validation_errors)}"
        )

    std_db_util.update_user_toolkit_config(user_id=payload.user_id, config_payload=payload.config, db=db)
    return {"message": "Toolkit configuration updated successfully."}



@router.get("/user-agent-config/{user_id}/{agent_id}")
def read_user_agent_config(
    user_id: str, 
    agent_id: str, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(std_db_util.get_db)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    data = std_db_util.get_user_agent_config(user_id, agent_id, db)
    data["tools"] = AGENT_LIBRARY[agent_id].get("tools", [])
    if data is None:
        raise HTTPException(status_code=404, detail=f"User agent config not found for agent '{agent_id}'.")
    return data


@router.post("/user-agent-config/{user_id}")
def update_user_agent_config(
    user_id: str, 
    payload: UserAgentConfigPayload, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(std_db_util.get_db)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )
    
    if payload.agent_id not in AGENT_LIBRARY:
        raise HTTPException(status_code=404, detail=f"Agent '{payload.agent_id}' not found in agent library.")

    # Overwrite tools from agent library, ignore tools from payload if any
    tools = AGENT_LIBRARY[payload.agent_id].get("tools", [])

    data = {
        "agent_id": payload.agent_id,
        "enable_memory": payload.enable_memory,
        "markdown": payload.markdown,
        "num_history_runs": payload.num_history_runs,
        "tools": tools,
        "agent_config": payload.agent_config or {},
        "knowledgebase_details": payload.knowledgebase_details or []
    }

    std_db_util.upsert_user_agent_config(user_id=user_id, payload=data, db=db)
    return {"message": f"User agent config updated for user '{user_id}'."}



@router.post("/initialize-all-configs/{user_id}")
def initialize_all_configs(user_id: str, authorization: Optional[str] = Header(None), db: Session = Depends(db_util.get_db)):
    """
    Initializes all agent and toolkit configuration entries in the DB
    with default empty values for a given user_id.
    Skips any entries that already exist (ON CONFLICT DO NOTHING).
    """
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )
    
    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    std_db_util.initialize_all_user_agents_and_toolkits(user_id, AGENT_LIBRARY, db)
    return {"message": f"All agent and toolkit configurations initialized for user '{user_id}'."}



@router.post("/chat_completion")
async def chat_completion(
    request: ChatCompletionRequest, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(std_db_util.get_db)
):
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=request.user_id
    )

    try:
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
            title = (request.user_query[:25]).strip()  # Use first 25 chars of user message as title
            std_db_util.create_chat_session(db, request.session_id, request.user_id, title)

        formatted_input = f"User Query:\n{request.user_query}\n" # Base User Query
        if request.query_content:   # Add attached file content if provided
            formatted_input += "\nAttached Files:\n"
            for idx, item in enumerate(request.query_content, start=1):
                formatted_input += f"\n[{idx}] Filename: {item.filename}\nContent:\n{item.content}\n"
        
        # DB Insertion of User Message
        std_db_util.insert_message(
            db, request.session_id, request.user_id, "user", request.user_query, attachments=request.query_content
        )
        db.commit()

        # Agent Response Streaming Generator
        async def event_stream() -> AsyncGenerator[str, None]:
            full_response = ""  # collecting the full response for DB insertion

            # Agents & Tools Initialization...
            agents, tools = await setup_agents_and_tools(
                db=db,
                session_id=request.session_id, 
                user_id=request.user_id, 
                model_id=request.model_id,
                agent_ids=request.agent_ids, 
            )

            try:
                async for response_chunk in setup_team(
                    agents=agents,
                    tools=tools,
                    user_query=formatted_input,
                    session_id=request.session_id,
                    user_id=request.user_id
                ):
                    full_response += str(response_chunk)
                    yield json.dumps({
                        "status": 200,
                        "response_chunk": response_chunk, 
                        "session_id": request.session_id,
                    }) + "\n"

                # Insert the collected response into DB once streaming is done
                std_db_util.insert_message(db, request.session_id, request.user_id, "agent", full_response)
                db.commit()

                # Disconnect all MCP server connections after completion
                for name, tool in reversed(list(tools.items())):
                    if name in MCPServerConfig.MCP_SERVERS_URL:
                        try:
                            await tool.close()
                            print(f"{name} MCP Server Connection Closed")
                        except Exception as e:
                            print(f"Error closing {name}: {e}")

            except Exception as e:
                error_message = str(e)
                db.rollback()
                # Handling model switch errors
                if ("Invalid value: 'tool_result'" in error_message or "`tool_use` ids were found without `tool_result`" in error_message):
                    updated_error_msg = (
                        "Switching models? Previous run data won’t carry over."
                        "To continue, stay with the same provider or start a new chat."
                    )
                else:
                    updated_error_msg = "[ERROR]" + error_message

                yield json.dumps({
                    "status": 500,
                    "response_chunk": f"{updated_error_msg}",
                    "session_id": request.session_id, 
                }) + "\n"

        return StreamingResponse(event_stream(), media_type="text/plain")

    except Exception as e:
        db.rollback()
        print(f"Error in chat_completion: {e}")
        return {
            "status": 500,
            "session_id": request.session_id,
            "error": str(e)
        }
    

@router.get("/chat-sessions/{user_id}")
def get_sessions(user_id: str, authorization: Optional[str] = Header(None), db: Session = Depends(std_db_util.get_db)):
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )
    
    try:
        sessions = std_db_util.fetch_sessions_by_user(db, user_id)
        return JSONResponse(status_code=200, content={"status": 200, "sessions": sessions})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": 500, "error": str(e)})


@router.get("/chat-messages/{user_id}/{session_id}")
def get_messages(user_id: str, session_id: str, authorization: Optional[str] = Header(None), db: Session = Depends(std_db_util.get_db)):
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    try:
        messages = std_db_util.fetch_messages_by_user_and_session(db, user_id, session_id)
        if not messages:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "error": "No messages found for given user and session"}
            )
        return JSONResponse(status_code=200, content={"status": 200, "messages": messages})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": 500, "error": str(e)})


