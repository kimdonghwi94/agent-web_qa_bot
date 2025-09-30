"""Main entry point for Web QA Bot Agent"""

import asyncio

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse

from src.executor.qa_executor import QAExecutor
from src.config import Config


def get_agent_config() -> dict:
    """Get hardcoded agent configuration"""
    return Config.get_agent_info()


def create_mcp_skills_from_tools(server_name: str, tools: list[dict]) -> list[AgentSkill]:
    """Create individual AgentSkill objects for each MCP tool"""
    if not tools:
        return []

    skills = []

    for tool in tools:
        tool_name = tool.get("name", "")
        tool_desc = tool.get("description", "")

        if not tool_name:
            continue

        # Generate skill ID based on tool name
        skill_id = f"mcp_{server_name}_{tool_name}"

        # Generate human-readable skill name
        skill_name = tool_name.replace('_', ' ').replace('-', ' ').title()

        # Use tool's actual description
        description = tool_desc if tool_desc else f"{tool_name} tool functionality"

        # Generate tags based on tool name and server
        tags = ["mcp", server_name, tool_name]

        skill = AgentSkill(
            id=skill_id,
            name=skill_name,
            description=description,
            tags=tags,
            examples=[],
        )

        skills.append(skill)

    return skills


async def create_agent_skills(tools):
    """Create agent skills from all available MCP servers"""
    if not tools:
        return []

    all_skills = []

    # Process all MCP server tools
    for server_name, mcp_tools in tools.items():
        if not mcp_tools:  # Skip servers without tools
            continue

        new_meta = []
        for tool in mcp_tools:
            meta_tool = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "server": server_name
            }
            new_meta.append(meta_tool)

        if new_meta:  # Only create skills if there are tools
            mcp_skills = create_mcp_skills_from_tools(server_name, new_meta)
            all_skills.extend(mcp_skills)

    return all_skills


async def create_app():
    """Create the A2A Starlette application"""

    # Get agent configuration
    agent_config = get_agent_config()
    config = Config()

    # Get agent info from config with defaults
    agent_info = agent_config.get("agent", {})

    # Hardcoded deployment info
    deployment = {
        "url": f"http://{config.HOST}:{config.PORT}/",
        "redirect_url": "https://github.com/"
    }

    # Create agent executor
    agent_executor = QAExecutor()
    await agent_executor.startup()

    # Create skills from MCP tools
    all_skills = await create_agent_skills(agent_executor.agent.mcp_tools)

    # Add built-in web analyzer skill
    web_analyzer_skill = AgentSkill(
        id="web_analyzer",
        name="웹 페이지 분석",
        description="웹 페이지 URL을 분석하여 마크다운 형식으로 내용을 추출합니다",
        tags=["web", "analyzer", "url", "markdown"],
        examples=["https://example.com 이 사이트를 분석해주세요"]
    )
    all_skills.append(web_analyzer_skill)

    # Add custom skills from config
    config_skills = agent_config.get("skills", [])
    for skill_config in config_skills:
        skill = AgentSkill(
            id=skill_config["id"],
            name=skill_config["name"],
            description=skill_config["description"],
            tags=skill_config.get("tags", []),
            examples=skill_config.get("examples", []),
        )
        all_skills.append(skill)

    # Create agent card
    agent_card = AgentCard(
        name=agent_info.get("name", "김동휘 웹사이트 QA 챗봇"),
        description=agent_info.get("description", "김동휘 웹사이트 방문자를 위한 전용 질의응답 챗봇. 한국어로 친근하게 소통하며 웹사이트 관련 질문에 정확하게 답변합니다."),
        url=deployment.get("url", "http://localhost:8000/"),
        version=agent_info.get("version", "1.0.0"),
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text/plain", "application/json"],
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
            extensions=None
        ),
        skills=all_skills,
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = server.build()

    @app.route("/health")
    async def health(request):
        return JSONResponse({
            "status": "healthy",
            "agent": "김동휘 웹사이트 QA 챗봇",
            "qa_engine": "active"
        })

    @app.route("/", methods=["GET"])
    async def homepage(request):
        html_content = '''<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>김동휘 웹사이트 QA 챗봇</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        margin: 0;
        background: #f8f9fa;
        min-height: 100vh;
        color: #333;
      }
      .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 30px;
      }
      h1 {
        margin: 0 0 8px;
        font-size: 28px;
        color: #2c3e50;
        text-align: center;
        font-weight: 700;
        letter-spacing: -0.5px;
      }
      .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 14px;
        margin-bottom: 24px;
      }
      .info-panel {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      }
      .info-panel h3 {
        margin: 0 0 12px;
        font-size: 16px;
        color: #495057;
        font-weight: 600;
      }
      .info-panel p {
        margin: 0 0 8px;
        font-size: 14px;
        line-height: 1.5;
        color: #6c757d;
      }
      .chat {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 24px;
        min-height: 400px;
        overflow-y: auto;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 16px;
      }
      .msg {
        padding: 12px 16px;
        border-radius: 16px;
        margin: 8px 0;
        max-width: 80%;
        white-space: pre-wrap;
        animation: fadeIn 0.3s ease-in;
        font-size: 14px;
        line-height: 1.5;
      }
      .status {
        padding: 8px 12px;
        border-radius: 12px;
        margin: 4px 0;
        max-width: 60%;
        font-size: 12px;
        color: #6c757d;
        background: #f1f3f5;
        border: 1px solid #dee2e6;
        font-style: italic;
        animation: fadeIn 0.3s ease-in;
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .user {
        background: #007bff;
        color: white;
        margin-left: auto;
        font-weight: 500;
      }
      .agent {
        background: #ffffff;
        color: #495057;
        border: 1px solid #dee2e6;
      }
      .input-section {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      }
      .context-input {
        margin-bottom: 16px;
      }
      .context-input label {
        display: block;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 14px;
        color: #495057;
      }
      .context-input textarea {
        width: 100%;
        padding: 12px;
        border: 1px solid #ced4da;
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        resize: vertical;
        min-height: 80px;
        outline: none;
        transition: all 0.2s ease;
        box-sizing: border-box;
      }
      .context-input textarea:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
      }
      .input {
        display: flex;
        gap: 8px;
      }
      input, button { font-size: 14px; }
      input {
        flex: 1;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #ced4da;
        background: white;
        color: #495057;
        outline: none;
        transition: all 0.2s ease;
      }
      input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
      }
      button {
        padding: 12px 20px;
        border-radius: 8px;
        border: none;
        background: #007bff;
        color: white;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s ease;
      }
      button:hover {
        background: #0056b3;
      }
      button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .hint {
        color: #6c757d;
        font-size: 12px;
        margin-top: 16px;
        text-align: center;
      }
      a {
        color: #007bff;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
      code {
        background: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        font-size: 11px;
        border: 1px solid #e9ecef;
      }
      .examples {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
        margin-top: 16px;
      }
      .example {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 13px;
      }
      .example:hover {
        background: #e9ecef;
        border-color: #007bff;
      }
      .example-title {
        font-weight: 600;
        color: #495057;
        margin-bottom: 4px;
      }
      .example-text {
        color: #6c757d;
        font-style: italic;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>김동휘 웹사이트 QA 챗봇</h1>
      <p class="subtitle">김동휘 웹사이트 방문자를 위한 전용 질의응답 서비스</p>

      <div class="info-panel">
        <h3>🤖 에이전트 정보</h3>
        <p><strong>기능:</strong> Context 기반 질의응답, 대화 기록 유지, 스트리밍 응답</p>
        <p><strong>LLM:</strong> Google Gemini</p>
        <p><strong>프로토콜:</strong> A2A (Agent-to-Agent)</p>
      </div>

      <div class="chat" id="chat">
        <div class="msg agent">
          안녕하세요! 김동휘 웹사이트 QA 챗봇입니다. 😊<br><br>
          <strong>사용 방법:</strong><br>
          1. 김동휘에 대한 질문이나 웹사이트 관련 질문을 입력하세요<br>
          2. Context 란에 추가 정보가 있다면 입력하세요 (선택사항)<br>
          3. 한국어로 친근하게 답변해드립니다<br><br>
          <em>예시 질문을 클릭하여 바로 사용해보세요!</em>
        </div>
      </div>

      <div class="input-section">
        <div class="context-input">
          <label for="context">Context (Host Agent가 제공하는 정보)</label>
          <textarea id="context" placeholder="관련 문서나 웹 페이지 내용을 여기에 입력하세요... (선택사항)"></textarea>
        </div>

        <div class="input">
          <input id="text" placeholder="질문을 입력하세요..." />
          <button id="send">전송</button>
        </div>

        <div class="examples">
          <div class="example" onclick="setExample('김동휘는 어떤 일을 하나요?', '')">
            <div class="example-title">김동휘 소개</div>
            <div class="example-text">김동휘는 어떤 일을 하나요?</div>
          </div>
          <div class="example" onclick="setExample('이 프로젝트에 대해 설명해주세요', 'Context 예시: 이 프로젝트는 김동휘가 개발한 웹사이트 QA 챗봇으로, A2A 프로토콜을 기반으로 동작하며 방문자들의 질문에 한국어로 답변합니다.')">
            <div class="example-title">프로젝트 설명</div>
            <div class="example-text">이 프로젝트에 대해 설명해주세요</div>
          </div>
          <div class="example" onclick="setExample('김동휘의 기술 스택은 무엇인가요?', '')">
            <div class="example-title">기술 스택</div>
            <div class="example-text">김동휘의 기술 스택은 무엇인가요?</div>
          </div>
          <div class="example" onclick="setExample('연락하려면 어떻게 해야 하나요?', '')">
            <div class="example-title">연락 방법</div>
            <div class="example-text">연락하려면 어떻게 해야 하나요?</div>
          </div>
        </div>
      </div>

      <div class="hint">
        이 UI는 <code>/chat</code> 엔드포인트로 메시지를 전송합니다. Agent Card는 <a href="/.well-known/agent.json">/.well-known/agent.json</a>에서 확인할 수 있습니다.
      </div>
    </div>
    <script>
      const chat = document.getElementById('chat');
      const input = document.getElementById('text');
      const contextInput = document.getElementById('context');
      const btn = document.getElementById('send');

      function safeUUID() {
        try {
          if (typeof crypto !== 'undefined' && crypto && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
          }
        } catch (_) {}
        const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
        return Date.now().toString(16) + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
      }
      let contextId = safeUUID();

      function setExample(question, context) {
        input.value = question;
        contextInput.value = context;
        input.focus();
      }

      function addMsg(text, cls) {
        const div = document.createElement('div');
        div.className = 'msg ' + cls;
        div.innerHTML = text.replace(/\\n/g, '<br>');
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
      }

      function addStatusMsg(text) {
        const div = document.createElement('div');
        div.className = 'status';
        div.textContent = text;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
        return div;
      }

      let isProcessing = false;
      let isComposing = false;

      async function send() {
        const text = input.value.trim();
        const context = contextInput.value.trim();
        if (!text || isProcessing) return;

        isProcessing = true;
        input.value = '';
        btn.disabled = true;

        // Show user message
        let displayText = text;
        if (context) {
          displayText += '<br><br><em style="color: #6c757d; font-size: 12px;">📄 Context 포함</em>';
        }
        addMsg(displayText, 'user');

        const statusMsg = addStatusMsg('답변을 준비하고 있습니다...');

        try {
          const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text,
              context: context || null,
              contextId
            })
          });

          if (statusMsg && statusMsg.parentNode) {
            statusMsg.parentNode.removeChild(statusMsg);
          }

          if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
          const data = await res.json();
          if (data && data.reply) {
            addMsg(data.reply, 'agent');
          } else {
            addMsg('[응답 없음]', 'agent');
          }
        } catch (e) {
          if (statusMsg && statusMsg.parentNode) {
            statusMsg.parentNode.removeChild(statusMsg);
          }
          console.error('POST /chat failed', e);
          addMsg('오류: ' + e.message, 'agent');
        } finally {
          btn.disabled = false;
          isProcessing = false;
          input.focus();
        }
      }

      btn.addEventListener('click', send);
      input.addEventListener('compositionstart', () => { isComposing = true; });
      input.addEventListener('compositionend', () => { isComposing = false; });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          if (e.isComposing || isComposing) return;
          e.preventDefault();
          send();
        }
      });

      input.focus();
    </script>
  </body>
</html>'''
        return HTMLResponse(html_content)

    @app.route("/chat", methods=["POST"])
    async def chat_endpoint(request):
        try:
            body = await request.json()
            user_message = body.get("text", "")
            context = body.get("context")
            context_id = body.get("contextId", "default_context")

            if not user_message:
                return JSONResponse({"error": "Message is required"}, status_code=400)

            # Add context to query if provided
            query_with_context = user_message
            if context:
                query_with_context = f"Context: {context}\n\nQuestion: {user_message}"

            # Process query
            final_response = ""
            async for chunk in agent_executor.agent.process_query(query_with_context):
                final_response += chunk

            response = final_response if final_response else "응답을 생성할 수 없습니다."

            return JSONResponse({"reply": response})

        except Exception as e:
            import traceback
            print(f"Chat endpoint error: {e}")
            print(traceback.format_exc())
            return JSONResponse({"error": str(e)}, status_code=500)

    return app


def main():
    """Main entry point"""
    import uvicorn
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Load configuration
    config = Config()

    # Create and run the app
    app = asyncio.run(create_app())

    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()