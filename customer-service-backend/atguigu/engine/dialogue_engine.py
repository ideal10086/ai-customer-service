# atguigu/engine/dialogue_engine.py
import time
from typing import List, Tuple

from atguigu.chitchat.hander import ChitchatHandler
from atguigu.clarify.responder import ClarifyResponder
from atguigu.domain.contexts import CollectSystemContext
from atguigu.domain.message import UserMessage, ProcessResult, BotMessage, MessageType
from atguigu.domain.state import DialogueState, Turn, FocusedObject
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.plan.plan_models import TurnPlanValidator, ClarifyReason
from atguigu.plan.planer import TurnPlanner
from atguigu.task.commands.models import StartFlowCommand, SetSlotsCommand, Command
from atguigu.task.flow.models import FlowsList
from atguigu.task.flow.steps import CollectSlotStep
from atguigu.task.taskhandler import TaskHandler

# 关键词 → flow_id 映射表（按优先级排序，匹配到即停止）
INTENT_KEYWORDS: List[Tuple[str, str]] = [
    ("退款", "refund_request"),
    ("退货", "refund_request"),
    ("退换", "refund_request"),
    ("物流", "logistics_tracking"),
    ("快递", "logistics_tracking"),
    ("配送", "logistics_tracking"),
    ("发货", "logistics_tracking"),
    ("运输", "logistics_tracking"),
    ("订单状态", "order_status_query"),
    ("订单", "order_status_query"),
    ("查单", "order_status_query"),
    ("推荐", "similar_product_recommendation"),
    ("相似", "similar_product_recommendation"),
    ("人工", "human_handoff"),
    ("转接", "human_handoff"),
    ("客服", "human_handoff"),
    ("你好", "onboarding"),
    ("帮助", "onboarding"),
    ("功能", "onboarding"),
    ("欢迎", "onboarding"),
    ("嗨", "onboarding"),
]

DEFAULT_FLOW = "onboarding"


class DialogueEngine:

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowledgeHandler,
            chitchat_handler: ChitchatHandler,
            clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator

    def _classify_intent(self, text: str) -> str:
        """基于关键词匹配将用户输入映射到 flow_id。"""
        if not text:
            return DEFAULT_FLOW
        for keyword, flow_id in INTENT_KEYWORDS:
            if keyword in text:
                return flow_id
        return DEFAULT_FLOW

    async def _handle_text_message(self, state: DialogueState, ) -> list[BotMessage]:
        # 1.预测轮次计划
        turn_plan = await self.turn_planner.predict(
            state, self.task_handler.flowers, self.knowledge_handler.knowledge_intents
        )
        # 2.验证轮次计划
        validation = self.turn_plan_validator.validate(
            turn_plan, state=state, knowledge_intents=self.knowledge_handler.knowledge_intents,
        )
        # 3.如果轮次计划无效，则进行澄清
        if not validation.valid:
            return await self._clarify(
                state=state,
                reason=validation.reason,
            )
        # 4.如果轮次计划有效，则执行任务或知识处理
        if turn_plan.task is not None:
            return await self.task_handler.handle(
                commands=turn_plan.task.commands,
                state=state,
            )
        elif turn_plan.knowledge is not None:
            if state.active_task:
                state.interrupt_active_task()
            return await self.knowledge_handler.handle(
                state=state,
                intents=turn_plan.knowledge.intents,
            )
        if state.active_task:
            state.interrupt_active_task()
        return await self.chitchat_handler.handle(state=state)

    async def _handle_object_message(self, message: UserMessage, state: DialogueState, ) -> list[BotMessage]:
        state.focused_object = FocusedObject.from_dict(message.object.to_dict())
        command = self._object_slot_command(
            message=message,
            state=state,
            flows=self.task_handler.flowers,
        )
        # 2.如果没有生成命令，则进行澄清
        if command is None:
            return await self.clarify_responder.respond(
                state=state,
                reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
            )
        # 3.如果生成了命令，则执行任务
        return await self.task_handler.handle(commands=[command], state=state)

    async def process(self, user_message:UserMessage,state: DialogueState) -> ProcessResult:
        self._prepare_session(state)
        state.begin_turn(user_message)

        if user_message.type is MessageType.TEXT:
            messages = await self._handle_text_message(
                state=state,
            )
        else:
            messages = await self._handle_object_message(
                message=user_message,
                state=state,
            )

        state.pending_turn.assistant_messages.extend(messages)
        state.commit_pending_turn(bot_message=messages)

        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages,
        )

    def _prepare_session(self, state:DialogueState):
        #获取当前会话
        session = state.get_current_session()
        now = time.time()
        # 判断session是否存在
        if session is None:
            state.start_session()
            return
        if now - session.last_activity_at > 60*60:
            #会话超时
            #关闭state，session中的最后一次对话（close_at）
            state.close_current_session(now)
            #清理运行状态
            state.reset_runtime_sate_for_new_session(now)
            #创建新会话
            state.start_session()
        else:
            #会话未超时
            state.update_session_last_activity(now)

    def _object_slot_command(self, message: UserMessage, state: DialogueState, flows: FlowsList) -> Command | None:
        message_object = message.object
        object_type = message_object.type.strip().lower()
        # 获取当前活动收集的槽位名称，如果有则返回槽位名称，如果没有则返回None
        collect_slot_name = self._current_collect_slot_name(state=state, flows=flows)
        # 如果返回有槽位名称且对象类型匹配，构造对应的SetSlotsCommand返回，否则返回None
        if object_type == "order" and collect_slot_name == "order_number":
            return SetSlotsCommand(
                command="set_slots",
                slots={"order_number": message_object.id},
            )
        if object_type == "product" and collect_slot_name == "product_id":
            return SetSlotsCommand(
                command="set_slots",
                slots={"product_id": message_object.id},
            )
        return None

    @staticmethod
    def _current_collect_slot_name(state: DialogueState, flows: FlowsList) -> str | None:
        # 检查活动系统流程是否为搜集槽位的流程
        if isinstance(state.active_system_task, CollectSystemContext):
            return state.active_system_task.slot_name or None
        # 检查活动任务是否为任务流程中collect类型的Step
        active_task = state.active_task
        if active_task is None:
            return None
        current_flow = flows.get_flow_by_id(active_task.flow_id)
        current_step = current_flow.get_step_by_id(active_task.step_id)
        if not isinstance(current_step, CollectSlotStep):
            return None
        return current_step.slot_name

    async def _clarify(self, state: DialogueState, reason: ClarifyReason, ) -> list[BotMessage]:
        return await self.clarify_responder.respond(
            state=state,
            reason=reason,
        )
