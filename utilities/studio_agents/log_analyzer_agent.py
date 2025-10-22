from agno.agent import Agent
from configuration import SSTDConfig
from services.mcp_service import MCPServerManager
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.llm_manager import agno_llm_model,agno_llm_model_claude_3_7
from utilities.prompt_templates import LOG_ANALYZER_PROMPT_TEMPLATE

GRAFANA_TOOLKIT = MCPServerManager().connect_server(toolkit_name="GRAFANA_LOKI_MCP_SERVER")
SERVICE_NOW_TOOLKIT = MCPServerManager().connect_server(toolkit_name="SERVICE_NOW_MCP_SERVER")


log_analyzer_agent = Agent(
    name="Log Analyzer Agent",
    role="Log Analyzer and RCA Assistant",
    description="An MCP server to fetch the logs related to the user query and provide the RCA report and code resolution for the issue ",
    system_message=LOG_ANALYZER_PROMPT_TEMPLATE,
    tools=[SERVICE_NOW_TOOLKIT,GRAFANA_TOOLKIT, GithubTools(access_token="dummy")],
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