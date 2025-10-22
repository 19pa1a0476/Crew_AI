# app/main.py
import sys
import asyncio
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from utilities.pg_sql_db_util import engine
from models.database_models import Base
from configuration import MCPServerConfig
import services.agents_service as agents_service
from services.mcp_service import MCPServerManager
from routers import (
    users_router, agents_router, workflow_router, 
    solution_std_router, knowledgebase_router
)

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    mcp_service = MCPServerManager()
    # await mcp_service.connect_all()
    # print("✅ Connected to all MCP servers")
    
    agents_service.initialize_agents(mcp_service)
    print("✅ Initialized system agents")

    yield  
    # await mcp_service.disconnect_all()
    # print("🔌 Disconnected from all MCP servers")


def setup_middleware(app: FastAPI):
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_application() -> FastAPI:
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = FastAPI(
        title="Agentic AI Framework",
        description="Web API for managing workflows, agents, and analytics",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    api_router = APIRouter()

    # Include all endpoint routers
    api_router.include_router(
        users_router.router,
        prefix="/users",
        tags=["users"]
    )

    api_router.include_router(
        agents_router.router,
        prefix="/agents",
        tags=["agents"]
    )

    api_router.include_router(
        workflow_router.router,
        prefix="/workflows",
        tags=["workflows"]
    )

    api_router.include_router(
        solution_std_router.router,
        prefix="/solution_studio",
        tags=["Solution Studio"]
    )

    api_router.include_router(
        knowledgebase_router.router,
        prefix="/knowledgebase",
        tags=["Knowledgebase"]
    )

    # Include routers
    app.include_router(api_router)
    return app

app = create_application()