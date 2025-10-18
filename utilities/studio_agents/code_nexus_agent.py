from agno.agent import Agent
from configuration import SSTDConfig
from utilities.llm_manager import agno_llm_model_claude_3_7
from utilities.prompt_templates import CODE_GEN_REFACTOR_SYSTEM_PROMPT

code_nexus_agent = Agent(
    name="Code Nexus Agent",
    role="Handles code generation, optimization, and refactoring based on user input.",
    description="""
        You are a multi-capable AI developer assistant. Based on the user's instruction, 
        you can generate new code, optimize existing code, or refactor code to upgrade versions.
        Only return the code unless the user asks for explanation.
    """,
    system_message=CODE_GEN_REFACTOR_SYSTEM_PROMPT,
    model=agno_llm_model_claude_3_7,
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

