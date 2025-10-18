from agno.agent import Agent
from configuration import SSTDConfig
from configuration import JiraConfig
from agno.tools.jira import JiraTools
from agno.tools.reasoning import ReasoningTools
from services.mcp_service import MCPServerManager
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import MANUAL_TESTCASE_GENERATOR_PROMPT

ONEDRIVE_MCP_TOOLKIT = MCPServerManager().connect_server(toolkit_name="ONEDRIVE_MCP_SERVER")

testcase_generator_agent = Agent(
    name="Test Case Generator",
    role="A QA-focused agent that creates, updates, optimizes and review manual test cases based on user input",
    description="Generates high-quality structured manual test cases using white-box techniques. Supports new features, changes, reviews, and sync with Jira.",
    model=agno_llm_model,
    system_message=MANUAL_TESTCASE_GENERATOR_PROMPT,
    tools=[
        JiraTools(server_url=JiraConfig.JIRA_API_URL),
        ReasoningTools(True),
        ONEDRIVE_MCP_TOOLKIT
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