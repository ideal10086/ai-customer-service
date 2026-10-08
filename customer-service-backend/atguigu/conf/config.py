from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Path(__file__) — 当前文件的路径（atguigu/conf/config.py）
# .resolve() — 转为绝对路径
# .parents[2] — 向上两级目录，到达项目根目录（cusomer_service_demo/）
# 最终指向 项目根目录下的 .env 文件
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_api_key: str
    llm_model: str
    llm_base_url: str

    # 数据库
    database_url: str

    # 商城 API
    commerce_api_base_url: str

    # 服务器
    app_host: str
    app_port: int

settings = Settings()

# 测试
if __name__ == '__main__':
    print(settings.llm_base_url)
