# Web QA Bot - 빠른 실행 가이드

## 📦 설치 및 실행 (3단계)

### 1. 환경 설정
```bash
# .env 파일 생성
echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
```

### 2. 의존성 설치
```bash
uv sync
```

### 3. 서버 실행
```bash
# 기본 실행 (포트 8000)
uv run python -m src

# 다른 포트에서 실행
PORT=8002 uv run python -m src
```

## 🌐 접속 방법

- **웹 인터페이스**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Agent Card**: http://localhost:8000/.well-known/agent.json

## 🔧 빠른 테스트

```bash
# Health check
curl http://localhost:8000/health

# 간단한 질문
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "안녕하세요!"}'
```

## ⚠️ 문제 해결

**포트 충돌**: `PORT=8001 uv run python -m src`
**API 키 오류**: `.env` 파일의 `GOOGLE_API_KEY` 확인

그게 다입니다! 🚀