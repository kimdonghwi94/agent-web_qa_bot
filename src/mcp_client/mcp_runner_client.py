"""MCP Runner Client for Web QA Bot"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import json
import uuid
import os
from src.config import Config
import logging

logger = logging.getLogger(__name__)


class MCPRunnerClient:
    """MCP Runner client to manage and execute MCP tools"""
    
    def __init__(self, base_url: str = None, mcp_config: Dict = None):
        config = Config()
        self.base_url = base_url or config.MCP_RUNNER_URL
        self.agent_id = f"web_qa_bot_{uuid.uuid4().hex[:8]}"
        
        self.active_sessions = {}
        self.mcp_configs = mcp_config or {}
        self.processed_configs = {}
        self.available_tools = {}
        self._initialized = False
        
    async def get_tools(self) -> Dict[str, List[Any]]:
        """Get all available MCP tools"""
        try:
            if not self.mcp_configs or not self.mcp_configs.get('mcpServers'):
                logger.warning("No MCP server configurations found")
                return {}
            
            # Load MCP configs and discover tools
            await self._load_mcp_configs()
            
            # Discover tools for each server
            for mcp_name in self.processed_configs.keys():
                await self._discover_mcp_tools(mcp_name)
            
            self._initialized = True
            total_tools = sum(len(tools) for tools in self.available_tools.values())
            logger.info(f"MCP Runner Client initialized: {len(self.mcp_configs)} servers, {total_tools} tools")
            
            # Return tools as executor objects
            tool_objects = {}
            for mcp_name, tools in self.available_tools.items():
                tool_objects[mcp_name] = [
                    MCPToolExecutor(
                        name=tool['name'],
                        description=tool.get('description', ''),
                        input_schema=tool.get('inputSchema', {}),
                        server_name=mcp_name,
                        client=self
                    )
                    for tool in tools
                ]
            
            return tool_objects
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Runner Client: {e}")
            self._initialized = False
            return {}
    
    async def _load_mcp_configs(self):
        """Load MCP configurations from the provided config"""
        try:
            configs = self.mcp_configs.get('mcpServers', {})
            processed_configs = {}

            for name, config in configs.items():
                command = config.get('command', '')
                args = config.get('args', [])

                processed_configs[name] = {
                    'name': name,
                    'command': command,
                    'args': args,
                    'env': self._resolve_env_variables(config.get('env', {})),
                }

            # Store processed configs separately
            self.processed_configs = processed_configs
            logger.info(f"MCP configurations loaded: {len(processed_configs)} servers")

        except Exception as e:
            logger.error(f"Failed to load MCP configurations: {e}")
            self.processed_configs = {}
    
    def _resolve_env_variables(self, env_config: Dict) -> Dict:
        """Resolve environment variables in configuration"""
        resolved = {}
        for key, value in env_config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, '')
            else:
                resolved[key] = value
        return resolved
    
    async def _discover_mcp_tools(self, mcp_name: str):
        """Discover tools for a specific MCP server"""
        if mcp_name not in self.processed_configs:
            logger.warning(f"MCP configuration not found: {mcp_name}")
            return

        session_id = f"{self.agent_id}_{mcp_name}_discovery"

        try:
            request_payload = {
                'session_id': session_id,
                'agent_id': self.agent_id,
                'mcp_config': self.processed_configs[mcp_name]
            }
            logger.debug(f"Sending MCP discover request: {json.dumps(request_payload, indent=2)}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/mcp/discover",
                    json=request_payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if result['status'] == 'success':
                            self.available_tools[mcp_name] = result['tools']
                            logger.info(f"MCP '{mcp_name}' tools discovered: {len(result['tools'])} tools")
                            for tool in result['tools']:
                                logger.debug(f"  - {tool['name']}: {tool.get('description', 'No description')}")
                        else:
                            logger.error(f"MCP '{mcp_name}' tool discovery failed: {result.get('error')}")
                            self.available_tools[mcp_name] = []
                    else:
                        error_text = await response.text()
                        logger.error(f"MCP Runner server error: {response.status}")
                        logger.error(f"Error details: {error_text}")
                        self.available_tools[mcp_name] = []
                        
        except Exception as e:
            logger.error(f"Error discovering MCP '{mcp_name}' tools: {e}")
            self.available_tools[mcp_name] = []
    
    async def execute_mcp_tool(self, mcp_name: str, tool_name: str, arguments: Dict):
        """Execute an MCP tool"""
        # Check if tool exists
        tools = self.available_tools.get(mcp_name, [])
        tool_exists = any(tool['name'] == tool_name for tool in tools)
        
        if not tool_exists:
            raise ValueError(f"Tool '{tool_name}' not found in MCP '{mcp_name}'")
            
        # Generate session ID
        session_key = f"{mcp_name}_{tool_name}"
        if session_key not in self.active_sessions:
            self.active_sessions[session_key] = f"{self.agent_id}_{mcp_name}_{uuid.uuid4().hex[:8]}"
            
        session_id = self.active_sessions[session_key]
        
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{self.base_url}/mcp/execute",
                    json={
                        'session_id': session_id,
                        'mcp_config': self.processed_configs[mcp_name],
                        'tool_name': tool_name,
                        'arguments': arguments
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        raise Exception(f"MCP Runner server error ({response.status}): {error_text}")
                        
        except Exception as e:
            logger.error(f"Tool execution failed '{mcp_name}.{tool_name}': {e}")
            raise
    
    async def cleanup(self):
        """Cleanup all resources"""
        try:
            for session_id in list(self.active_sessions.values()):
                try:
                    async with aiohttp.ClientSession() as http_session:
                        await http_session.post(
                            f"{self.base_url}/mcp/stop",
                            json={'session_id': session_id}
                        )
                except Exception as e:
                    logger.error(f"Session cleanup failed: {session_id} - {e}")
            
            self.active_sessions.clear()
            self._initialized = False
            logger.info("MCP Runner Client cleaned up")
            
        except Exception as e:
            logger.error(f"Error during MCP Runner Client cleanup: {e}")


class MCPToolExecutor:
    """Tool executor for MCP Runner"""
    
    def __init__(self, name: str, description: str, input_schema: Dict, server_name: str, client: MCPRunnerClient):
        self.name = name
        self.description = description
        self.inputSchema = input_schema
        self.server_name = server_name
        self.client = client
        
    async def __call__(self, **kwargs):
        """Execute the tool"""
        result = await self.client.execute_mcp_tool(self.server_name, self.name, kwargs)
        
        if result['status'] == 'success':
            return MCPRunnerResult(result.get('result', ''), True)
        else:
            return MCPRunnerResult(f"Error: {result.get('error', 'Unknown error')}", False)


class MCPRunnerResult:
    """MCP Runner execution result"""
    
    def __init__(self, content: Any, success: bool = True):
        if success:
            self.content = [MCPRunnerTextContent(str(content))]
        else:
            self.content = [MCPRunnerTextContent(str(content))]


class MCPRunnerTextContent:
    """Text content wrapper"""
    
    def __init__(self, text: str):
        self.text = text