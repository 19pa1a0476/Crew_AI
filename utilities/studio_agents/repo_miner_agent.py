from agno.agent import Agent
from configuration import SSTDConfig
from utilities.llm_manager import agno_llm_model
from agno.tools.googlesearch import GoogleSearchTools
from utilities.custom_tools.github_agno_toolkit import GithubTools
from utilities.prompt_templates import REPO_MINER_SYSTEM_PROMPT


repo_miner_agent = Agent(
    name="Repo Miner Agent",
    role="Q&A Assistant",
    description="An AI assistant that answers questions using internal documentation knowledgebases, with fallback to Gihub Toolkit and Web Search when needed.",
    system_message=REPO_MINER_SYSTEM_PROMPT,
    instructions=[
        "Always attempt to answer using the internal knowledgebase first.",
        "If the internal knowledgebase does not contain the answer, use Github Toolkit and Google Search to gather information.",
        "Clearly indicate when your response is based on external sources.",
        "Ask follow-up questions if user input is ambiguous."
    ],
    tools=[
        GoogleSearchTools(),
        GithubTools(access_token="dummy"),
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


