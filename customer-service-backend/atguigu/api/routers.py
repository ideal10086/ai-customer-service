import uuid
from typing import List

from fastapi import APIRouter, Depends

from atguigu.api.dependencies import get_dialogue_service
from atguigu.api.schemas import ChatHistoryResponse, ChatHistoryMessageResponse, ChatResponse, ChatRequest, \
    BotMessageResponse, ChatObjectPayload, ChatHistoryMessage
from atguigu.domain.message import UserMessage, MessageType, MessageObject, BotMessage
from atguigu.domain.state import Turn
from atguigu.service.dialogue_service import DialogueService

router = APIRouter()

@router.get("/api/chat/history",response_model=ChatHistoryResponse)
async def chat_history(sender_id: str):
    return ChatHistoryResponse(
        sender_id=sender_id,
        messages=[
            ChatHistoryMessageResponse(
                role="user",
                text="你好"
            ),
            ChatHistoryMessageResponse(
                role="bot",
                text="你好呀~O(∩_∩)O~"
            )
        ]
    )

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
        chat_request : ChatRequest,
        dialogue_service: DialogueService = Depends(get_dialogue_service)
):
    # 1.将chat_request转换为Message对象
    message:UserMessage = _build_message(chat_request)
    # 2.调用dialogue_service的process_message方法处理消息，并获取处理结果
    process_result = await dialogue_service.process_message(message)
    # 3. 将处理结果转换为ChatResponse对象并返回
    chat_response = _build_response(process_result)
    return chat_response


def _build_message(chat_request : ChatRequest)->UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id or str(uuid.uuid4()),
        type= MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        object=MessageObject(
            type=chat_request.object.type,
            id=chat_request.object.id,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes
        ) if chat_request.object else None
    )


def _build_response(process_result):
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages = [BotMessageResponse(
            text=bot_msg.text,
            object=ChatObjectPayload(
                type=bot_msg.object.type,
                id=bot_msg.object.id,
                title=bot_msg.object.title,
                attributes=bot_msg.object.attributes
            ) if bot_msg.object else None
        ) for bot_msg in process_result.messages]
    )


def _build_object(message: MessageObject) -> ChatObjectPayload | None:
    if message is None:
        return None
    return ChatObjectPayload(
        type=message.type,
        id=message.id,
        title=message.title,
        attributes=message.attributes
    )

def format_message(message:UserMessage|BotMessage)->ChatHistoryMessage:
    role = "user" if isinstance(message,UserMessage) else "bot"
    if message.text is not None:
        return ChatHistoryMessage(
            role=role,
            text=message.text
        )
    else:
        return ChatHistoryMessage(
            role=role,
            object=ChatObjectPayload(
                id=message.object.id,
                title=message.object.title,
                type=message.object.type,
                attributes=message.object.attributes
            )
        )


def _build_history_response(turns:List[Turn])->list[ChatHistoryMessage]:
    history_messages:list[ChatHistoryMessage] = []
    for turn in turns:
       # 获取一轮对话的用户消息，将用户消息转换成ChatHistoryMessage对象，添加到history_messages中
        user_message:UserMessage = turn.input_message
        history_messages.append(format_message(user_message))
        # 获取一轮对话的BotMessage，将BotMessage转换成ChatHistoryMessage对象，添加到history_messages中
        bot_messages: list[BotMessage] = turn.assistant_messages
        for bot_message in bot_messages:
            history_messages.append(format_message(bot_message))
    return history_messages

# @router.get("/api/chat/history",response_model=ChatHistoryResponse)
# async def chat_history(
#         sender_id:str,
#         dialogue_service:DialogueService = Depends(get_dialogue_service)
# ):
#     # 调用service 通过sender_id查询当前用户的历史记录
#     turns:List[Turn] = await dialogue_service.get_user_history(sender_id)
#     # 将查询的对话轮次格式化为 交互消息结构
#     history_messages:list[ChatHistoryMessage] = _build_history_response(turns)
#     # 响应前端
#     return ChatHistoryResponse(
#         sender_id=sender_id,
#         messages=history_messages
#     )


@router.get("/api/chat/history",response_model=ChatHistoryResponse)
async def chat_history(
        sender_id:str,
        dialogue_service:DialogueService = Depends(get_dialogue_service)
):
    # 调用service 通过sender_id查询当前用户的历史记录
    history_messages:list[ChatHistoryMessage] = await dialogue_service.get_user_history(sender_id)
    # 响应前端
    return ChatHistoryResponse(
        sender_id=sender_id,
        messages=history_messages
    )
