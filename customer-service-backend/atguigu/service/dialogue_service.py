from typing import List

from atguigu.api.schemas import ChatHistoryMessage, ChatObjectPayload
from atguigu.domain.message import UserMessage, ProcessResult, BotMessage
from atguigu.domain.state import DialogueState, Turn
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_repository import DialogueStateRepository

class DialogueService:
    def __init__(self,dialogue_state_repository: DialogueStateRepository,
            dialogue_engine: DialogueEngine):
        """
        定义初始化方法，用于初始化对话服务所需的各种参数和组件
        """
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def process_message(self,message:UserMessage)->ProcessResult:
        """
          定义处理消息的方法，用于处理传入的消息并返回处理结果
        """
        # 1.通过dialogue_state_repository获取对话状态
        state:DialogueState = await self.dialogue_state_repository.load(message.sender_id)
        # 2.通过dialogue_engine处理最新消息
        result:ProcessResult = await self.dialogue_engine.process(message,state)
        # 3.通过dialogue_state_repository保存对话状态
        await self.dialogue_state_repository.save(state)
        return result

    async def get_user_history(self, sender_id: str) -> list[ChatHistoryMessage]:
        history_messages: list[ChatHistoryMessage] = []
        state: DialogueState = await self.dialogue_state_repository.load(sender_id)
        for session in state.sessions:
            sid: str = session.session_id
            for turn in session.turns:
                # 获取一轮对话的用户消息，将用户消息转换成ChatHistoryMessage对象，添加到history_messages中
                user_message: UserMessage = turn.input_message
                history_messages.append(self._format_message(user_message, sid))
                # 获取一轮对话的BotMessage，将BotMessage转换成ChatHistoryMessage对象，添加到history_messages中
                bot_messages: list[BotMessage] = turn.assistant_messages
                for bot_message in bot_messages:
                    history_messages.append(self._format_message(bot_message, sid))
        return history_messages

    def _format_message(self, message: UserMessage | BotMessage, session_id: str) -> ChatHistoryMessage:
        role = "user" if isinstance(message, UserMessage) else "bot"
        if message.text is not None:
            return ChatHistoryMessage(
                session_id=session_id,
                role=role,
                text=message.text
            )
        else:
            return ChatHistoryMessage(
                session_id=session_id,
                role=role,
                object=ChatObjectPayload(
                    id=message.object.id,
                    title=message.object.title,
                    type=message.object.type,
                    attributes=message.object.attributes
                )
            )
