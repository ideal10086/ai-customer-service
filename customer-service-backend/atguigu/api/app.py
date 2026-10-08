"""
FastAPI 应用实例 & 生命周期管理

- 创建 FastAPI 应用实例
- 注册启动/关闭事件，初始化数据库引擎、HTTP 客户端
- 注册路由
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from atguigu.api.routers import router
from atguigu.infrastructure.database import init_db_engine, close_db_engine
from atguigu.infrastructure.http_util import close_http_client, init_http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== 启动阶段 =====
    init_db_engine()
    init_http_client()
    yield
    # ===== 关闭阶段 =====
    await close_http_client()
    await close_db_engine()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
