from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.engine.builder import build_dialogue_engine
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.infrastructure import database
from atguigu.repository.dialogue_repository import DialogueStateRepository
from atguigu.service.dialogue_service import DialogueService

_dialogue_engine: DialogueEngine | None = None


def get_engine() -> DialogueEngine:
    global _dialogue_engine
    if _dialogue_engine is None:
        _dialogue_engine = build_dialogue_engine()
    return _dialogue_engine


async def get_db():
    async with database.session_factory() as session:
        yield session


async def get_repository(db: AsyncSession = Depends(get_db),) -> DialogueStateRepository:
    return DialogueStateRepository(db)


async def get_dialogue_service(
        engine: DialogueEngine = Depends(get_engine),
        repository: DialogueStateRepository = Depends(get_repository),
) -> DialogueService:
    return DialogueService(dialogue_state_repository=repository, dialogue_engine=engine)
