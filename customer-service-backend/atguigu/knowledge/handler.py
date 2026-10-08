from typing import List, Dict

from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.knowledge.providers import KnowledgeProvider, KnowledgeChunk
from atguigu.knowledge.responder import KnowledgeResponder


class KnowledgeHandler:
    def __init__(
            self,
            knowledge_intents:Dict[str,KnowledgeIntent],
            provider_registry:Dict[str,KnowledgeProvider],
            knowledge_responder:KnowledgeResponder,
    ):
        self.knowledge_intents = knowledge_intents
        self.provider_registry = provider_registry
        self.knowledge_responder = knowledge_responder

    async def handle(self,intents:List[str],state:DialogueState)->List[BotMessage]:
        # 1.根据意图寻找知识来源
        provider_ids = []
        for intent in intents:
            if intent in self.knowledge_intents:
                provider_ids.extend(self.knowledge_intents[intent].provider_ids)
        # 2.去重
        provider_ids = list(set(provider_ids))
        # 3.调用知识来源获取知识
        chunks:List[KnowledgeChunk] = []
        for provider_id in provider_ids:
            provider:KnowledgeProvider = self.provider_registry.get(provider_id)
            if provider is not None:
                chunks.extend(await provider.retrieve(state))
        # 4.生成响应
        return await self.knowledge_responder.respond(
            user_message= state.pending_turn.input_message,
            recent_turns= state.get_current_session().turns,
            chunks= chunks
        )
