from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.jira import JiraTools
from a2a.types import AgentCard
from services.a2a_service import create_agent_card
from agno.models.azure import AzureOpenAI
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.memory import Memory
from utilities.prompt_templates import QUERY_GENERATION_PROMPT
from typing import Dict, Any, List, Optional
from utilities.llm_manager import embedding_model, agno_llm_model
from configuration import AzureOpenAIConfig, PGVectorConfig, JiraConfig
from utilities.custom_tools.metadata_builder_tool import MetadataBuilderTools
from utilities.custom_tools.agent_onboarding_toolkit import ExternalAgentToolkit
from utilities.custom_tools.order_details_tool import OrderDetailsTools
from agno.tools.twilio import TwilioTools
from utilities.custom_tools.github_tool import GitHubTools
from utilities.pg_sql_db_util import (
    SessionLocal,
    get_user_agent_by_id,
    create_user_agent,
    delete_user_agent,
    get_user_agents
)


# Setup for memory and storage 
postgres_url = PGVectorConfig.VECTOR_DB_CONNECTION_STRING
memory_db = PostgresMemoryDb(table_name="agent_memory", db_url=postgres_url)
storage = PostgresStorage(table_name="agent_sessions", db_url=postgres_url)
memory = Memory(db=memory_db)

# Registries
agent_registry = {}  # System predefined agents
user_agent_registry = {}  # User-defined agents, structured as {user_id: {agent_id: Agent}}
agent_cards_registry: Dict[str, AgentCard] = {}

tool_registry = {
    "File Reader/Writer Toolkit": FileTools,
    "JIRA Toolkit": lambda: JiraTools(
        server_url=JiraConfig.JIRA_API_URL,
        # username="sample@gmail.com",
        # password=JiraConfig.API_TOKEN
    ),
    "Internet Search Toolkit": DuckDuckGoTools,
    "Twilio Toolkit": TwilioTools,
    "Order Details Toolkit": OrderDetailsTools,
    "Crew-AI Agent Toolkit": ExternalAgentToolkit
}


def initialize_agents(mcp_manager):
    """Call this after MCP manager is connected"""
    global agent_registry
    global agent_cards_registry

    file_reader = Agent(
        name="File Reader",
        role="Expert at reading files",
        tools=[FileTools()],
        model=agno_llm_model,
        memory=memory,
        enable_user_memories=True,
        debug_mode=True,
        telemetry=True,
        enable_agentic_memory=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
        add_context=True,
        add_state_in_messages=True,
        context={},
    )
    agent_registry["File Reader"] = file_reader
    agent_cards_registry["File Reader"] = create_agent_card(agent=file_reader)

    jira_agent = Agent(
        name="User Story Generator",
        role="Expert at extracting the business requirements from provided content and generating the jira user story and uploading it to jira if possible",
        tools=[JiraTools(
            server_url=JiraConfig.JIRA_API_URL,
            # username="sample@gmail.com",
            # password=JiraConfig.API_TOKEN
        )],
        model=agno_llm_model,
        memory=memory,
        enable_user_memories=True,
        debug_mode=True,
        telemetry=True,
        enable_agentic_memory=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
        add_context=True,
        add_state_in_messages=True,
        context={},
    )
    agent_registry["User Story Generator"] = jira_agent
    agent_cards_registry["User Story Generator"] = create_agent_card(agent=jira_agent)


    query_generator = Agent(
        name="Transformation Query Generator",
        role="Expert at generating the queries for provided query languages like cypher, SQL, PostGreSQL etc using the provided mapping data for various attributes, rules and database schema as additional context",
        tools=[GitHubTools(), MetadataBuilderTools()],
        system_message= QUERY_GENERATION_PROMPT,
        model=agno_llm_model,
        memory=memory,
        enable_user_memories=True,
        enable_agentic_memory=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        debug_mode=True,
        telemetry=True,
        markdown=True,
        add_context=True,
        add_state_in_messages=True,
        context={
            # "language": "SQL",
            # "table_info": table_info,
            # "metadata": metadata
        },
    )
    agent_registry["Transformation Query Generator"] = query_generator
    agent_cards_registry["Transformation Query Generator"] = create_agent_card(agent=query_generator)


    test_cases_generator = Agent(
        name="Test Cases Generator",
        role="Expert at generating the Manual Test Cases",
        tools=[],
        # system_message= "Generate the test cases for all the attributes",
        model=agno_llm_model,
        # instructions=test_cases_instructions,
        memory=memory,
        enable_user_memories=True,
        enable_agentic_memory=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
        debug_mode=True,
        telemetry=True,
        add_context=True,
        add_state_in_messages=True,
        context={
            # "sql_query": sql_query,
            # "table_info": table_info,
            # "metadata": metadata
        },
    )

    agent_registry["Test Cases Generator"] = test_cases_generator
    agent_cards_registry["Test Cases Generator"] = create_agent_card(agent=test_cases_generator)


    test_script_generator = Agent(
        name="Test Script Generator",
        role="Expert at generating the test scripts for provided Manual Test Cases or requirements",
        tools=[],
        # system_message= "Generate the test cases for all the attributes",
        model=agno_llm_model,
        # instructions=test_cases_instructions,
        memory=memory,
        enable_user_memories=True,
        enable_agentic_memory=True,
        debug_mode=True,
        telemetry=True,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=3,
        markdown=True,
        add_context=True,
        add_state_in_messages=True,
        context={
            # "sql_query": sql_query,
            # "table_info": table_info,
            # "metadata": metadata
        },
    )
    agent_registry["Test Script Generator"] = test_script_generator
    agent_cards_registry["Test Script Generator"] = create_agent_card(agent=test_script_generator)


def load_user_agents(user_id: int):
    """Load user-defined agents from the database"""
    if user_id not in user_agent_registry:
        user_agent_registry[user_id] = {}
    
    with SessionLocal() as db:
        db_agents = get_user_agents(db, user_id)
        
        for db_agent in db_agents:
            # Create tools for the agent
            agent_tools = []
            for tool_name in db_agent.tools:
                if tool_name in tool_registry:
                    tool_factory = tool_registry[tool_name]
                    agent_tools.append(tool_factory() if callable(tool_factory) else tool_factory)
            
            # Create Agent instance
            agent = Agent(
                name=db_agent.name,
                role=db_agent.role,
                tools=agent_tools,
                model=agno_llm_model,
                memory=memory if db_agent.enable_memory else None,
                enable_user_memories=db_agent.enable_memory,
                enable_agentic_memory=db_agent.enable_memory,
                storage=storage,
                debug_mode=True,
                telemetry=True,
                add_history_to_messages=True,
                num_history_runs=db_agent.num_history_runs,
                markdown=db_agent.markdown,
                add_context=True,
                add_state_in_messages=True,
                context={},
            )
            
            # Add to user agent registry
            user_agent_registry[user_id][db_agent.agent_id] = agent

            # print(str(user_agent_registry))


def get_available_tools() -> List[str]:
    return list(tool_registry.keys())

def get_agent_card_and_skills(agent_name: str) -> AgentCard:
    card = agent_cards_registry.get(agent_name)
    if not card:
        raise ValueError(f"No AgentCard found for '{agent_name}'")
    return card

def create_new_agent(name: str, role: str, tool_names: List[str] = None,
                     enable_memory: bool = True, markdown: bool = True,
                     num_history_runs: int = 3, metadata: Dict[str, Any] = None,
                     user_id: Optional[int] = None) -> Agent:
    """Create a new agent and optionally store in the database if user_id is provided"""
    agent_id = name.lower().replace(" ", "_")
    tools = []

    if tool_names:
        for tool_name in tool_names:
            if tool_name in tool_registry:
                tool_factory = tool_registry[tool_name]
                tools.append(tool_factory() if callable(tool_factory) else tool_factory)
            else:
                raise ValueError(f"Tool '{tool_name}' not found.")

    agent = Agent(
        name=name,
        role=role,
        tools=tools,
        model=agno_llm_model,
        memory=memory if enable_memory else None,
        enable_user_memories=enable_memory,
        enable_agentic_memory=enable_memory,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=num_history_runs,
        markdown=markdown,
        add_context=True,
        add_state_in_messages=True,
        context={},
    )
    
    
    # If this is a system agent, add to agent_registry
    if user_id is None:
        agent_registry[agent_id] = agent
    else:
        # If this is a user agent, add to user_agent_registry and database
        if user_id not in user_agent_registry:
            user_agent_registry[user_id] = {}
        
        user_agent_registry[user_id][agent_id] = agent
        
        # Store in database
        with SessionLocal() as db:
            create_user_agent(
                db=db,
                user_id=user_id,
                agent_id=agent_id,
                name=name,
                role=role,
                tools=tool_names or [],
                enable_memory=enable_memory,
                markdown=markdown,
                num_history_runs=num_history_runs,
                metadata=metadata
            )
    
    return agent

def get_agent_by_name(name: str, user_id: Optional[int] = None) -> Agent:
    """Get an agent by name, checking user-defined agents first if user_id is provided"""
    name_lower = name.lower()
    
    # Check user-specific agents first if user_id is provided
    if user_id is not None and user_id in user_agent_registry:
        user_agents = user_agent_registry[user_id]
        if name_lower in user_agents:
            return user_agents[name_lower]
        
        # Check if name is an agent_id in database but not loaded yet
        with SessionLocal() as db:
            db_agent = get_user_agent_by_id(db, user_id, name_lower)
            if db_agent:
                load_user_agents(user_id)
                if name_lower in user_agent_registry[user_id]:
                    return user_agent_registry[user_id][name_lower]
    
    # Check system agents
    for agent_name, agent in agent_registry.items():
        if agent_name.lower() == name_lower:
            return agent
    
    raise ValueError(f"Agent '{name}' not found in registry")

def run_agent_with_context(agent_name: str, prompt: str, context: Dict[str, Any] = None, workflow_id: Optional[str] = None, user_id: Optional[int] = None) -> Any:
    """Run an agent with the specified context, checking user-defined agents if user_id is provided"""
    agent = get_agent_by_name(agent_name, user_id)
    agent.session_id = f"{agent_name}+{workflow_id}"
    agent.user_id = str(user_id)
    run_context = agent.context.copy() if hasattr(agent, "context") else {}
    if context:
        run_context.update(context)

    context_str = ""
    if context and len(context) > 0:
        context_str = "\n\n## Context from Previous Steps:\n"
        for key, value in context.items():
            if "output" in key.lower() or "result" in key.lower():
                context_str += f"\n### {key}:\n{value}\n"
            else:
                context_str += f"\n- {key}: {value}\n"

    enhanced_prompt = f"{prompt}\n{context_str}" if context_str else prompt
    return agent.arun(enhanced_prompt, context=run_context)

def get_all_available_agents(user_id: Optional[int] = None) -> List[str]:
    """Get list of all available agents including system and user-defined agents"""
    agents = list(agent_registry.keys())
    
    if user_id is not None:
        # Load user agents if they haven't been loaded yet
        if user_id not in user_agent_registry:
            load_user_agents(user_id)
        
        # Add user-defined agents
        if user_id in user_agent_registry:
            agents.extend(list(user_agent_registry[user_id].keys()))
    
    return agents

def delete_user_agent(user_id: int, agent_id: str) -> bool:
    """Delete a user-defined agent"""
    if user_id in user_agent_registry and agent_id in user_agent_registry[user_id]:
        del user_agent_registry[user_id][agent_id]
    
        with SessionLocal() as db:
            return delete_user_agent(db, user_id, agent_id)
    
    return False





