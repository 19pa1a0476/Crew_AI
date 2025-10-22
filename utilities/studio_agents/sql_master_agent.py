from agno.agent import Agent
from configuration import SSTDConfig
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import DB_GENIUS_SYSTEM_PROMPT
from utilities.custom_tools.sql_agno_toolkit import SQLTools

sql_master_agent = Agent(
    name="SQL Master Agent",
    role="SQL Query Expert",
    description="An AI assistant specialized in explaining SQL concepts, converting natural language to SQL queries, and optimizing SQL queries for any SQL database dialect.",
    system_message=DB_GENIUS_SYSTEM_PROMPT,
    model=agno_llm_model,
    tools= [SQLTools()], 
    debug_mode=True,
    telemetry=True,
    search_knowledge=True,
    memory=SSTDConfig.AGENT_MEMORY,
    storage=SSTDConfig.AGENT_STORAGE,
    enable_user_memories=True,
    enable_agentic_memory=True,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True
)

