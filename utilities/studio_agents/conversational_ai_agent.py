from agno.agent import Agent
from configuration import SSTDConfig
from utilities.llm_manager import agno_llm_model
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.duckduckgo import DuckDuckGoTools
from utilities.prompt_templates import CONVERSATIONAL_AI_SYSTEM_PROMPT

conversational_ai_agent = Agent(
    name="Conversational AI Agent",
    role="Q&A Assistant",
    description="An AI assistant that answers questions using internal documentation knowledgebases, with fallback to Web Search Toolkit when needed.",
    system_message=CONVERSATIONAL_AI_SYSTEM_PROMPT,
    tools=[
        # DuckDuckGoTools(),
        GoogleSearchTools()
    ],
    model=agno_llm_model,  
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


