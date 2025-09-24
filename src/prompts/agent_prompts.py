"""Agent Reasoning Prompts for intelligent decision making"""

from typing import List, Dict, Any
import json


class AgentPrompts:
    """Agent reasoning prompt templates"""

    @classmethod
    def generate_reasoning_prompt(
        cls,
        user_query: str,
        available_tools: List[Dict[str, Any]],
    ) -> str:
        """Generate prompt for agent reasoning and action selection"""

        tool_descriptions = []
        if available_tools:
            for tool in available_tools:
                tool_descriptions.append(f"- {tool['name']}: {tool['description']}")

        tool_list = "\n".join(tool_descriptions) if tool_descriptions else "사용 가능한 도구가 없습니다."

        prompt = f"""당신은 김동휘 웹사이트의 지능형 QA Agent입니다. 사용자의 질문을 분석하고 다음에 수행할 행동을 결정해야 합니다.

## 사용자 질문:
{user_query}

## 사용 가능한 도구들:
{tool_list}

## 가능한 행동들:
1. "use_tool" - 도구를 사용하여 정보를 수집해야 할 때
2. "respond_directly" - 이미 충분한 정보가 있거나 직접 답변 가능할 때 or 김동휘에 대해 질문할때 or 현재 웹 페이지에 대해 질문할때
3. "think_more" - 추가적인 분석이나 생각이 필요할 때

## 결정 과정:
1. 사용자 질문을 분석하세요
2. 현재 가지고 있는 정보로 답변이 가능한지 판단하세요
3. 부족한 정보가 있다면 어떤 도구가 도움이 될지 판단하세요
4. 다음 행동을 결정하세요

## 판단 원칙:
- 질문에 직접 답변이 가능한 경우 바로 "respond_directly" 선택
- 구체적인 정보(URL, 파일명 등)가 제공된 경우에만 해당 도구 사용
- 불명확하거나 애매한 질문의 경우 명확화를 요청하는 답변 제공
- 기술 설명보다는 사용자가 묻는 내용에 직접적으로 답변

아래 JSON 형식으로만 응답하세요:

{{
    "reasoning": "판단 과정과 이유를 한국어로 설명",
    "action": "use_tool|respond_directly|think_more",
    "tool_name": "사용할 도구 이름 (action이 use_tool인 경우만)",
    "tool_arguments": {{"필요한 파라미터들"}},
    "response": "최종 답변 (action이 respond_directly인 경우만)",
    "confidence": 0.0-1.0
}}"""

        return prompt

    @classmethod
    def generate_followup_prompt(
        cls,
        original_query: str,
        tool_results: List[Dict[str, Any]],
    ) -> str:
        """Generate prompt for processing tool results and deciding next action"""

        results_text = ""
        if tool_results:
            results_text = "\n## 도구 실행 결과들:\n"
            for i, result in enumerate(tool_results, 1):
                tool_name = result.get('tool_name', 'unknown')
                success = result.get('success', False)
                content = result.get('result', result.get('error', ''))

                status = "성공" if success else "실패"
                results_text += f"{i}. {tool_name} ({status}):\n"
                if isinstance(content, dict):
                    results_text += f"   {json.dumps(content, ensure_ascii=False, indent=2)[:500]}...\n"
                else:
                    results_text += f"   {str(content)[:500]}...\n"

        prompt = f"""당신은 김동휘 웹사이트의 지능형 QA Agent입니다. 도구 실행 결과를 분석하고 다음 행동을 결정해야 합니다.

**중요 컨텍스트:**
- 사용자가 "이 페이지", "여기", "이 사이트" 등으로 언급하면 항상 "김동휘 포트폴리오 웹사이트"를 지칭하는 것입니다
- 현재 페이지 URL: https://kimdonghwi94.github.io/dhkim
- 이 웹사이트는 김동휘의 포트폴리오, 이력서, 기술스택, 프로젝트, 블로그 등을 소개하는 개인 포트폴리오 사이트입니다

## 원래 사용자 질문:
{original_query}

{results_text}

## 분석 및 결정:
1. 도구 실행 결과를 분석하세요
2. 사용자 질문에 대답하기에 충분한 정보가 있는지 판단하세요
3. 추가 도구 사용이 필요한지, 아니면 지금 답변할 수 있는지 결정하세요

## 가능한 행동들:
1. "use_tool" - 추가 정보가 필요하여 다른 도구 사용
2. "respond_directly" - 충분한 정보가 있어 사용자에게 답변 or 김동휘에 대해 질문할때 or 현재 웹 페이지에 대해 질문할때
3. "think_more" - 결과를 더 분석하고 정리 필요

아래 JSON 형식으로만 응답하세요:

{{
    "reasoning": "도구 결과 분석과 다음 행동 결정 이유를 한국어로 설명",
    "action": "use_tool|respond_directly|think_more",
    "tool_name": "사용할 도구 이름 (action이 use_tool인 경우만)",
    "tool_arguments": {{"필요한 파라미터들"}},
    "response": "최종 답변 (action이 respond_directly인 경우만)",
    "confidence": 0.0-1.0
}}"""

        return prompt

    @classmethod
    def generate_final_response_prompt(
        cls,
        original_query: str,
        all_results: List[Dict[str, Any]],
    ) -> str:
        """Generate prompt for creating final response to user"""

        results_summary = ""
        if all_results:
            results_summary = "\n## 수집된 정보:\n"
            for i, result in enumerate(all_results, 1):
                tool_name = result.get('tool_name', 'unknown')
                success = result.get('success', False)
                if success:
                    content = result.get('result', '')
                    if isinstance(content, dict):
                        content = json.dumps(content, ensure_ascii=False)
                    results_summary += f"{i}. {tool_name}에서 수집한 정보:\n{str(content)[:1000]}...\n\n"

        prompt = f"""당신은 김동휘 웹사이트의 전용 질의응답 챗봇입니다. 수집된 정보를 바탕으로 사용자에게 최종 답변을 제공하세요.
        
**중요 컨텍스트:**
- 사용자가 "이 페이지", "여기", "이 사이트" 등으로 언급하면 항상 "김동휘 포트폴리오 웹사이트"를 지칭하는 것입니다
- 현재 페이지 URL: https://kimdonghwi94.github.io/dhkim
- 이 웹사이트는 김동휘의 포트폴리오, 이력서, 기술스택, 프로젝트, 블로그 등을 소개하는 개인 포트폴리오 사이트입니다


## 사용자 질문:
{original_query}

{results_summary}

## 답변 지침:
1. 수집된 정보를 종합하여 정확하고 유용한 답변을 제공하세요
2. 항상 한국어로 답변하세요
3. 친근하고 도움이 되는 톤으로 대화하세요
4. 김동휘 관련 정보를 우선적으로 활용하세요
5. 정보의 출처를 자연스럽게 언급하세요
6. 질문에 직접 답변하고, 불필요한 기술 설명이나 자랑은 피하세요
7. 구체적인 정보가 없으면 솔직히 모른다고 답변하거나 추가 정보를 요청하세요

최종 답변:"""

        return prompt