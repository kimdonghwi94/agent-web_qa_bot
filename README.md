# 김동휘 웹사이트 QA 챗봇

김동휘 웹사이트 방문자를 위한 전용 질의응답 챗봇입니다. Host Agent에서 웹사이트 컨텍스트를 받아 한국어로 친근하게 답변하는 A2A 프로토콜 기반 에이전트입니다.

## 🚀 빠른 시작

### 1. 환경 요구사항

- **Python 3.12 이상**
- **UV 패키지 매니저**

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd agent-web_qa_bot

# 의존성 설치
uv sync
```

### 3. 환경 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```env
# 필수: Google API Key
GOOGLE_API_KEY=your_google_api_key_here

# 선택사항: 서버 설정
HOST=0.0.0.0
PORT=8000

# 선택사항: LLM 설정
LLM_MODEL=gemini-1.5-flash-latest
TEMPERATURE=0.7
MAX_CONTEXT_LENGTH=4000
```

### 4. 서버 실행

```bash
# 기본 포트 (8000)에서 실행
uv run python -m src

# 또는 다른 포트에서 실행
PORT=8002 uv run python -m src

# 또는 간단한 명령어
uv run agent
```

서버가 성공적으로 시작되면:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## 🌐 사용법

### 웹 인터페이스

브라우저에서 `http://localhost:8000`에 접속하면 테스트 인터페이스를 사용할 수 있습니다.

### API 엔드포인트

#### Health Check
```bash
curl http://localhost:8000/health
```

#### A2A 프로토콜 질의응답
```bash
curl -X POST http://localhost:8000/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "질문 내용",
    "metadata": {
      "context": "Host Agent가 제공하는 컨텍스트 정보"
    }
  }'
```

#### 간단한 채팅 테스트
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요!",
    "context": "추가 컨텍스트 정보 (선택사항)",
    "contextId": "conversation-123"
  }'
```

## 📋 주요 기능

- **Context 기반 QA**: Host Agent가 제공하는 context를 활용한 정확한 답변
- **대화 기록 유지**: 컨텍스트 ID별 연속적인 대화 지원
- **스트리밍 응답**: 실시간 응답 스트리밍
- **A2A 프로토콜**: 표준 Agent-to-Agent 프로토콜 지원
- **MCP 통합**: Model Context Protocol을 통한 도구 확장
- **웹 인터페이스**: 브라우저에서 바로 테스트 가능

## 🔧 에이전트 카드

A2A 에이전트 정보는 다음에서 확인:
```
http://localhost:8000/.well-known/agent.json
```

## 🔧 문제 해결

### 포트 충돌
다른 포트를 사용하세요:
```bash
PORT=8001 uv run python -m src
```

### API 키 오류
`.env` 파일에 올바른 `GOOGLE_API_KEY`가 설정되어 있는지 확인하세요.

### MCP 연결 오류
MCP Runner 서버(`https://mcp-host-runner.onrender.com`)가 일시적으로 사용할 수 없을 수 있습니다. 서버는 MCP 없이도 기본 QA 기능은 정상 작동합니다.

## 📁 프로젝트 구조

```
agent-web_qa_bot/
├── src/
│   ├── agent/              # QA 에이전트 구현
│   ├── executor/           # A2A 실행기
│   ├── mcp_client/         # MCP 클라이언트
│   ├── prompts/            # 프롬프트 템플릿
│   ├── config.py           # 설정 관리
│   └── __main__.py         # 서버 실행 진입점
├── .env                    # 환경 변수 (사용자 생성)
├── agent.config.json       # 에이전트 설정
├── mcpserver.json          # MCP 서버 설정
└── pyproject.toml          # 프로젝트 설정
```

## 🛠 개발 정보

Python 3.12+, Google Gemini API, A2A Protocol, MCP 지원으로 구축된 간단하고 효과적인 QA 에이전트입니다.

Host Agent와 함께 사용하여 웹 페이지 분석, 문서 요약, 질의응답 등 다양한 작업을 수행할 수 있습니다.