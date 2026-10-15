"""A stable minimum-priority queue backed by heapq."""

from heapq import heappop, heappush
from itertools import count
from math import isfinite
from typing import Generic, TypeVar

T = TypeVar("T")


class PriorityQueue(Generic[T]):
    def __init__(self) -> None:
        self._heap: list[tuple[float, int, T]] = []
        self._order = count()

    def push(self, item: T, priority: float) -> None:
        if not isfinite(priority):
            raise ValueError("Priority must be finite")
        heappush(self._heap, (priority, next(self._order), item))

    def pop(self) -> T:
        return heappop(self._heap)[2]

    def is_empty(self) -> bool:
        return not self._heap
