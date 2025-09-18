"""Prompt templates for QA system"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class QAPrompts:
    """QA prompt templates and generators"""

    def __init__(self):
        """Initialize and load system prompt"""
        self._system_prompt = self._load_system_prompt()

    @classmethod
    def _load_system_prompt(cls) -> str:
        """Load system prompt from file"""
        current_dir = Path(__file__).parent
        prompt_file = current_dir / "qa_system_prompt.txt"
        example_file = current_dir / "qa_system_prompt.example.txt"

        # Try to load actual prompt file first
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # Fallback to example file
        if example_file.exists():
            with open(example_file, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # Fallback to basic prompt if no files exist
        return """
당신은 웹사이트의 전용 질의응답 챗봇입니다.

응답 규칙:
- 항상 한국어로 답변하세요
- 친근하고 도움이 되는 톤으로 대화하세요
- 제공된 컨텍스트가 있다면 이를 함께 참고하세요
- 간결하면서도 완전한 답변을 제공하세요

핵심 원칙:
- 모르는 것은 솔직히 모른다고 답변
- 항상 한국어로 자연스럽고 친근하게 소통
        """.strip()

    @property
    def SYSTEM_PROMPT(self) -> str:
        """Get system prompt (cached in memory)"""
        return self._system_prompt
    
    def generate_qa_prompt(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a complete QA prompt with context and history"""

        prompt_parts = [self._system_prompt]
        
        # Add conversation history if available
        if history:
            prompt_parts.append("\n## Conversation History:")
            for item in history[-5:]:  # Last 5 exchanges
                role = item.get('role', 'unknown')
                content = item.get('content', '')
                if role == 'user':
                    prompt_parts.append(f"User: {content}")
                elif role == 'assistant':
                    prompt_parts.append(f"Assistant: {content}")
        
        # Add context if available
        if context:
            prompt_parts.append("\n## Available Context:")
            prompt_parts.append(context)
            prompt_parts.append("\n## Instructions:")
            prompt_parts.append(
                "위의 컨텍스트를 활용하여 사용자의 질문에 한국어로 답변하세요. "
                "컨텍스트에 관련 정보가 있다면 이를 우선적으로 참고하세요. "
                "컨텍스트만으로 충분히 답변할 수 없는 경우, 일반적인 지식을 활용하되 "
                "어떤 부분이 컨텍스트에서 나온 정보인지 구분해서 답변하세요. "
                "항상 한국어로 친근하게 답변하세요."
            )
        
        # Add the current query
        prompt_parts.append(f"\n## User Question:\n{query}")
        prompt_parts.append("\n## Your Response:")
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def generate_summarization_prompt(cls, content: str, url: str) -> str:
        """Generate prompt for web content summarization"""
        return f"""
Please summarize the following web content from {url}.

Content:
{content[:3000]}...

Provide a concise summary that captures the main points and key information.
Include:
1. Main topic or purpose
2. Key points or arguments
3. Important details or data
4. Conclusions or takeaways

Summary:
"""
    
    @classmethod
    def generate_extraction_prompt(cls, content: str, question: str) -> str:
        """Generate prompt for extracting specific information"""
        return f"""
Extract information from the following content to answer this specific question: {question}

Content:
{content}

Please provide:
1. Direct answer to the question (if available)
2. Relevant quotes or excerpts
3. Source context
4. Confidence level in the answer

Extracted Information:
"""
    
    @classmethod
    def generate_comparison_prompt(cls, sources: List[Dict[str, Any]], question: str) -> str:
        """Generate prompt for comparing information from multiple sources"""
        prompt_parts = [
            f"Compare information from multiple sources to answer: {question}",
            "\nSources:"
        ]
        
        for i, source in enumerate(sources, 1):
            content = source.get('content', '')[:1000]
            url = source.get('url', f'Source {i}')
            prompt_parts.append(f"\nSource {i} ({url}):\n{content}...")
        
        prompt_parts.extend([
            "\nPlease provide:",
            "1. Synthesized answer based on all sources",
            "2. Points of agreement between sources",
            "3. Points of disagreement or contradiction",
            "4. Most reliable information with source attribution",
            "\nComparison Analysis:"
        ])
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def generate_followup_prompt(cls, original_query: str, answer: str, followup: str) -> str:
        """Generate prompt for follow-up questions"""
        return f"""
Original Question: {original_query}

Previous Answer: {answer}

Follow-up Question: {followup}

Please answer the follow-up question, building on the previous context and answer. 
Maintain consistency with the previous response while providing additional or clarifying information.

Follow-up Response:
"""
    
    @classmethod
    def generate_error_prompt(cls, error_type: str, details: str) -> str:
        """Generate user-friendly error messages"""
        error_messages = {
            "no_context": "I don't have enough context to answer your question accurately. Could you provide more details or a specific source?",
            "invalid_url": f"I couldn't access the provided URL: {details}. Please check the URL and try again.",
            "parsing_error": "I encountered an issue processing the content. Please try rephrasing your question or providing a different source.",
            "api_error": "I'm experiencing technical difficulties. Please try again in a moment.",
            "rate_limit": "I'm currently handling many requests. Please wait a moment and try again."
        }
        
        return error_messages.get(error_type, f"An error occurred: {details}")
    
    @classmethod
    def generate_citation_format(cls, source_url: str, title: str = None) -> str:
        """Generate citation format for sources"""
        if title:
            return f"[{title}]({source_url})"
        else:
            return f"[Source]({source_url})"
    
    @classmethod
    def validate_query(cls, query: str) -> Dict[str, Any]:
        """Validate and analyze user query"""
        query = query.strip()
        
        result = {
            "is_valid": bool(query),
            "length": len(query),
            "word_count": len(query.split()),
            "has_url": "http://" in query or "https://" in query,
            "is_question": any(q in query.lower() for q in ["?", "what", "how", "why", "when", "where", "who"]),
            "keywords": []
        }
        
        if query:
            # Extract potential keywords (simple approach)
            words = query.lower().split()
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being"}
            result["keywords"] = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return result