"""Configuration management for the Web QA Bot agent."""

import os
import json
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration for Web QA Bot."""

    # Platform Selection
    PLATFORM: str = os.getenv("PLATFORM", "GOOGLE").upper()  # GOOGLE or OPENAI

    # LLM Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model based on platform
    if PLATFORM == "OPENAI":
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    else:  # GOOGLE
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")

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
                    "id": "personal_qa",
                    "name": "사용자 질의응답",
                    "description": "사용자에 대한 개인정보, 경력, 프로젝트 질의응답",
                    "tags": ["김동휘", "AI개발자", "한국어", "QA"]
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

    def __init__(self):
        """Initialize configuration."""
        pass