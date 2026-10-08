from typing import Any
from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.ai_clients import llm_client
from atguigu.prompts.history_builder import build_history, render_user_message
from atguigu.task.action.base import Action, ActionResult


class ActionResponse(Action):
    name = "action_response"

    async def run(self,state: DialogueState,action_kwargs: dict[str, Any],) -> ActionResult:
        mode = action_kwargs.get("mode","static")
        if mode == "static":
            text = action_kwargs.get("text")
            render_text = self._render_text(text,state)
            return ActionResult(
                messages = [BotMessage(text=render_text)]
            )

        elif mode == "response":
            text = action_kwargs.get("text")
            render_text = self._render_text(text,state)
            prompt = action_kwargs.get("prompt")
            #调用llm对text进行优化
            rephrase_text = await self._call_llm(prompt = prompt,state = state,render_text= render_text)
            return ActionResult(
                messages = [BotMessage(text=rephrase_text)]
            )
        elif mode == "generate":
            prompt = action_kwargs.get("prompt")
            generate_text = await self._call_llm(prompt=prompt,state=state)
            return ActionResult(
                messages = [BotMessage(text=generate_text)]
            )
        else:
            return ActionResult()
    def _render_text(self, text:str, state: DialogueState) -> str:
        template = Template(text)
        return template.render(
            slots = state.active_task.slots,
            context = state.active_system_task or state.active_task
        )

    async def _call_llm(self, prompt:str, state:DialogueState, render_text:str="") -> str:
        prompt = PromptTemplate.format_prompt(
            prompt=prompt,
            template_format="jinja2"
        )
        chain = prompt | llm_client | StrOutputParser()
        result = await chain.invoke(
            {
                "history":build_history(state.get_current_session().turns),
                "user_message":render_user_message(state.pending_turn.input_message),
                "current_response":render_text
            }
        )
        return result
