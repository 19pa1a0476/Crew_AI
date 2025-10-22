import logging
import requests
from jira import JIRA
from github import Github
from typing import Dict, Any, Tuple
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class ToolCredentialValidator:
    """Validates credentials for various tools before saving them"""
    
    @staticmethod
    def validate_jira_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate JIRA credentials"""
        try:
            server_url = config.get("server_url")
            username = config.get("username")
            token = config.get("token")
            
            if not all([server_url, username, token]):
                return False, "Missing required JIRA credentials"
            
            # Test JIRA connection
            jira = JIRA(server=server_url, basic_auth=(username, token))
            
            # Try to get user info to validate credentials
            user = jira.myself()
            print(f"JIRA user info: {user}")
            if user:
                return True, "JIRA credentials validated successfully"
            else:
                return False, "Invalid JIRA credentials"
                
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return False, "Invalid JIRA username or token"
            elif "403" in error_msg or "Forbidden" in error_msg:
                return False, "JIRA access forbidden - check permissions"
            elif "timeout" in error_msg.lower():
                return False, "JIRA server connection timeout"
            else:
                return False, f"JIRA connection failed: {error_msg}"

    @staticmethod
    def validate_github_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate GitHub credentials"""
        try:
            access_token = config.get("access_token")
            base_url = config.get("base_url")

            if not access_token:
                return False, "GitHub access token is required"
            if base_url:
                github = Github(access_token, base_url=base_url)
            else:
                github = Github(access_token)
            
            # Test by getting user info
            user = github.get_user()
            username = user.login  # API call happens here
            user_id = user.id

            print({"Username": username, "User ID": user_id})
            if username and user_id:
                return True, "GitHub credentials validated successfully"
            else:
                return False, "Invalid GitHub credentials"
                
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Bad credentials" in error_msg:
                return False, "Invalid GitHub access token"
            elif "403" in error_msg:
                return False, "GitHub access forbidden - check token permissions"
            elif "timeout" in error_msg.lower():
                return False, "GitHub connection timeout"
            else:
                return False, f"GitHub connection failed: {error_msg}"

    @staticmethod
    def validate_sql_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate SQL database credentials"""
        try:
            db_url = config.get("db_url")
            if not db_url:
                return False, "Database URL is required"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
            return True, "SQL database credentials validated successfully"
            
        except Exception as e:
            
            error_msg = str(e)
            if "authentication failed" in error_msg.lower():
                return False, "Invalid database username or password"
            elif "does not exist" in error_msg.lower():
                return False, "Database does not exist"
            elif "timeout" in error_msg.lower():
                return False, "Database connection timeout"
            elif "connection refused" in error_msg.lower():
                return False, "Database connection refused - check host and port"
            elif "could not connect" in error_msg.lower():
                return False, "Could not connect to database server"
            elif "no such host" in error_msg.lower():
                return False, "Database host not found"
            elif "permission denied" in error_msg.lower():
                return False, "Permission denied - check credentials"
            elif "not an executable object" in error_msg.lower():
                return False, "SQLAlchemy compatibility issue - please update your setup"
            else:
                return False, f"Database connection failed: {error_msg}"
            
    @staticmethod
    def validate_onedrive_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate OneDrive/Microsoft Graph credentials"""
        try:
            client_id = config.get("client-id")
            client_secret = config.get("client-secret")
            tenant_id = config.get("tenant-id")
            user_email = config.get("user-email")
            
            if not all([client_id, client_secret, tenant_id, user_email]):
                missing = [k for k, v in [("client-id", client_id), ("client-secret", client_secret), 
                          ("tenant-id", tenant_id), ("user-email", user_email)] if not v]
                return False, f"Missing required fields: {', '.join(missing)}"
            
            # Get access token
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code != 200:
                return False, "Invalid credentials - authentication failed"
            
            access_token = response.json().get('access_token')
            if not access_token:
                return False, "No access token received"
            
            # Test Graph API access
            headers = {'Authorization': f'Bearer {access_token}'}
            test_urls = [
                "https://graph.microsoft.com/v1.0/organization",
                f"https://graph.microsoft.com/v1.0/users/{user_email}",
                f"https://graph.microsoft.com/v1.0/users/{user_email}/drive"  # Test OneDrive access
            ]
            
            for url in test_urls:
                test_response = requests.get(url, headers=headers, timeout=30)
                if test_response.status_code == 200:
                    return True, "OneDrive credentials validated successfully"
                elif test_response.status_code == 404 and "users" in url:
                    return False, f"User '{user_email}' not found in tenant"
                elif test_response.status_code == 403:
                    if "drive" in url:
                        return False, "OneDrive access forbidden - missing Files.Read.All permission"
                    elif "users" in url:
                        return False, "User access forbidden - missing User.Read.All permission"
                
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"
        

    @staticmethod
    def validate_snow_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Service-Now credentials"""
        try:
            snow_url = config.get("service-now-instance-url")
            snow_username = config.get("service-now-username")
            snow_password = config.get("service-now-password")

            if not snow_url or not snow_username or not snow_password:
                return False, "Missing required ServiceNow configuration fields."

            # Detect and clean trailing slashes
            normalized_url = snow_url.rstrip("/")
            if snow_url != normalized_url:
                return False, (
                    f"Invalid URL format: '{snow_url}'. "
                    f"Please remove trailing '/' so it looks like '{normalized_url}'."
                )
            
            # Test with a small query against the sys_user table (safe check)
            test_url = f"{snow_url}/api/now/table/sys_user?sysparm_limit=1"
            response = requests.get(test_url, auth=(snow_username, snow_password), timeout=30)

            if response.status_code == 200:
                return True, "ServiceNow credentials are valid."
            elif response.status_code == 401:
                return False, "Invalid ServiceNow credentials (unauthorized)."
            elif response.status_code == 403:
                return False, "Forbidden: Service account lacks required permissions."
            else:
                return False, f"Unexpected response {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        

    @staticmethod
    def validate_loki_credentials(config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Grafana-Loki credentials"""
        try:
            loki_endpoint = config.get("loki-endpoint", "")
            if not loki_endpoint:
                return False, "Missing Loki endpoint in configuration."

            # Normalize trailing slashes
            normalized_endpoint = loki_endpoint.rstrip("/")
            if loki_endpoint != normalized_endpoint:
                return False, (
                    f"Invalid Loki endpoint format: '{loki_endpoint}'. "
                    f"Please remove trailing '/' so it looks like '{normalized_endpoint}'."
                )

            test_url = f"{normalized_endpoint}/loki/api/v1/series?limit=1"
            response = requests.get(test_url, timeout=15)
            # print(response.text)

            if "application/json" not in response.headers.get("Content-Type", ""):
                return False, "Loki endpoint didn't respond with valid JSON."

            # Handle HTTP status codes
            if response.status_code == 200:
                try:
                    resp_json = response.json()
                except ValueError:
                    return False, "Response is not valid JSON."
                if resp_json.get("status") == "success" and "data" in resp_json:
                    return True, "Loki endpoint is reachable and valid."
                else:
                    return False, "Loki endpoint response missing required fields 'status' or 'data'."

            elif response.status_code == 401:
                return False, "Unauthorized: Loki credentials (if any) are invalid."
            elif response.status_code == 403:
                return False, "Forbidden: access to Loki endpoint denied."
            elif response.status_code == 404:
                return False, "Loki endpoint not found (404). Check the URL."
            else:
                return False, f"Unexpected response {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        
        
    @classmethod
    def validate_tool_credentials(cls, tool_name: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Main method to validate credentials for any tool"""
        validators = {
            "jira_tools": cls.validate_jira_credentials,
            "github": cls.validate_github_credentials,
            "sql_tools": cls.validate_sql_credentials,
            "SERVICE_NOW_MCP_SERVER": cls.validate_snow_credentials,
            "GRAFANA_LOKI_MCP_SERVER": cls.validate_loki_credentials,
            "ONEDRIVE_MCP_SERVER": cls.validate_onedrive_credentials,
            "google_search_tools": lambda config: (True, "No credentials required"),
            "reasoning_tools": lambda config: (True, "No credentials required"),
            "MERMAID_MCP_SERVER": lambda config: (True, "No credentials required"),
            "DASHBOARD_MCP_SERVER": lambda config: (True, "No credentials required")
        }
        
        validator = validators.get(tool_name)
        if not validator:
            return False, f"No validator found for tool: {tool_name}"
        
        try:
            return validator(config)
        except Exception as e:
            logger.error(f"Error validating {tool_name} credentials: {str(e)}")
            return False, f"Validation error: {str(e)}"