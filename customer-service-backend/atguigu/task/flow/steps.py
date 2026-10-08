from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any

from atguigu.task.flow.links import FlowStepLink, StaticLink, ConditionalLink, FallbackLink


class FlowStepType(str, Enum):
    START = "start"
    ACTION = "action"
    COLLECT = "collect"
    END = "end"


@dataclass(slots=True)
class ResponseDefinition:
    mode: str = "static"
    text: str | None = None
    prompt: str | None = None


@dataclass(slots=True)
class SlotValidation:      #TODO有啥用  校验使用
    condition: str | None = None
    failure_response: ResponseDefinition | None = None


@dataclass(slots=True)
class FlowStep:
    id: str
    type: FlowStepType
    next: List[FlowStepLink] = field(default_factory=list)
    description: str = ""

    @classmethod
    def from_dict(cls, step_data):
        step_type = step_data.get("type")
        flow_step_class = STEP_TYPE_TO_CLASS.get(step_type)
        return flow_step_class.from_dict(step_data)


def build_links(next_data:str|List[dict]) -> List[FlowStepLink]:
    next_list = []
    if isinstance(next_data,str):
        next_list.append(StaticLink(target=next_data))
    else:
        for link_data in next_data:
            if link_data.get("if"):
                next_list.append(ConditionalLink(
                    target=link_data.get("then"),
                    condition=link_data.get("if")
                ))
            else:
                next_list.append(FallbackLink(target=link_data.get("else")))
    return next_list


@dataclass(slots=True)
class StartFlowStep(FlowStep):

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]):
        return cls(
            id=step_data.get("id",""),
            type = FlowStepType.START,
            description = step_data.get("description",""),
            next = build_links(step_data.get("next", ""))
        )


@dataclass(slots=True)
class ActionFlowStep(FlowStep):
    """
    - id: show_order_status
      type: action
      action: action_response
      args:
        text: "订单{{ slots.order_number }}当前状态是：{{ slots.order_status }}。{{ slots.order_summary }}"
      next: end
    """
    action: str = ""
    args: Dict[str, Any] | str = field(default_factory=dict)

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "ActionFlowStep":
        return cls(
            id=step_data.get("id"),
            type=FlowStepType.ACTION,
            next=build_links(step_data.get("next", "")),
            description=step_data.get("description", ""),
            action=step_data.get("action"),
            args=step_data.get("args", {}),
        )


@dataclass(slots=True)
class CollectSlotStep(FlowStep):
    """
    - id: ask_order_number
      type: collect
      slot_name: order_number
      response:
        mode: "static"
        text: "请告诉我你的订单号。"
        prompt: "提示词"
      next: ask_refund_reason
      validateion:
        condition:"len({{order_number}})>0"
        failure_response:
            mode: "static"
            text: "请输入订单号。"
    """
    slot_name: str = ""
    response: ResponseDefinition = field(default_factory=ResponseDefinition)
    validation: SlotValidation | None = None

    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "CollectSlotStep":
        validation_data = step_data.get("validation") #TODO 检验步骤
        return cls(
            id=step_data.get("id"),
            type=FlowStepType.COLLECT,
            next=build_links(step_data.get("next", "")),
            description=step_data.get("description", ""),
            slot_name=step_data.get("slot_name"),
            response = ResponseDefinition(**step_data.get("response",{})),
            validation = SlotValidation(
                condition=validation_data["condition"],
                failure_response=ResponseDefinition(**validation_data["failure_response"])
            ) if validation_data else None
        )


@dataclass(slots=True)
class EndFlowStep(FlowStep):


    @classmethod
    def from_dict(cls, step_data: Dict[str, Any]) -> "EndFlowStep":
        return cls(
            id=step_data.get("id"),
            type= FlowStepType.END,
            next= build_links(step_data.get("next", "")),
            description=step_data.get("description", ""),
        )

STEP_TYPE_TO_CLASS = {
    "start": StartFlowStep,
    "action": ActionFlowStep,
    "collect": CollectSlotStep,
    "end": EndFlowStep,
}
