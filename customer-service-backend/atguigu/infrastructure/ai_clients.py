from langchain.chat_models import init_chat_model

from atguigu.conf.config import settings

llm_client = init_chat_model(
    model = settings.llm_model,
    model_provider="openai",
    base_url = settings.llm_base_url,
    api_key = settings.llm_api_key,
    temperature = 0
)

# 测试
if __name__ == '__main__':
    print(llm_client.invoke("你好").content)
