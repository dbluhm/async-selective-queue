import asyncio
from typing import Callable
import pytest

from async_selective_queue import AsyncSelectiveQueue as Queue


@pytest.fixture
def queue():
    yield Queue()


@pytest.fixture
def create_task(event_loop: asyncio.AbstractEventLoop):
    def _create_task(coro):
        return asyncio.ensure_future(coro, loop=event_loop)

    return _create_task


@pytest.mark.asyncio
async def test_multiple_consumers(queue: Queue[int], create_task: Callable):
    async def consume():
        await queue.get()

    async def produce(timeout: float = 0.0):
        await asyncio.sleep(timeout)
        await queue.put(0)

    tasks = []
    for _ in range(3):
        tasks.append(create_task(consume()))
    for i in range(3):
        tasks.append(create_task(produce(0.25 + i * 0.25)))

    await asyncio.gather(*tasks)
    assert queue.empty()


@pytest.mark.asyncio
async def test_condition_value_present_no_match(queue: Queue[int], create_task: Callable):
    await queue.put(0)

    async def consume():
        await queue.get(lambda value: value != 0)

    async def produce():
        await asyncio.sleep(1)
        await queue.put(1)

    tasks = (create_task(consume()), create_task(produce()))
    await asyncio.gather(*tasks)
    assert queue.flush() == [0]
    assert queue.empty()


@pytest.mark.asyncio
async def test_condition_value_not_initially_present(
    queue: Queue[int], create_task: Callable
):
    for i in range(3):
        await queue.put(i)

    async def consume():
        await queue.get(lambda value: value == 3)

    async def produce():
        await asyncio.sleep(1)
        await queue.put(3)

    tasks = (create_task(consume()), create_task(produce()))
    await asyncio.gather(*tasks)
    assert queue.flush() == [0, 1, 2]
    assert queue.empty()


@pytest.mark.asyncio
async def test_out_of_order_retrieval(queue: Queue[int]):
    for i in range(3):
        await queue.put(i)

    await queue.get(lambda value: value == 1)
    await queue.get(lambda value: value == 2)
    await queue.get(lambda value: value == 0)
    assert queue.empty()


@pytest.mark.asyncio
async def test_get_all(queue: Queue[int]):
    for i in range(3):
        await queue.put(i)

    assert queue.get_all() == [0, 1, 2]
    assert queue.get_all() == []
    assert queue.empty()


@pytest.mark.asyncio
async def test_get_all_select(queue: Queue[int]):
    for i in range(3):
        await queue.put(i)

    assert queue.get_all(lambda value: value == 1) == [1]
    assert queue.get_all() == [0, 2]
    assert queue.empty()


@pytest.mark.asyncio
async def test_get_nowait(queue: Queue[int]):
    assert queue.get_nowait() is None

    for i in range(4):
        await queue.put(i)

    assert queue.get_nowait() == 0
    assert queue.get_nowait(lambda value: value == 10) is None
    assert queue.get_nowait(lambda value: value == 3) == 3
    assert queue.get_nowait(lambda value: value == 1) == 1
    assert queue.get_nowait(lambda value: value == 2) == 2
    assert queue.empty()


@pytest.mark.asyncio
async def test_flush(queue: Queue[int]):
    for i in range(3):
        await queue.put(i)

    assert queue.flush() == [0, 1, 2]
    assert queue.empty()
