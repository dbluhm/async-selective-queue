import asyncio
from typing import Callable, Generic, List, Optional, Sequence, TypeVar


QueueEntry = TypeVar("QueueEntry")
Select = Callable[[QueueEntry], bool]


class AsyncSelectiveQueue(Generic[QueueEntry]):
    """Asynchronous Queue implementation with selective retrieval of entries."""

    def __init__(self):
        self._queue: List[QueueEntry] = []
        self._cond: asyncio.Condition = asyncio.Condition()

    def _first_matching_index(self, select: Select):
        for index, entry in enumerate(self._queue):
            if select(entry):
                return index
        return None

    async def _get(self, select: Optional[Select] = None) -> QueueEntry:
        """Retrieve an entry from the queue."""
        while True:
            async with self._cond:
                # Lock acquired
                if not self._queue:
                    # No items on queue yet so we need to wait for items to show up
                    await self._cond.wait()

                if not self._queue:
                    # Another task grabbed the value before we got to it
                    continue

                if not select:
                    # Just get the first entry
                    return self._queue.pop(0)

                # Return first matching item, if present
                match_idx = self._first_matching_index(select)
                if match_idx is not None:
                    return self._queue.pop(match_idx)
                else:
                    # Queue is not empty but no matching elements
                    # We need to wait for more before checking again
                    # Otherwise, this becomes a busy loop
                    await self._cond.wait()

    async def get(
        self,
        select: Optional[Select] = None,
        *,
        timeout: int = 5,
    ) -> QueueEntry:
        """Retrieve a entry from the queue."""
        return await asyncio.wait_for(self._get(select), timeout)

    def get_all(self, select: Optional[Select] = None) -> Sequence[QueueEntry]:
        """Return all entries matching a given select."""
        entries = []
        if not self._queue:
            return entries

        if not select:
            entries = [entry for entry in self._queue]
            self._queue.clear()
            return entries

        # Store entries that didn't match in the order they are seen
        filtered: List[QueueEntry] = []
        for entry in self._queue:
            if select(entry):
                entries.append(entry)
            else:
                filtered.append(entry)

        # Queue contents set to entries that didn't match select
        self._queue[:] = filtered
        return entries

    def get_nowait(self, select: Optional[Select] = None) -> Optional[QueueEntry]:
        """Return a entry from the queue without waiting."""
        if not self._queue:
            return None

        if not select:
            return self._queue.pop(0)

        match_idx = self._first_matching_index(select)
        if match_idx is not None:
            return self._queue.pop(match_idx)

        return None

    async def put(self, value: QueueEntry):
        """Push a entry onto the queue and notify waiting tasks."""
        async with self._cond:
            self._queue.append(value)
            self._cond.notify_all()

    def flush(self) -> Sequence[QueueEntry]:
        """Clear queue and return final contents of queue at time of clear."""
        final = self._queue.copy()
        self._queue.clear()
        return final

    def empty(self) -> bool:
        """Return whether queue is empty."""
        return not bool(self._queue)
