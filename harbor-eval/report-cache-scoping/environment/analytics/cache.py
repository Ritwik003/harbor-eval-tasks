"""A tiny in-process memoisation cache used by the reporting layer.

Reports are expensive to compute, so identical queries are served from here.
The hit/miss counters are read by the operations dashboard.
"""


class MemoCache:
    def __init__(self):
        self._store = {}
        self.hits = 0
        self.misses = 0

    def get_or_compute(self, key, compute):
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        value = compute()
        self._store[key] = value
        return value

    def clear(self):
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def size(self):
        return len(self._store)
