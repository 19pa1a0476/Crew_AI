from agno.agent import Agent
from configuration import SSTDConfig
from agno.tools.reasoning import ReasoningTools
from services.mcp_service import MCPServerManager
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import XDATA_ANALYTICS_PROMPT

DASHBOARD_TOOLKIT = MCPServerManager().connect_server(toolkit_name="DASHBOARD_MCP_SERVER")

xdata_analytics_agent = Agent(
        name="XData Analytics Agent",
        role="Data Insights & Visualization Assistant",
        description="Provides data-driven insights with clear analysis and visualization guidance.",
        system_message = XDATA_ANALYTICS_PROMPT,
        model=agno_llm_model,
        tools=[DASHBOARD_TOOLKIT,ReasoningTools(True)],
        memory=SSTDConfig.AGENT_MEMORY,
        storage=SSTDConfig.AGENT_STORAGE,
        enable_agentic_memory=True,
        enable_user_memories=True,
        num_history_runs=3,
        add_history_to_messages=True,
        read_chat_history=True,
        search_knowledge=True,
        debug_mode=True,
        telemetry= False,
        show_tool_calls=True,
        markdown=True,
    )