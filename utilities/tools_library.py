import os
from agno.tools.mcp import MCPTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.jira import JiraTools
from configuration import JiraConfig
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.duckduckgo import DuckDuckGoTools
from utilities.custom_tools.sql_agno_toolkit import SQLTools
from utilities.custom_tools.github_agno_toolkit import GithubTools

# Dummy Values for by passing the Toolkit Validation Checks
os.environ["JIRA_SERVER_URL"] = JiraConfig.JIRA_API_URL
os.environ["GITHUB_ACCESS_TOKEN"] = "dummy_token"
os.environ["DUMMY_DB_URL"] = "postgresql://username:password@localhost:5432/dbname"

TOOLKIT_LIBRARY = {
    "jira_tools": {
        "description": "Jira Toolkit",
        "config_schema": {
            "fields": [
                {
                    "key": "server_url",
                    "description": "The base URL of your JIRA server (e.g., https://your-domain.atlassian.net)",
                    "type": "string",
                    "required": True
                },
                {
                    "key": "username",
                    "description": "Your JIRA username or email address used to authenticate",
                    "type": "string",
                    "required": True
                },
                {
                    "key": "token",
                    "description": "API token or personal access token for authenticating with JIRA",
                    "type": "password",
                    "required": True
                }
            ]
        },
        "tool_object": JiraTools  # Tool instance stored here
    },

    "github": {
        "description": "GitHub Toolkit",
        "config_schema": {
            "fields": [
                {
                    "key": "access_token",
                    "description": "Personal Access Token",
                    "type": "password",
                    "required": True
                },
                {
                    "key": "base_url",
                    "description": "Optional base URL for GitHub Enterprise instances (e.g., https://github.company.com/api/v3)",
                    "type": "string",
                    "required": False
                }
            ]
        },
        "tool_object": GithubTools  # Tool instance stored here
    },

    "google_search_tools": {
        "description": "Google Search Toolkit",
        "config_schema": {
            "fields": []
        },
        "tool_object": GoogleSearchTools  # Tool instance stored here
    },

    "duckduckgo": {
        "description": "Web Search Toolkit",
        "config_schema": {
            "fields": []
        },
        "tool_object": DuckDuckGoTools  # Tool instance stored here
    },

    "sql_tools": {
        "description": "SQL DB Toolkit",
        "config_schema": {
            "fields": [
                {
                    "key": "db_url",
                    "description": "Database Connection String (Encoded Password)",
                    "type": "password",
                    "required": True
                }
            ]
        },
        "tool_object": SQLTools  # Tool instance stored here
    },

    "reasoning_tools": {
        "description": "Reasoning Toolkit",
        "config_schema": {
            "fields": [
                # {
                #     "key": "Think",
                #     "description": "Think",
                #     "type": "toggle",
                #     "required": True
                # }
            ]
        },
        "tool_object": ReasoningTools  # Tool instance stored here
    },

    "ONEDRIVE_MCP_SERVER": {
        "description": "MCP Server Toolkit for interacting with OneDrive",
        "config_schema": {
            "fields": [
                {
                    "key": "user-email",
                    "description": "OneDrive email of user",
                    "type": "email",
                    "required": True
                },
                {
                    "key": "client-id",
                    "description": "OneDrive Client ID",
                    "type": "password",
                    "required": True
                },
                {
                    "key": "client-secret",
                    "description": "OneDrive Client Secret Key",
                    "type": "password",
                    "required": True
                },                
                {
                    "key": "tenant-id",
                    "description": "OneDrive Client Tenant ID",
                    "type": "password",
                    "required": True
                }
            ]
        },
        "tool_object": MCPTools  # Tool instance stored here
    },
    
    "MERMAID_MCP_SERVER": {
        "description": "MCP Server Toolkit for generating mermaid flow diagrams",
        "config_schema": {
            "fields": [
                # No specific fields required for this toolkit
            ]
        },
        "tool_object": MCPTools  # Tool instance stored here
    },

    "DASHBOARD_MCP_SERVER": {
        "description": "MCP server for generating charts/dashboards.",
        "config_schema": {
            "fields": [
                # No specific fields required for this toolkit
            ]
        },
        "tool_object": MCPTools  
    },

    "SERVICE_NOW_MCP_SERVER": {
        "description": "MCP Server Toolkit for interacting with Service-Now Instance",
        "config_schema": {
            "fields": [
                {
                    "key": "service-now-instance-url",
                    "description": "Service-Now Instance URL: https://xyz.service-now.com",
                    "type": "url",
                    "required": True
                },
                {
                    "key": "service-now-username",
                    "description": "Service-Now Username",
                    "type": "username",
                    "required": True
                },
                {
                    "key": "service-now-password",
                    "description": "Service-Now Password",
                    "type": "password",
                    "required": True
                }
            ]
        },
        "tool_object": MCPTools  # Tool instance stored here
    },

    "GRAFANA_LOKI_MCP_SERVER": {
        "description": "MCP Server Toolkit for Querying the logs/labels from Grafana/Loki",
        "config_schema": {
            "fields": [
                {
                    "key": "loki-endpoint",
                    "description": "Loki Endpoint : http://<loki-host>:3100",
                    "type": "url",
                    "required": True
                }
            ]
        },
        "tool_object": MCPTools  # Tool instance stored here
    },
}
