"""QA Agent implementation for Web QA Bot"""

import logging
import asyncio
from typing import Dict, List, Any, AsyncGenerator, Optional
import json
import re

from src.mcp_client.mcp_runner_client import MCPRunnerClient
from src.prompts.qa_prompts import QAPrompts
from src.prompts.agent_prompts import AgentPrompts
from src.config import Config
from src.skills.web_analyzer_skill import WebAnalyzerSkill

# Conditional imports for LLM platforms
try:
    from google import genai
    from google.genai import types
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class QAAgent:
    """Simple Question Answering Agent - receives context from host agent"""

    def __init__(self):
        self.agent_name = "Web QA Bot"
        self.agent_description = "Intelligent Web Question Answering Agent"
        self._initialized = False
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

        # Components
        self.mcp_client: Optional[MCPRunnerClient] = None
        self.client = None  # Will be Google or OpenAI client
        self.mcp_tools = {}
        self.web_analyzer = WebAnalyzerSkill()

        # Configuration
        self.config = Config()
    
    async def initialize(self):
        """Initialize the QA agent with LLM and MCP components"""
        if self._initialized:
            return

        try:
            # Initialize LLM Client based on platform
            if self.config.PLATFORM == "OPENAI":
                if not OPENAI_AVAILABLE:
                    raise ImportError("OpenAI library not installed. Please install with: pip install openai")
                if self.config.OPENAI_API_KEY:
                    self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)  # For compatibility
                    logger.info(f"Initialized OpenAI client for model: {self.config.LLM_MODEL}")
                else:
                    raise ValueError("OPENAI_API_KEY not configured")
            else:  # GOOGLE
                if not GOOGLE_AVAILABLE:
                    raise ImportError("Google GenAI library not installed. Please install with: pip install google-genai")
                if self.config.GOOGLE_API_KEY:
                    self.client = genai.Client(api_key=self.config.GOOGLE_API_KEY)
                    logger.info(f"Initialized Google GenAI client for model: {self.config.LLM_MODEL}")
                else:
                    raise ValueError("GOOGLE_API_KEY not configured")

            # Initialize MCP Client
            self.mcp_client = MCPRunnerClient(
                base_url=self.config.MCP_RUNNER_URL,
                mcp_config=self.config.load_mcp_config()
            )
            self.mcp_tools = await self.mcp_client.get_tools()
            logger.info(f"Initialized MCP Client with {len(self.mcp_tools)} tools")

            self._initialized = True
            logger.info("Web QA Bot initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Web QA Bot: {e}")
            raise
    
    async def process_query(self, query: str, context_id: str, context: str = None) -> AsyncGenerator[str, None]:
        """Process a user query using intelligent agent reasoning - SECURE VERSION"""
        try:
            # Get conversation history
            history = self.conversation_history.get(context_id, [])

            # **CRITICAL**: All agent processing happens silently
            # User only sees final result - NO internal logic exposure
            final_response = await self._execute_agent_internally(query, history, context)

            # Stream only the final response to user
            async for chunk in self._stream_response(final_response):
                yield chunk

            # Update conversation history
            await self._update_conversation_history(context_id, query, final_response)

        except Exception as e:
            logger.error(f"Error in agent processing: {e}")
            yield "죄송합니다. 질문을 처리하는 중에 예상치 못한 문제가 발생했습니다. 잠시 후 다시 시도해주세요."

    async def _execute_agent_internally(self, query: str, history: List[Dict[str, str]], context: str = None) -> str:
        """Internal agent execution - completely hidden from user"""
        max_iterations = 5
        iteration = 0
        executed_actions = []
        current_context = context or ""

        logger.info("[INTERNAL] Starting agent reasoning loop")

        # Silent agent reasoning loop
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"[INTERNAL] Agent iteration {iteration}/{max_iterations}")

            # Get available tools
            available_tools = await self._get_available_tools_list()

            # Generate reasoning prompt
            if iteration == 1:
                reasoning_prompt = AgentPrompts.generate_reasoning_prompt(
                    user_query=query,
                    available_tools=available_tools,
                    conversation_history=history[-3:] if history else None,
                    previous_actions=executed_actions,
                    context=current_context
                )
            else:
                reasoning_prompt = AgentPrompts.generate_followup_prompt(
                    original_query=query,
                    tool_results=executed_actions,
                    conversation_history=history[-3:] if history else None
                )

            # Get agent decision (internal only)
            decision = await self._get_agent_decision(reasoning_prompt)
            if not decision:
                logger.warning("[INTERNAL] Failed to get agent decision")
                break

            action = decision.get('action')
            reasoning = decision.get('reasoning', '')
            logger.info(f"[INTERNAL] Agent decision: {action}")
            # DO NOT log reasoning details to prevent exposure

            if action == "use_tool":
                tool_name = decision.get('tool_name')
                tool_args = decision.get('tool_arguments', {})

                if tool_name:
                    logger.info(f"[INTERNAL] Executing tool silently")
                    # Execute tool completely silently
                    tool_result = await self._execute_tool(tool_name, tool_args)
                    executed_actions.append({
                        'type': 'tool_execution',
                        'tool_name': tool_name,
                        'arguments': tool_args,
                        'result': tool_result.get('result', ''),
                        'success': tool_result.get('success', False),
                        'error': tool_result.get('error', '')
                    })
                    logger.info(f"[INTERNAL] Tool executed: {tool_result.get('success', False)}")
                else:
                    logger.warning("[INTERNAL] Tool name not specified")
                    break

            elif action == "respond_directly":
                # Generate final response
                response = decision.get('response', '')
                if not response:
                    response = await self._generate_final_response(query, executed_actions, current_context)
                logger.info("[INTERNAL] Generated final response")
                return response

            elif action == "think_more":
                logger.info("[INTERNAL] Agent continuing analysis...")
                continue
            else:
                logger.warning(f"[INTERNAL] Unknown action: {action}")
                break

        # If max iterations reached
        logger.info("[INTERNAL] Max iterations reached, generating final response")
        final_response = await self._generate_final_response(query, executed_actions, current_context)
        return final_response

    async def _get_available_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of available tools for agent reasoning"""
        tools_list = []

        # Add built-in web analyzer skill
        tools_list.append({
            'name': 'web_analyzer',
            'description': '웹 페이지 URL을 마크다운 형식으로 변환하여 내용을 추출합니다',
            'server': 'builtin',
            'parameters': ['url']
        })

        # Add MCP tools if available
        if self.mcp_tools:
            for server_name, tools in self.mcp_tools.items():
                for tool in tools:
                    tools_list.append({
                        'name': tool.name,
                        'description': tool.description,
                        'server': server_name,
                        'parameters': list(tool.inputSchema.get('properties', {}).keys())
                    })

        return tools_list

    async def _get_agent_decision(self, reasoning_prompt: str) -> Dict[str, Any]:
        """Get agent decision from LLM reasoning"""
        try:
            if not self.client:
                return None

            response_text = ""

            if self.config.PLATFORM == "OPENAI":
                # Use OpenAI API
                response = await self.client.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that responds in JSON format."},
                        {"role": "user", "content": reasoning_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    response_format={ "type": "json_object" }
                )
                response_text = response.choices[0].message.content
            else:
                # Use Google GenAI API
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.config.LLM_MODEL,
                    contents=reasoning_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,  # Lower temperature for more consistent reasoning
                        top_p=0.9,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )
                response_text = response.text.strip()

            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                decision = json.loads(json_text)
                return decision
            else:
                logger.error(f"No valid JSON found in response: {response_text}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error getting agent decision: {e}")
            return None

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool and return results"""

        # Handle built-in web analyzer skill
        if tool_name == 'web_analyzer':
            try:
                url = tool_args.get('url', '')
                if not url:
                    return {'success': False, 'error': 'URL parameter is required for web_analyzer'}

                result = await self.web_analyzer.execute(url)
                return {
                    'success': result['success'],
                    'result': result['result'],
                    'error': result.get('error'),
                    'tool_name': tool_name,
                    'server': 'builtin'
                }
            except Exception as e:
                logger.error(f"Error executing web_analyzer: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'tool_name': tool_name
                }

        # Handle MCP tools
        if not self.mcp_client or not self.mcp_tools:
            return {'success': False, 'error': 'No MCP tools available'}

        # Find the tool
        target_server = None
        target_tool = None

        for server_name, tools in self.mcp_tools.items():
            for tool in tools:
                if tool.name == tool_name:
                    target_server = server_name
                    target_tool = tool
                    break
            if target_tool:
                break

        if not target_tool:
            return {'success': False, 'error': f'Tool {tool_name} not found'}

        try:
            # Validate and prepare arguments
            validated_args = self._validate_tool_arguments(target_tool, tool_args)

            # Execute tool
            result = await self.mcp_client.execute_mcp_tool(target_server, tool_name, validated_args)

            return {
                'success': True,
                'result': result,
                'tool_name': tool_name,
                'server': target_server
            }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool_name': tool_name
            }

    def _validate_tool_arguments(self, tool, provided_args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare tool arguments"""
        schema = tool.inputSchema
        properties = schema.get('properties', {})
        required = schema.get('required', [])

        validated_args = {}

        # Add provided arguments that are valid
        for key, value in provided_args.items():
            if key in properties:
                validated_args[key] = value

        # Add default values for missing required parameters
        for req_param in required:
            if req_param not in validated_args:
                param_info = properties.get(req_param, {})
                param_type = param_info.get('type', 'string')

                # Try to infer reasonable defaults
                if param_type == 'string':
                    validated_args[req_param] = ''
                elif param_type == 'boolean':
                    validated_args[req_param] = True
                elif param_type in ['number', 'integer']:
                    validated_args[req_param] = 0

        return validated_args

    async def _generate_final_response(self, original_query: str, executed_actions: List[Dict[str, Any]], context: str) -> str:
        """Generate final response based on all collected information"""
        try:
            if not self.client:
                return "죄송합니다. 현재 AI 서비스를 사용할 수 없습니다."

            # Generate final response prompt
            final_prompt = AgentPrompts.generate_final_response_prompt(
                original_query=original_query,
                all_results=executed_actions,
                context=context
            )

            if self.config.PLATFORM == "OPENAI":
                # Use OpenAI API
                # Adjust max_tokens based on model
                max_tokens = 4096 if "gpt-3.5" in self.config.LLM_MODEL else 8192
                response = await self.client.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": QAPrompts.SYSTEM_PROMPT},
                        {"role": "user", "content": final_prompt}
                    ],
                    temperature=self.config.TEMPERATURE,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Use Google GenAI API
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.config.LLM_MODEL,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.config.TEMPERATURE,
                        top_p=0.95,
                        top_k=self.config.TOP_K,
                        max_output_tokens=8192,
                    )
                )
                return response.text

        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return "죄송합니다. 답변을 생성하는 중에 문제가 발생했습니다."

    async def _update_conversation_history(self, context_id: str, query: str, response: str):
        """Update conversation history"""
        if context_id not in self.conversation_history:
            self.conversation_history[context_id] = []

        self.conversation_history[context_id].append({
            "role": "user",
            "content": query
        })
        self.conversation_history[context_id].append({
            "role": "assistant",
            "content": response
        })

        # Keep only last 10 exchanges
        if len(self.conversation_history[context_id]) > 20:
            self.conversation_history[context_id] = self.conversation_history[context_id][-20:]
    
    async def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using LLM client"""
        try:
            if self.config.PLATFORM == "OPENAI":
                # Use OpenAI API
                # Adjust max_tokens based on model
                max_tokens = 4096 if "gpt-3.5" in self.config.LLM_MODEL else 8192
                response = await self.client.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": QAPrompts.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.TEMPERATURE,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Use Google GenAI API
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.config.LLM_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.config.TEMPERATURE,
                        top_p=0.95,
                        top_k=self.config.TOP_K,
                        max_output_tokens=8192,
                    )
                )
                return response.text
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            # 사용자에게 친화적인 메시지로 변경
            error_str = str(e)
            if "overloaded" in error_str or "503" in error_str:
                return "죄송합니다. 현재 서비스가 많이 사용되고 있어서 일시적으로 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
            elif "UNAVAILABLE" in error_str:
                return "죄송합니다. 현재 AI 서비스에 일시적인 문제가 있습니다. 조금 후에 다시 시도해주세요."
            elif "quota" in error_str.lower() or "limit" in error_str.lower() or "429" in error_str:
                return "죄송합니다. 현재 서비스 사용량이 한계에 도달했습니다. 잠시 후 다시 시도해주세요."
            elif "401" in error_str or "unauthorized" in error_str.lower():
                return "죄송합니다. 현재 시스템에 일시적인 인증 문제가 있습니다. 관리자에게 문의해주세요."
            else:
                return "죄송합니다. 답변을 생성하는 중에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    async def _stream_response(self, response: str) -> AsyncGenerator[str, None]:
        """Stream response in chunks"""
        chunk_size = 50  # Characters per chunk
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay for streaming effect
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()
        self._initialized = False
        logger.info("Web QA Bot cleaned up")
    
    @property
    def is_ready(self) -> bool:
        """Check if agent is ready"""
        return self._initialized