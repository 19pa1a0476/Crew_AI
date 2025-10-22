from agno.models.aws import Claude
from agno.models.azure import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.azure_openai import AzureOpenAIEmbedder
from langchain_openai.chat_models.azure import AzureChatOpenAI
from utilities.custom_pg_vector import PgVector as CustomPGVector
from utilities.custom_pg_vector import SearchType as CustomSearchType
from configuration import (
    AzureOpenAIConfig, 
    PGVectorConfig, 
    AzureOpenAIO4MiniConfig,
    AzureOpenAIGPT5Config,
    AWSClaudeConfig
)
from google import genai

# Initialize Gemini client
gemini_client = genai.Client(api_key="YOUR API KEY")  # Replace with your real key
agno_llm_model = {
    "client": gemini_client,
    "model_name": "gemini-2.5-flash",  # or gemini-1.5-pro depending on what’s enabled in your account
}

LLM_MODEL_DICT = {
    "gpt-4o-mini" : agno_llm_model,
    "gpt-o4-mini" : agno_llm_model,
    "gpt-5-mini" : agno_llm_model,
    "gpt-5-nano" : agno_llm_model,
    "claude-sonnet-3.7" : agno_llm_model,
    "claude-haiku-3.5" : agno_llm_model,
    "claude-opus-4" : agno_llm_model,
    "default" : agno_llm_model,
}

def get_vector_db(schema: str, table_name: str) -> PgVector:
    return PgVector(
        schema=schema,
        table_name=table_name,
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING,
        embedder=agno_llm_model,
        search_type=SearchType.hybrid,
    )

def get_custom_vector_db(schema: str, table_name: str) -> CustomPGVector:
    return CustomPGVector(
        schema=schema,
        table_name=table_name,
        db_url=PGVectorConfig.VECTOR_DB_CONNECTION_STRING,
        embedder=agno_llm_model,
        search_type=CustomSearchType.hybrid,
    )

def get_llm_model(model_id: str):
    if model_id.lower() in LLM_MODEL_DICT:
        return LLM_MODEL_DICT[model_id.lower()]
    else:
        # Optional: log or raise
        print(f"[WARN] Invalid model_id '{model_id}', falling back to default - GPT-4o-Mini")
        return LLM_MODEL_DICT["default"]