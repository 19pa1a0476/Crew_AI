from agno.agent import Agent
from configuration import SSTDConfig
from configuration import JiraConfig
from agno.tools.jira import JiraTools
from services.mcp_service import MCPServerManager
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import GENERATE_USER_STORY_SYSTEM_PROMPT
from utilities.custom_tools.github_agno_toolkit import GithubTools

ONEDRIVE_MCP_TOOLKIT = MCPServerManager().connect_server(toolkit_name="ONEDRIVE_MCP_SERVER")

user_story_agent = Agent(
    name="User Story Agent",
    role="JIRA User Story Generator Agent",
    description="Agile Business Analyst who writes concise Jira User Stories with acceptance criteria and tasks.",
    model=agno_llm_model,
    system_message=GENERATE_USER_STORY_SYSTEM_PROMPT,
    tools=[
        JiraTools(server_url=JiraConfig.JIRA_API_URL),
        GithubTools(access_token="dummy")
    ],
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