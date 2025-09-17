"""Configuration management for the Web QA Bot agent."""

import os
import json
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration for Web QA Bot."""
    
    # LLM Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")
    
    # QA Settings
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # MCP Configuration
    MCP_CONFIG_PATH: Path = Path("mcpserver.json")
    MCP_RUNNER_URL: str = os.getenv("MCP_RUNNER_URL", "https://mcp-host-runner.onrender.com")

    @classmethod
    def get_agent_info(cls) -> dict[str, Any]:
        """Get hardcoded agent configuration."""
        return {
            "agent": {
                "name": "김동휘 웹사이트 QA 챗봇",
                "description": "김동휘 웹사이트 방문자를 위한 전용 질의응답 챗봇",
                "version": "1.0.0"
            },
            "skills": [
                {
                    "id": "donghwi_qa",
                    "name": "김동휘 질의응답",
                    "description": "김동휘에 대한 개인정보, 경력, 프로젝트 질의응답",
                    "tags": ["김동휘", "AI개발자", "한국어", "QA"]
                },
                {
                    "id": "context_qa",
                    "name": "컨텍스트 기반 QA",
                    "description": "제공된 컨텍스트를 활용한 질의응답",
                    "tags": ["context", "qa", "korean"]
                }
            ]
        }

    @classmethod
    def load_mcp_config(cls) -> dict[str, Any]:
        """Load MCP server configuration."""
        # Try relative to project root first
        project_root = Path(__file__).parent.parent
        config_path = project_root / "mcpserver.json"

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)

        # Fallback to original path
        if cls.MCP_CONFIG_PATH.exists():
            with open(cls.MCP_CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)

        return {"mcpServers": {}}
    
    @classmethod
    def get_qa_settings(cls) -> dict[str, Any]:
        """Get QA-specific settings."""
        return {
            "max_context_length": cls.MAX_CONTEXT_LENGTH,
            "temperature": cls.TEMPERATURE,
            "top_k": cls.TOP_K,
        }

    def __init__(self):
        """Initialize configuration."""
        pass