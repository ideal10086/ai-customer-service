import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import http_util


@dataclass
class KnowledgeChunk(ABC):
    content:str


class KnowledgeProvider(ABC):
    provider_id:str
    @abstractmethod
    async def retrieve(self,state:DialogueState) -> list[KnowledgeChunk]:
        pass

class ProductAPIProvider(KnowledgeProvider):
    provider_id = "api.product"
    async def retrieve(self, state: DialogueState) -> List[KnowledgeChunk]:
        # 1.从focused_object中获取商品ID
        product_id = state.focused_object.id
        # 2.调用商品查询接口，获取商品信息
        text = await self._fetch(product_id)
        # 3.返回商品信息
        return [
            KnowledgeChunk(
                content="商品信息：\n"+ json.dumps(text,ensure_ascii=False,indent=2)
            )
        ]

    async def _fetch(self, product_id):
        # 向商品查询接口 /products/{product_id} 发送http请求，获取商品信息
        url = f"{settings.commerce_api_base_url}/products/{product_id}"
        response = await http_util.http_client.get(url)
        return response.json()["data"]


class OrderAPIProvider(KnowledgeProvider):
    provider_id = "api.order"
    async def retrieve(self, state: DialogueState) -> List[KnowledgeChunk]:
        # 1.从focused_object中获取订单ID
        order_number = state.focused_object.id
        # 2.调用订单查询接口，获取订单信息
        order_payload, logistics_payload = await asyncio.gather(
            self._fetch_order(order_number),
            self._fetch_logistics(order_number),
        )
        result_dict = {
                        "order_number": order_number,
                        "order": order_payload,
                        "logistics": logistics_payload,
                    }
        # 3.返回订单信息
        return [
            KnowledgeChunk(
                content="订单与物流信息：\n" + json.dumps(
                    result_dict,ensure_ascii=False,indent=2)
            )
        ]
    async def _fetch_order(self, order_number)->dict:
        url = f"{settings.commerce_api_base_url}/orders/{order_number}"
        response = await http_util.http_client.get(url)
        return response.json()["data"]

    async def _fetch_logistics(self, order_number)->dict:
        url = f"{settings.commerce_api_base_url}/orders/{order_number}/logistics"
        response = await http_util.http_client.get(url)
        return response.json()["data"]

class FAQProvider(KnowledgeProvider):
    provider_id = "faq.default"

    async def retrieve(self, state: DialogueState) -> List[KnowledgeChunk]:
        return [KnowledgeChunk(content="未检索到相关问题（faq）")]


class RAGProvider(KnowledgeProvider):
    provider_id = "rag.default"

    async def retrieve(self, state: DialogueState) -> List[KnowledgeChunk]:
        return [KnowledgeChunk(content="未检索到相关问题（rag）")]
