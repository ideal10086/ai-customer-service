from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, load_prompt

from atguigu.domain.message import BotMessage, UserMessage
from atguigu.domain.state import Turn
from atguigu.infrastructure.ai_clients import llm_client
from atguigu.knowledge.providers import KnowledgeChunk
from atguigu.prompts.history_builder import render_user_message, build_history



class KnowledgeResponder:
    async def respond(
        self,
        user_message: UserMessage,
        recent_turns: list[Turn],
        chunks: list[KnowledgeChunk],
    ) -> list[BotMessage]:
        # 获取用户消息
        user_message_content = render_user_message(user_message)
        # 处理历史记录
        history = build_history(recent_turns)
        # 处理KnowledgeChunk
        knowledge_content = "\n\n".join([chunk.content for chunk in chunks])
        # 调用LLM
        prompt_text = load_prompt("knowledge_respond")
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        output_parser = StrOutputParser()
        chain = prompt | llm_client | output_parser
        response = await chain.ainvoke({
            "knowledge_content": knowledge_content,
            "history": history,
            "user_message": user_message_content
        })
        # 返回messages
        return [BotMessage(text=response)]
