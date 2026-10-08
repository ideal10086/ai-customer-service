from pydantic import BaseModel

class ChatObjectPayload(BaseModel):
    type: str
    id: str
    title: str | None = None
    attributes: dict = {}

class ChatRequest(BaseModel):
    sender_id: str
    text: str | None = None
    object: ChatObjectPayload | None = None
    message_id: str | None = None

class BotMessageResponse(BaseModel):
    text: str | None = None
    object: ChatObjectPayload | None = None

class ChatResponse(BaseModel):
    sender_id: str
    message_id: str
    messages: list[BotMessageResponse]

class ChatHistoryMessageResponse(BaseModel):
    role: str
    text: str | None = None
    object: ChatObjectPayload | None = None

class ChatHistoryResponse(BaseModel):
    sender_id: str
    messages: list[ChatHistoryMessageResponse]

class HistoryMessage(BaseModel):
    """
    历史消息
    """
    role: str  # user or bot
    text: str | None = None
    object: ChatObjectPayload | None = None

class HistoryResponse(BaseModel):
    """
    历史消息列表
    `GET /api/chat/history` 的返回体。
    """
    sender_id: str
    messages: list[HistoryMessage]


class ChatHistoryMessage(BaseModel):
    session_id:str
    role: str
    text: str | None = None
    object: ChatObjectPayload | None = None
