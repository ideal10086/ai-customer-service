# atguigu/domain/state.py
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List

from typer.cli import state

from atguigu.domain.message import UserMessage, BotMessage

@dataclass(slots=True)
class FocusedObject:
    """当前对话聚焦的业务对象（如订单、商品）。"""
    type: str
    id: str
    title: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusedObject":
        return cls(
            type=data["type"],
            id=data["id"],
            title=data.get("title", ""),
            attributes=dict(data.get("attributes", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "attributes": dict(self.attributes)
        }


@dataclass(slots=True)
class Turn:
    """一次对话轮次: 包含一个用户消息和多个机器人消息。"""
    turn_id: str
    input_message: UserMessage
    assistant_messages: List[BotMessage] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Turn":
        return cls(
            turn_id=data["turn_id"],
            input_message=UserMessage.from_dict(data["input_message"]),
            assistant_messages=[BotMessage.from_dict(m) for m in data.get("assistant_messages", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "input_message": self.input_message.to_dict(),
            "assistant_messages": [m.to_dict() for m in self.assistant_messages],
        }


@dataclass(slots=True)
class Session:
    session_id: str
    started_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)
    closed_at: float | None = None
    turns: List[Turn] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            started_at=data.get("started_at", time.time()),
            last_activity_at=data.get("last_activity_at", time.time()),
            closed_at=data.get("closed_at"),
            turns=[Turn.from_dict(t) for t in data.get("turns", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "last_activity_at": self.last_activity_at,
            "closed_at": self.closed_at,
            "turns": [t.to_dict() for t in self.turns],
        }




@dataclass(slots=True)
class TaskContext:
    flow_id: str
    step_id: str | None = None
    slots: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskContext":
        return cls(
            flow_id=data["flow_id"],
            step_id=data.get("step_id"),
            slots=dict(data.get("slots", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "slots": dict(self.slots)
        }

@dataclass(slots=True)
class SystemContext:
    flow_id: str
    step_id: str | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemContext":
        return cls(
            flow_id=data.get("flow_id", ""),
            step_id=data.get("step_id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "base",
            "flow_id": self.flow_id,
            "step_id": self.step_id
        }



@dataclass(slots=True)
class DialogueState:
    sender_id: str
    active_task: TaskContext | None = None
    paused_tasks: List[TaskContext] = field(default_factory=list)
    active_system_task: SystemContext | None = None
    focused_object: FocusedObject | None = None
    sessions: List[Session] = field(default_factory=list)
    current_session_id: str | None = None
    pending_turn: Turn | None = None
    latest_action_name: str | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueState":
        """从字典还原 DialogueState。"""
        state = cls(sender_id=data["sender_id"])
        raw_task = data.get("active_task")
        state.active_task = TaskContext.from_dict(raw_task) if raw_task is not None else None
        state.paused_tasks = [TaskContext.from_dict(t) for t in data.get("paused_tasks", [])]
        raw_sys = data.get("active_system_task")
        state.active_system_task = SystemContext.from_dict(raw_sys) if raw_sys is not None else None
        raw_fo = data.get("focused_object")
        state.focused_object = FocusedObject.from_dict(raw_fo) if raw_fo is not None else None
        state.sessions = [Session.from_dict(s) for s in data.get("sessions", [])]
        state.current_session_id = data.get("current_session_id")
        state.latest_action_name = data.get("latest_action_name")
        return state

    def to_dict(self) -> Dict[str, Any]:
        """序列化为可 JSON 存储的字典（不含 pending_turn，它是处理中的瞬态）。"""
        return {
            "sender_id": self.sender_id,
            "active_task": self.active_task.to_dict() if self.active_task is not None else None,
            "paused_tasks": [t.to_dict() for t in self.paused_tasks],
            "active_system_task": self.active_system_task.to_dict() if self.active_system_task is not None else None,
            "focused_object": self.focused_object.to_dict() if self.focused_object is not None else None,
            "sessions": [s.to_dict() for s in self.sessions],
            "current_session_id": self.current_session_id,
            "latest_action_name": self.latest_action_name,
        }

    def get_current_session(self) -> Session | None:
        return self.sessions[-1] if self.sessions else None

    def start_session(self):
        new_session = Session(session_id=uuid.uuid4().hex)
        self.sessions.append(new_session)
        self.current_session_id = new_session.session_id

    def update_session_last_activity(self, now) :
        self.latest_action_name = now

    def close_current_session(self,now):
        self.get_current_session().closed_at = now
        self.current_session_id = None

    def reset_runtime_sate_for_new_session(self,now):
        self.active_task = None
        self.active_system_task = None
        self.focused_object = None
        self.paused_tasks = []

    def begin_turn(self,user_message: UserMessage):
        self.pending_turn = Turn(
            turn_id=uuid.uuid4().hex,
            input_message=user_message,
        )

    def commit_pending_turn(self,bot_message):
        self.pending_turn.assistant_messages.extend(bot_message)
        self.get_current_session().turns.append(self.pending_turn)
        self.pending_turn = None

    def start_system_task(self, system_context: SystemContext):
        self.active_system_task = system_context

    def end_system_task(self):
        self.active_system_task = None

    def interrupt_active_task(self):
        # 将当前任务移入暂停列表
        self.paused_tasks.append(self.active_task)
        # 将当前任务设为 None
        self.active_task = None

    def start_task(self, task_context: TaskContext):
        self.active_task = task_context

    def cancel_active_task(self):
        self.active_task = None
        self.active_system_task = None

    def resume_task(self, flow_id: str):
        for task in self.paused_tasks:
            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                break

    def set_slots(self, slots: Dict[str, Any]):
        self.active_task.slots.update(slots)

    def get_current_task_context(self):
        return self.active_system_task or self.active_task

    def remove_slot(self, slot_name: str):
        self.active_task.slots.pop(slot_name)

    def end_task(self):
        self.active_task = None
