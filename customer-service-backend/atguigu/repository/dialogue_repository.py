# atguigu\repository\dialogue_repository.py
import asyncio
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from atguigu.domain.state import DialogueState
from atguigu.infrastructure import database
from atguigu.models.dialogue_state import DialogueStateRecord


class DialogueStateRepository:
    def __init__(self,session:AsyncSession):
        self._session = session


    async def load(self, sender_id:str)->DialogueState:
        result = await self._session.execute(
            select(DialogueStateRecord).where(DialogueStateRecord.sender_id == sender_id)
        )
        # 获取查询记录
        record = result.scalar_one_or_none()
        if record is None:
            return DialogueState(sender_id=sender_id)
        # 将查询记录转换为DialogueState对象（记录-->json-->实例）
        return DialogueState.from_dict(json.loads(record.state_json))

    async def save(self, state: DialogueState) -> None:
        result = await self._session.execute(
            select(DialogueStateRecord).where(DialogueStateRecord.sender_id == state.sender_id)
        )
        record = result.scalar_one_or_none()
        # to_dict：将对象转换为字典结构
        state_json = json.dumps(state.to_dict(), ensure_ascii=False)
        if record is None:
            self._session.add(DialogueStateRecord(
                sender_id=state.sender_id,
                state_json=state_json
            ))
        else:
            record.state_json = state_json
        await self._session.commit()

if __name__ == "__main__":
    database.init_db_engine()

    # async def test():
    #     async with database.session_factory() as session:
    #         repo = DialogueStateRepository(session)
    #         record = await repo.load("u1001")
    #         print("查询结果:", record)

    async def test():
        async with database.session_factory() as session:
            repo = DialogueStateRepository(session)
            record = await repo.load("u1001")
            record.sender_id = "u1003"
            await repo.save(record)
        await database.close_db_engine()

    asyncio.run(test())
