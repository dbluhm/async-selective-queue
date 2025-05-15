# Async Selective Queue

[![PyPI](https://img.shields.io/pypi/v/async-selective-queue)](https://pypi.org/project/async-selective-queue/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/async-selective-queue)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/dbluhm/async-selective-queue/tests.yml?branch=main&label=tests)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Python library for an asynchronous queue with the ability to selectively
retrieve elements from the queue.

## Overview

`AsyncSelectiveQueue` lets you enqueue items and have consumers wait for—and optionally filter—specific items—without dropping everything else. Unmatched items remain in the queue until explicitly retrieved or flushed. Ideal for noisy event buses and test harnesses where you only care about a subset of events but still want to inspect or clear the rest later.


## Installation

```sh
pip install async-selective-queue
```

## Usage

```python
import asyncio
from async_selective_queue import AsyncSelectiveQueue

async def producer(q: AsyncSelectiveQueue[str]):
    for e in ["foo", "bar", "baz", "qux"]:
        await q.put(e)

async def test_consumer(q: AsyncSelectiveQueue[str]):
    # Only care about events containing "a"
    matches = await q.get_all(select=lambda s: "a" in s)
    print("Matched:", matches)
    # Non‑matching items ("foo", "qux") remain in queue
    print("Still queued:", q.flush())
````

## API Reference

### `await put(value: T) -> None`

Enqueue and notify waiters.

### `await get(select: Optional[Callable[[T], bool]] = None, *, timeout: float = 5) -> T`

* Removes and returns the first matching item (or oldest if no `select`).
* Waits up to `timeout` seconds, then raises `asyncio.TimeoutError`.
* Non‑matching items are untouched.

### `get_nowait(select: Optional[Callable[[T], bool]] = None) -> Optional[T]`

* Non‑blocking version of `get`.
* Returns a matching item or `None`.
* Everything else stays in queue.

### `get_all(select: Optional[Callable[[T], bool]] = None) -> List[T]`

* Atomically removes all matching items and returns them.
* If `select` is `None`, drains entire queue.
* Non‑matching items remain in their original order for later retrieval or inspection.

### `flush() -> List[T]`

* Clears queue and returns all items present at time of call.

### `empty() -> bool`

* Returns `True` if no items are queued.

## Concurrency & Nuances

* Uses `asyncio.Condition` to avoid busy‑waiting.
* Selective retrieval wakes only when matching items arrive—others stay queued.
* Useful for:
  * **Noisy event buses**: pull only relevant events.
  * **Testing**: assert on a subset of actions, then inspect or flush the rest.
* Cancelling a pending `get` leaves the queue unchanged.
* FIFO ordering for non‑selective operations; relative order preserved for `get_all`.
