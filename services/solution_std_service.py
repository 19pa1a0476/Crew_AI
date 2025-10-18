from agno.agent import Agent, RunResponse
from configuration import MCPServerConfig
from services.mcp_service import MCPServerManager
from utilities.llm_manager import get_llm_model 
from agno.team import Team
from configuration import SSTDConfig
from sqlalchemy.orm import Session
from utilities.tools_library import TOOLKIT_LIBRARY
import utilities.sol_std_db_util as std_db_util
from typing import Dict, List, Any
from utilities.knowledgebase_retriever import KnowledgebaseRetriever
from agno.agent import ToolCallCompletedEvent

# In-memory storage of registered agents
AGENT_LIBRARY: Dict[str, Dict] = {}


def get_toolkit_config(agent_id: str, user_id: str, db: Session) -> Dict[str, Dict[str, Any]]:
    """
    Returns configuration fields and descriptions for tools associated with a given agent,
    along with prefilled values from the database (if available).

    Args:
        agent_id (str): Identifier of the agent.
        user_id (str): ID of the user to fetch saved config values.
        db (Session): SQLAlchemy DB session.

    Returns:
        dict: Mapping of tool names to their config fields, including default values.
    """
    if agent_id not in AGENT_LIBRARY:
        raise ValueError(f"Agent '{agent_id}' not found in agent library.")

    tools = AGENT_LIBRARY[agent_id].get("tools", [])
    result = {}

    # Fetch all config values from DB in one call
    db_config_values = std_db_util.fetch_tool_config(user_id=user_id, tool_names=tools, db=db)

    for tool_name in tools:
        if tool_name not in TOOLKIT_LIBRARY:
            print(f"Tool '{tool_name}' not found in toolkit library.")
            continue

        toolkit_entry = TOOLKIT_LIBRARY[tool_name]
        fields = toolkit_entry.get("config_schema", {}).get("fields", [])
        description = toolkit_entry.get("description", "")

        # Get user config for this tool from DB
        user_config = db_config_values.get(tool_name, {})

        # Add 'value' key to each field, using DB value if available
        enriched_fields = []
        for field in fields:
            key = field["key"]
            field_with_value = field.copy()
            field_with_value["value"] = user_config.get(key, "")  # Use DB value or empty string
            enriched_fields.append(field_with_value)

        result[tool_name] = {
            "config_fields": enriched_fields,
            "description": description
        }
    return result


def register_agent(agent: Agent):
    """
    Registers an Agent object into the AGENT_LIBRARY dictionary.
    """
    if not isinstance(agent, Agent):
        raise ValueError("Provided object is not an instance of Agent")

    agent_id = agent.name.replace(" ", "_").lower()
    AGENT_LIBRARY[agent_id] = {
        "agent_name": getattr(agent, "name", agent_id.replace("_", " ").title()),
        "tools": [tool.name for tool in agent.tools] if hasattr(agent, "tools") and agent.tools else [],
        "agent_object": agent  # Store the full Agent object
        # "role": getattr(agent, "role", None),
        # "instructions": getattr(agent, "instructions", []),
        # "description": getattr(agent, "description", ""),
        # "system_message": getattr(agent, "system_message", ""),
        
    }
    print(f"Agent '{agent_id}' registered successfully.")



async def initialize_tool_objects(tool_config: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    initialized_tools = {}
    for tool_name, config in tool_config.items(): 
        if tool_name in MCPServerConfig.MCP_SERVERS_URL:
            print("Connecting to MCP ToolKit...")
            mcp_toolkit = MCPServerManager().connect_server(
                toolkit_name=tool_name,
                tool_config=config
            )
            await mcp_toolkit.connect()
            initialized_tools[tool_name] = mcp_toolkit    
        else:
            tool_class = TOOLKIT_LIBRARY[tool_name]["tool_object"]
            initialized_tools[tool_name] = tool_class(**config)     
    return initialized_tools


def initialize_agents(session_id: str, user_id: str, model_id: str, agent_config: Dict[str, Dict[str, Any]], tool_instances: Dict[str, Any]) -> Dict[str, Agent]:
    agents = {}
    for agent_id, config in agent_config.items():
        # agents[agent_id] = build_updated_agent(user_id, agent_id, config, tool_instances)
        agents[agent_id] = build_agent(session_id, user_id, model_id, agent_id, config, tool_instances)
    return agents


async def setup_agents_and_tools(session_id: str, user_id: str, model_id: str, agent_ids: List[str], db):
    all_tools = list({t for aid in agent_ids for t in AGENT_LIBRARY[aid]["tools"]})
    agent_config = std_db_util.fetch_agent_config(user_id=user_id, agent_ids=agent_ids, db=db)
    tool_config = std_db_util.fetch_tool_config(user_id=user_id, tool_names=all_tools, db=db)
    tools = await initialize_tool_objects(tool_config)
    agents = initialize_agents(session_id, user_id, model_id, agent_config, tools)
    return agents, tools


def build_agent(
    session_id: str,    
    user_id: str,
    model_id: str,
    agent_id: str,
    config: Dict[str, Any],
    tool_instances: Dict[str, Any]
) -> Agent:
    """
    Builds a Agent using AGENT_LIBRARY defaults and config overrides.

    Parameters:
    - user_id (str): The ID of the user.
    - agent_id (str): The key to look up in AGENT_LIBRARY.
    - config (dict): Runtime overrides (enable_memory, markdown, knowledgebase_details, etc.)
    - tools (list): List of instantiated tool objects.

    Returns:
    - Agent: Constructed agent instance.
    """
    base_agent = AGENT_LIBRARY[agent_id]["agent_object"]
    kb_retriever = KnowledgebaseRetriever(
        user_id=user_id, 
        kb_list=config.get("knowledgebase_details", [])
    )

    if model_id:
        agent_model = get_llm_model(model_id=model_id)
    else:
        agent_model = getattr(base_agent, "model",  None)

    agent = Agent(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
        name=getattr(base_agent, "name", agent_id.replace("_", " ").title()),
        role=getattr(base_agent, "role",  ""),
        tools=[tool_instances[t] for t in AGENT_LIBRARY[agent_id]["tools"]],
        instructions=getattr(base_agent, "instructions",  ""),
        system_message=getattr(base_agent, "system_message",  ""),
        user_message=getattr(base_agent, "user_message",  ""),
        description=getattr(base_agent, "description",  ""),
        expected_output=getattr(base_agent, "expected_output",  ""),
        debug_mode=True,
        # show_tool_calls=True,
        telemetry=False,
        search_knowledge=True,
        memory=SSTDConfig.AGENT_MEMORY,
        storage=SSTDConfig.AGENT_STORAGE,
        model=agent_model,
        reasoning=getattr(base_agent, "reasoning",  False),
        reasoning_model=getattr(base_agent, "reasoning_model",  None),
        reasoning_max_steps=getattr(base_agent, "reasoning_max_steps", 3),
        reasoning_min_steps=getattr(base_agent, "reasoning_min_steps", 1),
        enable_user_memories=config.get("enable_memory", True),
        enable_agentic_memory=config.get("enable_memory", True),
        add_history_to_messages=config.get("enable_memory", True),
        # context=config.get("context", {}),
        # add_context=True,
        markdown=True,
        num_history_runs=config.get("num_history_runs", 3),
        retriever=kb_retriever.get_retriever()
    )

    print(f"Inside Build Agent - Using Agent instance ID: {id(agent)}")
    print(f"Inside Build Agnet - Using retriever function ID: {id(agent.retriever)}")
    print(f"Inside Build Agnet - KB List: {config.get("knowledgebase_details", [])}")
    return agent


# Helper Function for Formatting the Tool Execution Responses
def format_tool_execution_message(
    tool_display: str,
    exec_time: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    tool_call_error: bool = False
) -> str:
    """
    Create a user-friendly markdown message for a completed tool call or error, including tool details always and token usage only if input and output tokens are not both zero and no error occurred.
    """
    if tool_call_error:
        return f"""
⚠️ **Tool Execution Error**  
**Tool:** `{tool_display}`  
**Status:** Retrying due to an error in the tool call.  
"""
    tool_execution_message = f"""
**Tool Execution Completed**  
**Tool:** `{tool_display}`  
**Execution Time:** {exec_time}  
"""
    if input_tokens != 0 and output_tokens != 0:
        tool_execution_message += f"""
**Token Usage:**  
- Input Tokens: {input_tokens}  
- Output Tokens: {output_tokens}  
- Total Tokens: {total_tokens}  
"""
    return tool_execution_message


async def setup_team(agents: Dict[str, Agent], tools, user_query: str, session_id: str, user_id: str):
    # Check if any agent has enable_agentic_memory == True
    agentic_memory_flag = any(
        getattr(agent, "enable_agentic_memory", False) for agent in agents.values()
    )

    for agent in agents.values():
        response_stream: RunResponse = await agent.arun(user_query, stream=True)
        async for chunk in response_stream:
            if isinstance(chunk, ToolCallCompletedEvent):
                tool = chunk.tool
                if tool:
                    # Format tool name with parameters
                    params_str = ", ".join([f"{k}={v}" for k, v in (tool.tool_args or {}).items()])
                    tool_display = f"{tool.tool_name or 'Unknown Tool'} - {{{params_str[:20] + '...' if len(params_str) > 20 else params_str}}}" if params_str else f"{tool.tool_name or 'Unknown Tool'}"

                    if tool.metrics:
                        exec_time = f"{tool.metrics.time:.3f}s" if tool.metrics.time else "N/A"
                        input_tokens = tool.metrics.input_tokens or 0
                        output_tokens = tool.metrics.output_tokens or 0
                        total_tokens = input_tokens + output_tokens
                    else:
                        exec_time = "N/A"
                        input_tokens = output_tokens = total_tokens = 0

                    tool_response = format_tool_execution_message(
                        tool_display, 
                        exec_time, 
                        input_tokens, 
                        output_tokens, 
                        total_tokens, 
                        tool_call_error=tool.tool_call_error or False
                    )
                    print(tool_response)
                    yield tool_response
            else:
                if chunk.content:
                    yield chunk.content

        images = agent.run_response.images
        if images and isinstance(images, list):
            header = "- **Generated Images**\n\n"
            yield header  

            for idx, image_response in enumerate(images, start=1):
                markdown_snippet = (
                    f"- Format: {image_response.mime_type}\n\n"
                    f"![Image {idx}](data:{image_response.mime_type};base64,{image_response.content.decode()})\n\n"
                )
                yield markdown_snippet
                # with open("output.md", "a") as f:
                #     f.write(markdown_snippet)

        # return agent.arun(user_query)

    # team = Team(
    #     name="Chat Completion Team",
    #     description=("Team of agents collaboratively answering the user query."),
    #     session_id=session_id,
    #     instructions=("Ensure the task is properly delegated among members based on their roles and capabilities."
    #     "Make Sure you pass proper context while delegating the tasks (i.e user_query and necessary context about it)"),
    #     user_id=user_id,
    #     model=agno_llm_model,
    #     mode="coordinate",
    #     members=list(agents.values()),  # Dynamically add all agent objects
    #     tools=list(tools.values()),
    #     show_members_responses=True,
    #     search_knowledge=True,
    #     markdown=True,
    #     memory=SSTDConfig.TEAM_MEMORY,
    #     storage=SSTDConfig.TEAM_STORAGE,
    #     share_member_interactions=True,
    #     get_member_information_tool=True,
    #     add_member_tools_to_system_message=True,
    #     enable_agentic_memory=agentic_memory_flag,
    #     enable_user_memories=agentic_memory_flag,
    #     enable_session_summaries=agentic_memory_flag,
    #     enable_team_history=agentic_memory_flag,
    #     debug_mode=True,
    #     telemetry=False
    # )
    # return team.arun(user_query)