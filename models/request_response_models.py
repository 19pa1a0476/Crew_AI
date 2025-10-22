import asyncio
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional, Literal

class UserRequest(BaseModel):
    user_id: str
    username: Optional[str] = None

class StepRequest(BaseModel):
    name: str
    prompt: str
    human_review: bool
    allow_edit: bool = False  # Flag to allow editing of outputs
    metadata: Optional[Dict[str, Any]] = None

class StartWorkflowRequest(BaseModel):
    user_id: str
    workflow_id: Optional[str] = None
    username: Optional[str] = None
    name: str = "Untitled Workflow"  
    description: Optional[str] = None  
    steps: Optional[List[StepRequest]] = None

class ReviewRequest(BaseModel):
    user_id: str
    approved: bool
    feedback: str = ""  # Optional feedback for the agent
    edited_output: Optional[str] = None  # Optional edited output

class EditOutputRequest(BaseModel):
    user_id: str
    edited_output: str

class CreateAgentRequest(BaseModel):
    user_id: str
    username: Optional[str] = None
    name: str
    role: str
    tools: List[str] = []  # List of tool names to enable
    enable_memory: bool = True
    markdown: bool = True
    num_history_runs: int = 3
    metadata: Optional[Dict[str, Any]] = None

class WorkflowStep(BaseModel):
    name: str
    prompt: str
    human_review: bool
    allow_edit: bool = False  # Flag to allow editing of outputs
    metadata: Dict[str, Any] = {}

class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep] = []
    is_drafted: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class InvokeAgentPayload(BaseModel):
    agent_name: str
    prompt: str
    context: Optional[Dict[str, Any]] = None
    user_id: str
    workflow_id: Optional[str] = None


class WorkflowState:
    def __init__(self, steps: List[WorkflowStep]):
        self.steps = steps
        self.current_index = 0
        self.event = asyncio.Event()
        self.approved = None
        self.outputs = []
        self.context = {}  # Shared context between steps
        self.feedback = ""  # Feedback for regeneration
        self.edited_output = None  # Store edited output from user
        self.is_drafted = False

class QueryContentItem(BaseModel):
    filename: str
    content: str

class KBCreateRequest(BaseModel):
    type: Literal["PDF_URL", "LOCAL", "WEBSITE", "S3", "GITHUB"]
    name: str
    urls: Optional[List[str]] = None
    local_files: Optional[List[QueryContentItem]] = None
    s3_bucket: Optional[str] = None
    s3_prefix: Optional[str] = None
    repo_url: Optional[str] = None
    repo_branch: Optional[str] = None
    git_access_token: Optional[str] = None
    ext_list: Optional[List[str]] = None

class UserAgentConfigPayload(BaseModel):
    agent_id: str
    enable_memory: Optional[bool] = False
    markdown: Optional[bool] = False
    num_history_runs: Optional[int] = 3
    agent_config: Optional[Dict[str, Any]] = {}
    knowledgebase_details: Optional[List[str]] = []

class ToolkitFieldUpdate(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    type: Optional[str] = None
    required: Optional[bool] = None

class ToolkitConfigPayload(BaseModel):
    user_id: str
    config: Dict[str, List[ToolkitFieldUpdate]]

class ChatCompletionRequest(BaseModel):
    user_id: str
    user_query: str
    session_id: Optional[str] = None
    agent_ids: List[str]
    model_id: Optional[str] = None
    query_content: Optional[List[QueryContentItem]] = None