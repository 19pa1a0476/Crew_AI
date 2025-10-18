from agno.agent import Agent
from configuration import SSTDConfig
from agno.tools.reasoning import ReasoningTools
from utilities.llm_manager import agno_llm_model
from utilities.custom_tools.sql_agno_toolkit import SQLTools
from utilities.prompt_templates import SYNTHETIC_TEST_DATA_AGENT_PROMPT

synthetic_data_agent = Agent(
    name="Synthetic Data Agent",
    model=agno_llm_model,
    # knowledge= knowledge_base, 
    tools=[ 
        # FileTools(synthetic_data_dir), 
        SQLTools(),
        ReasoningTools(True)
    ],
    instructions=[SYNTHETIC_TEST_DATA_AGENT_PROMPT],
    memory=SSTDConfig.AGENT_MEMORY,
    storage=SSTDConfig.AGENT_STORAGE,
    enable_agentic_memory=True,
    enable_user_memories=True,
    add_history_to_messages=True,
    num_history_runs=1,
    search_knowledge = True,
    markdown=True,
    show_tool_calls=True,
    debug_mode=True,
    telemetry=True,
)