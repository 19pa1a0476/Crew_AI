from agno.agent import Agent
from configuration import SSTDConfig
from configuration import JiraConfig
from agno.tools.jira import JiraTools
from agno.tools.reasoning import ReasoningTools
from utilities.prompt_templates import IMPACT_ANALYZER_SYSTEM_PROMPT
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.llm_manager import agno_llm_model

impact_analyzer_agent = Agent(
    name="Impact Analyzer Agent",
    role="Impact Analyzer Assistant",
    model = agno_llm_model,
    description="Analyze the potential impact of user story across the code files, identifying the affected components, risks, and testing requirements.",
    system_message=IMPACT_ANALYZER_SYSTEM_PROMPT,
    tools=[
        JiraTools(server_url=JiraConfig.JIRA_API_URL),
        GithubTools(access_token="dummy"),
        ReasoningTools(True)
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