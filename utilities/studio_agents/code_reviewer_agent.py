from agno.agent import Agent
from configuration import SSTDConfig
from agno.tools.jira import JiraTools
from configuration import JiraConfig
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.prompt_templates import CODE_REVIEWER_AGENT_SYSTEM_PROMPT
from utilities.llm_manager import agno_llm_model

code_reviewer_agent = Agent(
    name="Code Reviewer Agent",
    # model=agno_llm_model,
    model = agno_llm_model,
    description="Review the provided Pull Request and add the review comment over the Pull Request",
    tools=[
        GithubTools(access_token="dummy"),
        JiraTools(server_url=JiraConfig.JIRA_API_URL)
    ],
    show_tool_calls=True,
    system_message=CODE_REVIEWER_AGENT_SYSTEM_PROMPT,
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