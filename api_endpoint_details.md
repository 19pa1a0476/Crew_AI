# API Documentation

## Table of Contents
- [Users](#users)
- [Agents](#agents)
- [Workflows](#workflows)
- [Analytics](#analytics)
- [Tools](#tools)

## Users

### Create User
**Endpoint:** `POST /users/`

**Description:** Create a new user or get existing user.

**Request Sample:**
```json
{
  "user_id": "ext_123456",
  "username": "johndoe"
}
```

**Response Sample:**
```json
{
  "user_id": 1,
  "external_id": "ext_123456",
  "username": "johndoe"
}
```

## Agents

### Create Agent
**Endpoint:** `POST /create_agent/`

**Description:** Create a new agent with custom configuration.

**Request Sample:**
```json
{
  "user_id": "ext_123456",
  "username": "johndoe",
  "name": "Research Assistant",
  "role": "You are a helpful research assistant that can find and summarize information.",
  "tools": ["web_search", "document_retrieval"],
  "enable_memory": true,
  "markdown": true,
  "num_history_runs": 3,
  "metadata": {
    "specialty": "scientific literature"
  }
}
```

**Response Sample:**
```json
{
  "agent_id": "research_assistant",
  "name": "Research Assistant",
  "role": "You are a helpful research assistant that can find and summarize information.",
  "tools": ["web_search", "document_retrieval"],
  "status": "created"
}
```

### Delete Agent
**Endpoint:** `DELETE /agents/{agent_id}`

**Description:** Delete a user-defined agent.

**Request Sample:**
```
DELETE /agents/research_assistant?user_id=ext_123456
```

**Response Sample:**
```json
{
  "message": "Agent 'research_assistant' successfully deleted"
}
```

### Get Available Agents
**Endpoint:** `GET /available_agents`

**Description:** List all available agents in the system including user-defined agents.

**Request Sample:**
```
GET /available_agents?user_id=ext_123456
```

**Response Sample:**
```json
{
  "agents": [
    {
      "agent_id": "researcher",
      "name": "Researcher",
      "description": "An agent for research tasks"
    },
    {
      "agent_id": "writer",
      "name": "Writer",
      "description": "An agent for writing tasks"
    },
    {
      "agent_id": "research_assistant",
      "name": "Research Assistant",
      "description": "A custom agent for scientific research"
    }
  ]
}
```

### Get User Agents
**Endpoint:** `GET /user_agents`

**Description:** List only user-defined agents.

**Request Sample:**
```
GET /user_agents?user_id=ext_123456
```

**Response Sample:**
```json
{
  "agents": [
    {
      "agent_id": "research_assistant",
      "name": "Research Assistant",
      "role": "You are a helpful research assistant that can find and summarize information.",
      "tools": ["web_search", "document_retrieval"],
      "enable_memory": true,
      "markdown": true,
      "num_history_runs": 3,
      "created_at": "2025-05-08T14:35:22.456789"
    }
  ]
}
```

## Workflows

### Start Workflow
**Endpoint:** `POST /start_workflow/`

**Description:** Start a new workflow with defined steps.

**Request Sample:**
```json
{
  "user_id": "ext_123456",
  "username": "johndoe",
  "name": "Content Creation",
  "description": "Create blog post with research and edits",
  "steps": [
    {
      "name": "researcher",
      "prompt": "Research the latest trends in AI for healthcare",
      "human_review": false,
      "allow_edit": false
    },
    {
      "name": "writer",
      "prompt": "Write a blog post based on the research",
      "human_review": true,
      "allow_edit": true,
      "metadata": {
        "tone": "professional",
        "length": "1500 words"
      }
    }
  ]
}
```

**Response Sample:**
```json
{
  "workflow_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "name": "Content Creation",
  "status": "started"
}
```

### Review Workflow
**Endpoint:** `POST /review/{workflow_id}`

**Description:** Review and optionally edit a workflow step output.

**Request Sample:**
```json
{
  "user_id": "ext_123456",
  "approved": true,
  "feedback": "Great job! Add more details about neural networks.",
  "edited_output": "This is the edited version of the output with more details about neural networks..."
}
```

**Response Sample:**
```json
{
  "message": "Review processed successfully"
}
```

### Get Workflow Output
**Endpoint:** `GET /workflow_output/{workflow_id}`

**Description:** Get the outputs from a workflow.

**Request Sample:**
```
GET /workflow_output/a1b2c3d4-e5f6-7890-abcd-1234567890ab?user_id=ext_123456
```

**Response Sample:**
```json
{
  "outputs": [
    {
      "agent": "researcher",
      "output": "Here are the latest trends in AI for healthcare...",
      "can_edit": false
    },
    {
      "agent": "writer",
      "output": "# AI in Healthcare: Transforming Patient Care\n\nIn recent years...",
      "can_edit": true
    }
  ],
  "current_step": 2,
  "total_steps": 2,
  "context": {
    "output_from_researcher": "Here are the latest trends in AI for healthcare...",
    "current_step_metadata": {
      "tone": "professional",
      "length": "1500 words"
    }
  }
}
```

### Get Workflow Status
**Endpoint:** `GET /workflow_status/{workflow_id}`

**Description:** Get the current status of a workflow.

**Request Sample:**
```
GET /workflow_status/a1b2c3d4-e5f6-7890-abcd-1234567890ab?user_id=ext_123456
```

**Response Sample:**
```json
{
  "current_step": 2,
  "total_steps": 2,
  "completed": false,
  "awaiting_review": true,
  "allow_edit": true
}
```

### Get User Workflows
**Endpoint:** `GET /user_workflows`

**Description:** List workflows created by the user.

**Request Sample:**
```
GET /user_workflows?user_id=ext_123456
```

**Response Sample:**
```json
{
  "workflows": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "name": "Content Creation",
      "description": "Create blog post with research and edits",
      "created_at": "2025-05-08T12:34:56.789012",
      "completed": false,
      "current_step": 2,
      "total_steps": 2
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-23456789abcd",
      "name": "Market Analysis",
      "description": "Analyze market trends for product launch",
      "created_at": "2025-05-07T10:22:33.445566",
      "completed": true,
      "current_step": 3,
      "total_steps": 3
    }
  ]
}
```

## Analytics

### Get Workflow Analytics
**Endpoint:** `GET /workflow_analytics/{workflow_id}`

**Description:** Get analytics for each agent used in a workflow.

**Request Sample:**
```
GET /workflow_analytics/a1b2c3d4-e5f6-7890-abcd-1234567890ab?user_id=ext_123456
```

**Response Sample:**
```json
{
  "workflow_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "analytics": {
    "researcher": {
      "time": 2.45,
      "input_tokens": 125,
      "output_tokens": 850,
      "prompt_tokens": 325,
      "total_tokens": 1300
    },
    "writer": {
      "time": 5.78,
      "input_tokens": 975,
      "output_tokens": 1500,
      "prompt_tokens": 450,
      "total_tokens": 2925
    },
    "summary": {
      "time": 8.23,
      "input_tokens": 1100,
      "output_tokens": 2350,
      "prompt_tokens": 775,
      "total_tokens": 4225,
      "agent_count": 2
    }
  }
}
```

## Tools

### Get Available Tools
**Endpoint:** `GET /available_tools`

**Description:** List all available tools that can be used with custom agents.

**Request Sample:**
```
GET /available_tools
```

**Response Sample:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information"
    },
    {
      "name": "document_retrieval",
      "description": "Retrieve information from documents"
    },
    {
      "name": "code_interpreter",
      "description": "Execute and interpret code"
    }
  ]
}
```