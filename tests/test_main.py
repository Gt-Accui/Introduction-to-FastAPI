"""
AttributeError: 'async_generator' object has no attribute 'post'
    https://zenn.dev/sh0nk/scraps/a981a1e100f62c#comment-f182253d10d867
    Must run like: `docker-compose run --entrypoint "poetry run pytest --asyncio-mode=auto" demo-app`
"""

import pytest
import starlette.status

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from api.db import get_db, Base
from api.main import app

ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_client() -> AsyncClient:
    async_engine = create_async_engine(ASYNC_DB_URL, echo=True)
    async_session = sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )

    # テスト用にオンメモリの SQLite テーブルを初期化
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # DI を使って FastAPI の DB の向き先をテスト用に変更
    async def get_test_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db

    # テスト用に非同期 HTTP クライアントを返却
    """
    DeprecationWarning: The 'app' shortcut is now deprecated. Use the explicit style 'transport=ASGITransport(app=...)' instead.
        https://www.python-httpx.org/advanced/transports/#example_1
    """
    # async with AsyncClient(app=app, base_url="http://test") as client:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_and_read(async_client):
    TEST_TASK_TITLE = "テストタスク for task"

    # create
    json = {"title": TEST_TASK_TITLE}
    response = await async_client.post("/tasks", json=json)
    assert response.status_code == starlette.status.HTTP_200_OK

    response_obj = response.json()
    assert response_obj["title"] == TEST_TASK_TITLE

    # read
    response = await async_client.get("/tasks")
    assert response.status_code == starlette.status.HTTP_200_OK

    response_obj = response.json()
    assert len(response_obj) == 1
    assert response_obj[0]["title"] == TEST_TASK_TITLE
    assert response_obj[0]["done"] is False


@pytest.mark.asyncio
async def test_done_flag(async_client):
    TEST_TASK_TITLE = "テストタスク for done"

    # create task
    json = {"title": TEST_TASK_TITLE}
    response = await async_client.post("/tasks", json=json)
    assert response.status_code == starlette.status.HTTP_200_OK

    response_obj = response.json()
    assert response_obj["title"] == TEST_TASK_TITLE

    # raise flag
    response = await async_client.put("/tasks/1/done")
    assert response.status_code == starlette.status.HTTP_200_OK

    # try raise flag is already up
    response = await async_client.put("/tasks/1/done")
    assert response.status_code == starlette.status.HTTP_400_BAD_REQUEST

    # remove flag is already up
    response = await async_client.delete("/tasks/1/done")
    assert response.status_code == starlette.status.HTTP_200_OK

    # try remove flag is not up
    response = await async_client.delete("/tasks/1/done")
    assert response.status_code == starlette.status.HTTP_404_NOT_FOUND
