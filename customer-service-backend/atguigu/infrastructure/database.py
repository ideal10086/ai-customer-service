import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from atguigu.conf.config import settings

# 【全局变量】
# engine         - 异步数据库引擎，负责管理连接池和与数据库的通信
# session_factory - 异步会话工厂，用于创建数据库会话（事务单元）
engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


# 初始化数据库引擎和会话工厂
def init_db_engine() -> None:
    global engine, session_factory
    # 【create_async_engine 参数说明】
    # settings.database_url : 数据库连接 URL，如 postgresql+asyncpg://user:pass@host/db
    # echo=False            : 关闭 SQL 语句日志输出，生产环境减少噪音，调试时可设为 True
    # pool_pre_ping=True    : 每次从连接池取出连接前发送心跳查询（SELECT 1）检测连接是否存活，
    #                         若连接已断开则自动丢弃并创建新连接，避免"连接已失效"错误
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

    # 【async_sessionmaker 参数说明】
    # engine               : 绑定的异步数据库引擎，提供实际的数据库连接
    # expire_on_commit=False: 事务提交后 ORM 对象属性不过期，可直接访问无需触发懒加载查询，
    #                         减少意外的数据库请求
    session_factory = async_sessionmaker(engine, expire_on_commit=False)


# 关闭数据库引擎
async def close_db_engine():
    if engine is not None:
        await engine.dispose()


if __name__ == '__main__':
    # 测试数据库连接
    async def test():
        async with session_factory() as session:
            result = await session.execute(text("select 1"))
            print(result.fetchone())
        await close_db_engine()
    init_db_engine()
    asyncio.run(test())
