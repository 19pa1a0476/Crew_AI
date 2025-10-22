from agno.tools.mcp import MCPTools, StreamableHTTPClientParams
from configuration import MCPServerConfig
from typing import Dict, Any, Optional

class MCPServerManager:
    async def ping_servers(self):
        self.connect_all()
        self.disconnect_all()
    
    async def connect_all(self):
        """
        Establish connections to all MCP servers.
        """
        for toolkit_name, url in MCPServerConfig.MCP_SERVERS_URL.items():
            mcp_tool = MCPTools(transport='streamable-http', url=url, timeout_seconds=30)
            mcp_tool.name = toolkit_name
            await mcp_tool.__aenter__()
            MCPServerConfig.MCP_CONNECTIONS[toolkit_name] = mcp_tool

    def connect_server(self, toolkit_name :str, tool_config: Optional[Dict[str, Any]] = None)->MCPTools:
        """
        Establish connection to particular MCP server
        in real time for each chat-completion api request.
        """
        server_params = StreamableHTTPClientParams(
            url = MCPServerConfig.MCP_SERVERS_URL.get(toolkit_name),
            headers= tool_config or None
        )

        mcp_tool = MCPTools(transport='streamable-http', server_params=server_params, timeout_seconds=30)
        mcp_tool.name = toolkit_name
        return mcp_tool

    async def disconnect_server(self, tool_server :MCPTools):
        """
        Close particular MCP server connection
        in real time for each chat-completion api request.
        """
        try:
            await tool_server.close()
            return True
        except Exception as e:
            return False

    async def disconnect_all(self):
        """
        Close all MCP server connections.
        """
        for mcp_tool in MCPServerConfig.MCP_CONNECTIONS.values():
            await mcp_tool.__aexit__(None, None, None)
        MCPServerConfig.MCP_CONNECTIONS.clear()

    def get_tool(self, name: str) -> MCPTools:
        """
        Retrieve the MCPTools instance for a given server name.
        """
        return MCPServerConfig.MCP_CONNECTIONS.get(name)


