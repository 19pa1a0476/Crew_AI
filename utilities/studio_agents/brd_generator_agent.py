from agno.agent import Agent
from configuration import SSTDConfig
from utilities.prompt_templates import BRD_GENERATOR_SYSTEM_PROMPT
from utilities.llm_manager import agno_llm_model

brd_generator_agent = Agent(
    name="BRD Builder Agent",
    role="BRD Builder Agent",
    description="To automate the generation of clear, structured, and accurate Business Requirement Documents (BRDs) from high-level input such as epics, user stories and generic documents as per the user input.",
    model=agno_llm_model,
    system_message= BRD_GENERATOR_SYSTEM_PROMPT,
    show_tool_calls=True,
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
