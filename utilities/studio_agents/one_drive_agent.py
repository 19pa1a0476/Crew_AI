from agno.agent import Agent
from configuration import SSTDConfig
from services.mcp_service import MCPServerManager
from utilities.llm_manager import agno_llm_model

ONEDRIVE_TOOLKIT = MCPServerManager().connect_server(toolkit_name="ONEDRIVE_MCP_SERVER")

onedrive_agent = Agent(
    name="One Drive Agent",
    role="One Drive Assistant",
    system_message="Only Use Tools provided nothing else to answer user query",
    tools=[ONEDRIVE_TOOLKIT],
    description="""An Agent for interacting with Microsoft OneDrive via Graph API.
    Provides tools for listing, searching, getting content of files/folders, and uploading files.""",
    instructions="""
        Only answer queries related to Microsoft OneDrive files and folders.
        Use the provided tools to list, search, upload and get the file content.
        Before getting the file content make sure you get the proper file path for given file.
        Try to provide the file urls as proper hyperlink if available.
        Do not provide information outside OneDrive scope.
        If the answer is not available, inform the user. Keep responses clear and ask for clarification if needed
    """,
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