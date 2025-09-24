"""QA Executor implementation for Web QA Bot"""

import logging

from a2a.server.agent_execution import AgentExecutor as BaseAgentExecutor, RequestContext
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TaskState,
    TaskStatus,
)
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_text_artifact

from src.agent.qa_agent import QAAgent

logger = logging.getLogger(__name__)


class QAExecutor(BaseAgentExecutor):
    """Executor for QA Agent"""
    
    def __init__(self):
        self._startup_complete = False
        self.agent = QAAgent()
    
    async def startup(self):
        """Initialize the QA agent and executor"""
        if not self._startup_complete:
            try:
                await self.agent.initialize()
                self._startup_complete = True
                logger.info("QAExecutor initialized successfully")
            except Exception as e:
                logger.error(f"QAExecutor initialization failed: {e}")
                self._startup_complete = False
                raise
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute QA request and stream results"""

        # Extract user message from RequestContext
        user_message = self._extract_message(context)

        # Extract context_id and task_id from context (following A2A standard)
        context_id = getattr(context, 'context_id', 'default_context')
        task_id = getattr(context, 'task_id', getattr(context, 'id', 'default_task'))

        try:
            logger.info(f"Processing query: {user_message[:100]}...")

            # Process query and stream response
            response_text = ""
            async for chunk in self.agent.process_query(user_message):
                response_text += chunk

                # Send progress update
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(chunk),
                        ),
                        final=False,
                        context_id=context_id,
                        task_id=task_id,
                    )
                )

            # Send final response as artifact
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=context_id,
                    task_id=task_id,
                    last_chunk=True,
                    artifact=new_text_artifact(
                        name='qa_response',
                        description='QA Agent Response',
                        text=response_text,
                    ),
                )
            )

            # Mark task as completed
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(state=TaskState.completed),
                    final=True,
                    context_id=context_id,
                    task_id=task_id,
                )
            )

            logger.info(f"Query processed successfully for context: {context_id}")

        except Exception as e:
            logger.error(f"Error executing request: {e}")
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            f"Error processing your request: {str(e)}",
                        ),
                    ),
                    final=True,
                    context_id=context_id,
                    task_id=task_id,
                )
            )
    
    def _extract_message(self, context: RequestContext) -> str:
        """Extract user message from RequestContext"""
        user_message = ""
        if hasattr(context, "message") and context.message:
            if hasattr(context.message, "parts") and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, "root") and part.root:
                        if hasattr(part.root, "text"):
                            user_message += part.root.text
                    elif hasattr(part, "text"):
                        user_message += part.text
        return user_message

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel ongoing operation"""

        # Extract context_id and task_id from context
        context_id = getattr(context, 'context_id', 'default_context')
        task_id = getattr(context, 'task_id', getattr(context, 'id', 'default_task'))

        if hasattr(self.agent, 'cancel'):
            await self.agent.cancel()

        # Send cancellation status
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(
                    state=TaskState.canceled,
                    message=new_agent_text_message(
                        "Operation canceled.",
                        context_id,
                        task_id,
                    ),
                ),
                final=True,
                context_id=context_id,
                task_id=task_id,
            )
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self.agent, 'cleanup'):
                await self.agent.cleanup()
            self._startup_complete = False
            logger.info("QAExecutor cleaned up")
        except Exception as e:
            logger.error(f"QAExecutor cleanup error: {e}")
    
    
    @property
    def is_ready(self) -> bool:
        """Check if executor is ready"""
        return self._startup_complete and self.agent is not None