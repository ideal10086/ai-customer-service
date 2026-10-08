from typing import Any

from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.shared import fetch_product
from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState


class RecommendSimilarProductsAction(Action):
    """类似商品推荐Action"""

    name = "action_recommend_similar_products"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        product_id = state.current_task().slots.get("product_id")
        label = product_id or "这件商品"

        payload = await fetch_product(product_id)
        if payload:
            label = str(payload.get("title") or "").strip() or label

        text = (
            f"我已经收到你对\"{label}\"的相似商品推荐需求。"
            "不过当前版本还没有接入正式的推荐系统，稍后可以继续补上这部分能力。"
        )
        return ActionResult(messages=[BotMessage(text=text)])
