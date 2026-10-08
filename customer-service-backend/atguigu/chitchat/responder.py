from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import load_prompt, PromptTemplate
from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import Turn
from atguigu.infrastructure.ai_clients import llm_client
from atguigu.prompts.history_builder import build_history, render_user_message


class ChitchatResponder:

    async def respond(
            self,
            user_message: UserMessage,
            recent_turns: list[Turn],
    ) -> list[BotMessage]:
        user_message = render_user_message(user_message)
        history = build_history(recent_turns)
        prompt_text = load_prompt("chitchat_respond")
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        chain = prompt | llm_client | StrOutputParser()
        response = await chain.ainvoke({
            "user_message": user_message,
            "history": history,
        })
        return [BotMessage(text=response)]
