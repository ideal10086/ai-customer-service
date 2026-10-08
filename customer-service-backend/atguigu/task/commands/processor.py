from pathlib import Path

from atguigu.domain.contexts import CanceledSystemContext, StartedSystemContext, InterruptedSystemContext, \
    ResumedSystemContext
from atguigu.domain.state import DialogueState, TaskContext
from atguigu.task.commands.models import Command, StartFlowCommand, SetSlotsCommand, CancelFlowCommand, \
    ResumeFlowCommand
from atguigu.task.flow.models import FlowsList, Flow


class CommandProcessor:
    def run(self, commands: list[Command], state: DialogueState, flows: FlowsList) -> None:
        #遍历命令列表，执行每个命令
        for command in commands:
            self._apply(command, state, flows)

    def _apply(self, command, state, flows):
        # 根据命令类型执行相应的处理方法
        if isinstance(command, StartFlowCommand):
            # 启动流程
            self._handle_start_flow(command, state, flows)
        elif isinstance(command, SetSlotsCommand):
            # 设置槽值
            self._handle_set_slots(command, state)
        elif isinstance(command, CancelFlowCommand):
            # 取消流程
            self._handle_cancel_flow(state, flows)
        elif isinstance(command, ResumeFlowCommand):
            # 恢复流程
            self._handle_resume_flow(command, state, flows)

    def _handle_start_flow(self, command:StartFlowCommand, state:DialogueState, flows:FlowsList):
        # 1.如果有正在执行的系统任务，清理系统任务上下文
        state.end_system_task()
        # 2.获取要启动的目标flow
        #   从command中获取flow_id
        flow_id = command.flow
        #   根据flow_id获取目标flow对象
        flow:Flow = flows.get_flow_by_id(flow_id)
        # 3.判断是否有正在执行的task
        active_task = state.active_task
        if active_task:
        # 挂起旧任务
            state.interrupt_active_task()
        # 启动新任务
            state.start_task(TaskContext(
                    flow_id=flow_id,
                    step_id=flow.get_start_step().id,
                )
            )
            # 启动 system_task_interrupted系统Flow
            state.start_system_task(InterruptedSystemContext(
                flow_id = "system_task_interrupted",
                step_id = flows.get_flow_by_id("system_task_interrupted").get_start_step().id,
                interrupted_flow_id=active_task.flow_id,
                interrupted_flow_name=flows.get_flow_by_id(active_task.flow_id).name,
                started_flow_id=flow_id,
                started_flow_name=flow.name,
            ))
        else:
            # 启动新任务
            state.start_task(TaskContext(
                flow_id=flow_id,
                step_id=flow.get_start_step().id,
            ))
            # 启动 system_task_started系统Flow
            state.start_system_task(StartedSystemContext(
                flow_id="system_task_started",
                step_id=flows.get_flow_by_id("system_task_started").get_start_step().id,
                started_flow_id=flow_id,
                started_flow_name=flow.name
            ))

    def _handle_set_slots(self, command:SetSlotsCommand, state:DialogueState):
        # 1.读取command中的slots
        slots = command.slots
        # 2.如果有正在执行的任务，则设置到任务的槽位
        if state.active_task:
            state.set_slots(slots)

    def _handle_cancel_flow(self, state:DialogueState, flows:FlowsList):
        # 1.获取正在执行的任务
        active_task = state.active_task
        cancel_flow = flows.get_flow_by_id(active_task.flow_id)
        # 2.取消当前task
        state.cancel_active_task()
        # 3.启动system_task_canceled系统任务
        state.start_system_task(CanceledSystemContext(
            flow_id="system_task_canceled",
            step_id=flows.get_flow_by_id("system_task_canceled").get_start_step().id,
            canceled_flow_id=cancel_flow.id,
            canceled_flow_name=cancel_flow.name
        ))

    def _handle_resume_flow(self, command:ResumeFlowCommand, state:DialogueState, flows:FlowsList):
        #从command中获取flow_id
        target_flow:Flow = flows.get_flow_by_id(command.flow)
        # 2.获取正在执行的任务
        active_task = state.active_task
        # 3.判断是否有正在执行的任务
        if active_task is not None:
            # 3.1 当前有正在运行的任务
            if active_task.flow_id == target_flow.id:
                return
            else:
                state.interrupt_active_task()
                state.resume_task(target_flow.id)
                state.start_system_task(InterruptedSystemContext(
                    flow_id = "system_task_interrupted",
                    step_id=flows.get_flow_by_id("system_task_interrupted").get_start_step().id,
                    interrupted_flow_id=active_task.flow_id,
                    interrupted_flow_name=flows.get_flow_by_id(active_task.flow_id).name,
                    started_flow_id=active_task.flow_id,
                    started_flow_name=target_flow.name,
                ))
        else:
            state.start_system_task(ResumedSystemContext(
                flow_id="system_task_resumed",
                step_id=flows.get_flow_by_id("system_task_resumed").get_start_step().id,
                resumed_flow_id=target_flow.id,
                resumed_flow_name=target_flow.name
            ))
