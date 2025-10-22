from agno.agent import Agent
from configuration import SSTDConfig
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import CODE_CONVERSION_SYSTEM_PROMPT


code_conversion_agent = Agent(
    name="Code Converter Agent",
    role="Converts code from a source language to a target language with structural fidelity.",
    model=agno_llm_model, 
    description="""
You are an expert programming language translator that supports all major programming languages.
You convert source code to target code cleanly, accurately, and in a production-ready format.
You handle complex logic, functions, control structures, data types, and even platform-specific syntax (e.g., SQL dialects, JVM-based code, etc.).
Do not include explanations — output only the target code in valid syntax.
""",
    instructions=[CODE_CONVERSION_SYSTEM_PROMPT],
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