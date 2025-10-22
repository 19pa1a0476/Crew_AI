from agno.agent import Agent
from configuration import SSTDConfig
from utilities.prompt_templates import TEST_SCRIPT_GENERATOR_SYSTEM_PROMPT
from utilities.llm_manager import agno_llm_model

test_script_generator_agent = Agent(
    name="Test Script Generator",
    description="Generates test scripts from the user provided prompt, language, and framework",
    role="Generates test scripts from the validated prompt, language, and framework.",
    model=agno_llm_model,
    system_message=TEST_SCRIPT_GENERATOR_SYSTEM_PROMPT,
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