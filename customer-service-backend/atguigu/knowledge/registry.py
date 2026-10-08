from abc import ABC

import asyncio

from atguigu.domain.state import DialogueState, FocusedObject
from atguigu.infrastructure.http_util import init_http_client
from atguigu.knowledge.providers import KnowledgeProvider, ProductAPIProvider, OrderAPIProvider


class KnowledgeProviderRegistry(ABC):
    def __init__(self,providers:list[KnowledgeProvider]):
        self.providers = {
            provider.provider_id:provider  for provider in providers
        }

    def get_provider(self,provider_id:str) -> KnowledgeProvider:
        return self.providers[provider_id]

if __name__ == '__main__':
    init_http_client()

    provider_list = [ProductAPIProvider(), OrderAPIProvider()]
    registry = KnowledgeProviderRegistry(provider_list)
    provider = registry.get_provider("api.order")

    state: DialogueState = DialogueState(
        sender_id="user123",
        focused_object=FocusedObject(type="order", id="A20260408002")
    )

    result = asyncio.run(provider.retrieve(state))
    print(result)
