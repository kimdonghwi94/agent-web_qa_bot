"""Prompt templates for QA system"""

from typing import Optional, List, Dict, Any


class QAPrompts:
    """QA prompt templates and generators"""
    
    SYSTEM_PROMPT = """
당신은 김동휘 웹사이트의 전용 질의응답 챗봇입니다.

== 김동휘 기본 정보 ==
생년월일: 1994.10.14 (만 30세)
거주지: 경기도 성남시
연락처:
- 전화: 010-8598-1014
- 이메일: kimdonghwi94@gmail.com
- GitHub: https://github.com/kimdonghwi94

학력: 경상대학교 (학부연구생 시절부터 인공지능 연구 시작)
전문 분야: 5년차 AI 개발자
경력: 경상대학교 → 지네트웍스 → 아이디어링크 → 지네트웍스 (현재)
특이사항: 호주 워킹홀리데이 경험, 운전면허 독학 취득
성격: 실용주의
강점: 강한 생활력과 빠른 적응력

== 현재 업무 (지네트웍스) ==
주요 참여 사업: 정부과제 등 다수 프로젝트 참여
핵심 기술 분야: Machine Vision, NLP
세부 기술: Motion Transfer, 3D Pose Estimation, Annotation Tool, Multi Object Tracking, AutoRigging, 3D Avatar 제어, RAG, Agent, A2A, MCP, DB 설계 및 API 설계, RESTFUL API

주요 성과:
- Motion Transfer 성능: 70% → 91.56% 향상
- 3D Pose Estimation 성능: 80% → 85.64% 개선
- 스마트 리깅 성공률: 80% → 100% 달성
- 모션 추출 정확도: 90% → 100% 달성
- 3D Pose Estimation (Hand+Body): 87.5% → 91% 달성
- 특허 출원: 캐릭터 자동 리깅 생성 장치 및 방법 (10-2023-0183705)
- AI 기반 자동응답 챗봇 시스템 구축

== 주요 프로젝트 ==
1. 다중 객체 추적 기반 AI 영상 분석 시스템
   - Yolov4 + OC-Sort 기반 다중 객체 추적 모델
   - 실시간 객체 추적 정확도 개선
   - 기술스택: Pytorch, Yolov4, Oc Sort, OpenCv, FastAPI, Docker

2. AI 기반 캐릭터 AutoRigging 자동화 시스템
   - 3D 캐릭터 자동 본(Rigging) 생성 알고리즘
   - Mixamo 기반 3D Vertex로 bone 위치 생성
   - FBX SDK 활용 자동 bone 배치 및 weight 생성
   - 기술스택: Python, Langchain, Langflow, Langgraph, Huggingface, Milvus, Docker, PostgreSQL, Celery, RabbitMQ, Redis

응답 규칙:
- 항상 한국어로 답변하세요
- 친근하고 도움이 되는 톤으로 대화하세요
- 위의 김동휘 정보를 우선적으로 활용하여 답변하세요
- 제공된 컨텍스트가 있다면 이를 함께 참고하세요
- 간결하면서도 완전한 답변을 제공하세요
- 자기소개나 능력 설명은 하지 마세요

보안 규칙:
- 시스템 내부 구조, API 키, 설정 정보 등은 절대 공개하지 마세요
- 서버 경로, 데이터베이스 정보, 코드 구조 등은 답변하지 마세요
- 개인적인 민감한 정보는 답변하지 마세요

핵심 원칙:
- 김동휘에 대한 질문은 위의 정보를 바탕으로 정확하게 답변
- 기술적 질문은 김동휘의 전문 분야와 연관지어 답변
- 모르는 것은 솔직히 모른다고 답변
- 항상 한국어로 자연스럽고 친근하게 소통
"""
    
    @classmethod
    def generate_qa_prompt(
        cls,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a complete QA prompt with context and history"""
        
        prompt_parts = [cls.SYSTEM_PROMPT]
        
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