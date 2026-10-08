from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.runner import ActionRunner
from atguigu.task.commands.models import Command
from atguigu.task.commands.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.models import FlowsList


class TaskHandler:
    def __init__(self,command_processor:CommandProcessor,flow_executor:FlowExecutor,action_runner:ActionRunner,flowers:FlowsList):
        self.command_processor = command_processor
        self.flow_executor = flow_executor
        self.action_runner = action_runner
        self.flowers = flowers

    async def handle(self,commands: list[Command],state:DialogueState) -> list[BotMessage]:
        self.command_processor.run(commands,state,self.flowers)
        messages:list[BotMessage] = await self.flow_executor.run_task(state,self.flowers,self.action_runner)
        return messages
