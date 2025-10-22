from typing import Dict
from agno.tools.mcp import MCPTools
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.storage.postgres import PostgresStorage
from urllib.parse import quote_plus  # For URL encoding

class JiraConfig:
    JIRA_API_URL = "https://your-domain.atlassian.net/rest/api/3"
    
class AzureKeyVaultConfig:
    SM_CLIENT_ID = ""
    SM_CLIENT_SECRET = ""                                  
    SM_URL = ""
    SM_TENANT_ID = ""

class AzureKeyVaultConfig2:
    SM_CLIENT_ID = ""
    SM_CLIENT_SECRET = ""
    SM_URL = ""
    SM_TENANT_ID = ""


class MCPServerConfig:
    MCP_CONNECTIONS: Dict[str, MCPTools] = {}
    MCP_SERVERS_URL = {
        # Add more servers as needed
        "ONEDRIVE_MCP_SERVER" : "http://localhost:8501/sse",
        "MERMAID_MCP_SERVER": "http://localhost:8503/sse", 
        "DASHBOARD_MCP_SERVER": "http://localhost:8504/sse",
        "SERVICE_NOW_MCP_SERVER" : "http://localhost:8505/sse",
        "GRAFANA_LOKI_MCP_SERVER" : "http://localhost:8506/sse",
        "DB_GENIE_MCP_SERVER": "http://localhost:8502/sse",
        "JIRA_MCP_SERVER": "http://localhost:8080/sse"
    }    


class AzureOpenAIConfig:
    # Store secrets directly in the file
    AZURE_OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
    AZURE_OPENAI_RESOURCE_NAME = "YOUR_OPENAI_RESOURCE_NAME"
    AZURE_OPENAI_DEPLOYMENT_ID = "YOUR_OPENAI_DEPLOYMENT_ID"
    AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
    AZURE_OPENAI_ENDPOINT = f"https://{AZURE_OPENAI_RESOURCE_NAME}.openai.azure.com/"
    AZURE_EMBEDDING_MODEL_NAME = 'text-embedding-ada-002'


class AzureOpenAIO4MiniConfig:
    """Configuration manager for Azure OpenAI service connections and operations."""
    AZURE_OPENAI_API_KEY_O4_MINI = "YOUR_O4_MINI_API_KEY"
    AZURE_OPENAI_ENDPOINT_O4_MINI = "YOUR_O4_MINI_ENDPOINT"
    AZURE_OPENAI_DEPLOYMENT_O4_MINI = "YOUR_O4_MINI_DEPLOYMENT_ID"
    AZURE_OPENAI_API_VERSION_O4_MINI = "YOUR_O4_MINI_API_VERSION"
    AZURE_EMBEDDING_MODEL_NAME = 'text-embedding-ada-002'


class AzureOpenAIGPT5Config:
    AZURE_OPENAI_API_KEY_GPT5 = "YOUR_GPT5_API_KEY"
    AZURE_OPENAI_ENDPOINT_GPT5 = "YOUR_GPT5_ENDPOINT"
    AZURE_OPENAI_API_VERSION_GPT5 = "YOUR_GPT5_API_VERSION"
    AZURE_OPENAI_DEPLOYMENT_GPT5_MINI = "gpt-5-mini"
    AZURE_OPENAI_DEPLOYMENT_GPT5_NANO = "gpt-5-nano"


class AWSClaudeConfig:
    AWS_ACCESS_ID = "YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS = "YOUR_AWS_SECRET_ACCESS_KEY"
    REGION_NAME = "YOUR_AWS_REGION"
    AWS_MODEL_ID_CLAUDE_3_7 = "YOUR_CLAUDE_3_7_MODEL_ID"
    AWS_MODEL_ID_CLAUDE_3_5 = "YOUR_CLAUDE_3_5_MODEL_ID"
    AWS_MODEL_ID_CLAUDE_4 = "YOUR_CLAUDE_4_MODEL_ID"
    ANTHROPIC_VERSION = "YOUR_ANTHROPIC_VERSION"
    AWS_GUARDRAIL_ID = "YOUR_GUARDRAIL_ID"
    AWS_GUARDRAIL_VERSION = "YOUR_GUARDRAIL_VERSION"


class PGVectorConfig:
    VECTORDB_PORT = "5432"
    VECTORDB_NAME = "crew_ai"
    VECTORDB_USER = "postgres"
    VECTORDB_PASS = "postgres"
    VECTORDB_HOST = "localhost"
    ENCODED_PASSWORD = quote_plus(VECTORDB_PASS) 
    VECTOR_DB_CONNECTION_STRING = f"postgresql+psycopg://{VECTORDB_USER}:{ENCODED_PASSWORD}@{VECTORDB_HOST}:{VECTORDB_PORT}/{VECTORDB_NAME}"


class SSTDConfig:
    SSTD_SCHEMA = "solution_studio"
    KB_TABLE = "knowledgebases"

    agent_memory_db = PostgresMemoryDb(
        table_name="agent_memory", 
        schema="solution_studio",
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING)
    
    team_memory_db = PostgresMemoryDb(
        table_name="team_memory", 
        schema="solution_studio",
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING)
    
    AGENT_STORAGE = PostgresStorage(
        table_name="agent_sessions", 
        schema="solution_studio",
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING)
    
    TEAM_STORAGE = PostgresStorage(
        table_name="team_sessions", 
        schema="solution_studio",
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING)
    
    from utilities.llm_manager import agno_llm_model
    AGENT_MEMORY = Memory(
        model=agno_llm_model,
        db=agent_memory_db

    )
    TEAM_MEMORY = Memory(
        model=agno_llm_model,
        db=team_memory_db
    )


class OKTAConfig:
    OKTA_ENABLED = False

    OKTA_JWT_OAUTH_CONFIG = {
        "client_id": "",
        "issuer_url": "",
    }



