from agno.agent import Agent
from configuration import SSTDConfig
from configuration import JiraConfig
from utilities.llm_manager import agno_llm_model
from utilities.prompt_templates import UNIT_TESTCASE_GENERATOR_SYSTEM_PROMPT
from utilities.custom_tools.github_agno_toolkit import GithubTools
from agno.tools.jira import JiraTools

unit_test_generator_agent = Agent(
    name="Unit Test Agent",
    role="A developer-focused agent that creates, updates, audits, and optimizes unit test cases covering all scenarios",
    description="Generates comprehensive unit test cases covering positive, negative, edge cases, and boundary conditions."
    "Supports multiple testing frameworks and ensures maximum code coverage.",
    model=agno_llm_model,
    system_message=UNIT_TESTCASE_GENERATOR_SYSTEM_PROMPT,
    tools=[
        #JiraTools(server_url=JiraConfig.JIRA_API_URL),
        GithubTools(access_token="dummy"),
    ],
    show_tool_calls=True,
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






 