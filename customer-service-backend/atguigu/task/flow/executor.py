from dataclasses import asdict
from pickletools import long1
from typing import List

from atguigu.domain.contexts import CollectSystemContext
from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.runner import ActionRunner, ActionCall
from atguigu.task.flow.links import FlowStepLink, StaticLink, ConditionalLink
from atguigu.task.flow.models import FlowsList, Flow
from atguigu.task.flow.steps import FlowStep, FlowStepType, ActionFlowStep, CollectSlotStep, StartFlowStep, \
    ResponseDefinition, EndFlowStep


class FlowExecutor():
    #外层循环
    async def run_task(self, state: DialogueState, flows: FlowsList, action_runner: ActionRunner,
                       max_steps: int = 1000) -> List[BotMessage]:

        step_count = 0
        messages: List[BotMessage] = []
        while True:
            # 1.推进流程，查找action
            action_call = await self.advance_util_action(state, flows)
            if action_call.action_name == "action_listen":
                break
            # 2.运行action
            action_result = await action_runner.run(action_call, state)
            # 3.更新state
            state.set_slots(action_result.slot_updates)
            # 4.更新messages
            messages.extend(action_result.messages)

            step_count += 1
            if step_count >= max_steps:
                raise RuntimeError(
                    f"Flow execution exceeded {max_steps} steps."
                )
        return messages
    #内层循环
    async def advance_util_action(self,state: DialogueState, flows: FlowsList) -> ActionCall:
        while True:
            context = state.get_current_task_context()

            if context is not None:
                flow_id = context.flow_id
                step_id = context.step_id
                flow:Flow = flows.get_flow_by_id(flow_id)
                step:FlowStep|None = flow.get_step_by_id(step_id)
                if step is None:
                    print("文件flow-step配置有误")
                action_call:ActionCall|None = self.run_step(step,state,flows)
                print(f"流程是f{flow_id},步骤是{step_id}")
                if action_call is not None:
                    return action_call
            else:
                return ActionCall(action_name="action_listen")

    def run_step(self,step: FlowStep,state: DialogueState, flows: FlowsList) -> ActionCall:
        if isinstance(step,StartFlowStep):
            self._handle_start_step(step,state)
            return None
        elif isinstance(step,ActionFlowStep):
            return self._handle_action_step(step,state)
        elif isinstance(step,CollectSlotStep):
            return self._handle_collect_step(step,state,flows)
        elif isinstance(step,EndFlowStep):
            return self._handle_end_step(step, state, flows)
        else:
            return None

    def _advance_to_next_step(self, step: FlowStep, state: DialogueState):
        next_list: List[FlowStepLink] = step.next
        for link in next_list:
            """
            # 配置中的条件表达式（字符串）
            condition_str = "slots.get('order_status') == '已发货' and slots.get('amount') > 100"

            # 当前状态中的值
            slots = {"order_status": "已发货", "amount": 299}

            # eval 执行字符串表达式
            result = eval(condition_str, {"__builtins__": {}}, {"slots": slots, "context": {}})
            # → True
            """
            if isinstance(link, ConditionalLink):
                globals = {"__builtins__": {}}  # 禁用所有内置函数（open、import 等），安全措施
                locals = {
                    "slots": state.active_task.slots if state.active_task else {},  # 把 slots 注入为变量
                    "context": asdict(state.get_current_task_context())  # 把 context 转为 dict 注入
                }
                # link.condition 是字符串，比如 "slots.get('order_status') == '已发货'"
                if bool(eval(link.condition, globals, locals)):
                    state.get_current_task_context().step_id = link.target  # 条件满足，跳转到目标步骤
                    break
            elif isinstance(link, StaticLink):
                next_step_id = link.target
                state.get_current_task_context().step_id = next_step_id
                break
        return None

    def _handle_start_step(self, step:FlowStep, state:DialogueState):
        self._advance_to_next_step(step,state)
        return None

    def _handle_action_step(self, step:ActionFlowStep, state:DialogueState):
        # 直接跳转到下一步
        self._advance_to_next_step(step, state)
        # 返回ActionCall
        if isinstance(step.args, dict):
            return ActionCall(action_name=step.action, action_kwargs=step.args)
        elif isinstance(step.args, str):
            # 例如 system_collect_information系统任务中 args: context.response
            args = asdict(state.get_current_task_context())[step.args.split(".")[1]]
            return ActionCall(action_name=step.action, action_kwargs=args)
        else:
            return ActionCall(action_name=step.action)

    def _handle_collect_step(self, step:CollectSlotStep, state:DialogueState, flows):
        #尝试填槽
        # 1.尝试从focused_object自动填槽
        if state.focused_object is not None:
            if step.slot_name == "order_number" and state.focused_object.type == "order":
                state.set_slots({step.slot_name: state.focused_object.id})
            if step.slot_name == "product_id" and state.focused_object.type == "product":
                state.set_slots({step.slot_name: state.focused_object.id})
        # 2.判断填槽是否成功
        if state.active_task.slots.get(step.slot_name) is not None:
            # 3.如果槽位有值，且有校验，则执行校验
            if step.validation is not None:
                conditional_str:str|None = step.validation.condition
                globals = {"__builtins__": {}}
                locals = {
                    "slots": state.active_task.slots,
                    "context": asdict(state.get_current_task_context())
                }
                if bool(eval(conditional_str, globals, locals)):
                    # 4.如果校验通过则推进到下一步
                    self._advance_to_next_step(step, state)
                    return None
                else:
                    # 5.如果校验不通过则清空槽位：将槽位值设为None
                    state.remove_slot(step.slot_name)
                    # 6.判断是否有失败回复
                    failure_response: ResponseDefinition | None= step.validation.failure_response
                    if step.validation.failure_response is not None:
                        # 7.返回 ActionCall(action_response)
                        return ActionCall(action_name="action_response", action_kwargs=asdict(failure_response))
                    else:
                        return None
            else:
                # 无需校验
                self._advance_to_next_step(step, state)
                return None
        else:
            # 槽位没有值，激活系统流程
            state.start_system_task(
                CollectSystemContext(
                    flow_id="system_collect_information",
                    step_id=flows.get_flow_by_id("system_collect_information").get_start_step().id,
                    slot_name=step.slot_name,
                    response=asdict(step.response)
                )
            )
            return None

    def _handle_end_step(self, step, state, flows):
        if state.active_system_task:
            state.end_system_task()
        else:
            state.cancel_active_task()
            return None
