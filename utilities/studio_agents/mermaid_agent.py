from agno.agent import Agent
from configuration import SSTDConfig
from services.mcp_service import MCPServerManager
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import MERMAID_PROMPT_TEMPLATE

MERMAID_TOOLKIT = MCPServerManager().connect_server(toolkit_name="MERMAID_MCP_SERVER")


mermaid_agent = Agent(
    name="MermaidCrafter Agent",
    role="Mermaid Flowchart Assistant",
    description="An MCP server for generating mermaid flow diagrams from user prompts.",
    system_message=MERMAID_PROMPT_TEMPLATE,
    tools=[MERMAID_TOOLKIT, GithubTools(access_token="dummy")],
    model=agno_llm_model,  
    debug_mode=True,
    telemetry=False,
    search_knowledge=True,
    memory=SSTDConfig.AGENT_MEMORY,
    storage=SSTDConfig.AGENT_STORAGE,
    enable_user_memories=True,
    enable_agentic_memory=True,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True
)