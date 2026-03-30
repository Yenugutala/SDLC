"""
In-memory session cache for LLM query results.

Why caching matters here:
    Each query to the LLM costs an API call (~200–500ms + token cost).
    In interactive sessions (scripts/interactive_query.py), users often re-ask
    similar questions or rephrase the same intent. The cache intercepts these
    and returns instantly without hitting the LLM again.

Cache key design:
    Keys are normalised (lowercase, whitespace-collapsed, punctuation-stripped)
    so "What pipelines exist?" and "what pipelines exist" map to the same entry.
    A prefix parameter ("query" / "reasoning") separates the two query modes
    since they return different response formats.

Scope:
    Session-scoped — lives for the lifetime of the NaturalLanguageQueryEngine
    instance. Not persisted to disk. Safe to ignore TTL because the KG data
    does not change mid-session.
"""

import re
from typing import Any, Dict, Optional


class QueryCache:
    """
    Thread-unsafe in-memory cache suitable for single-threaded CLI sessions.

    Usage:
        cache = QueryCache()
        result = cache.get(query, prefix="query")
        if result is None:
            result = expensive_llm_call()
            cache.set(query, result, prefix="query")
    """

    def __init__(self):
        # Plain dict — O(1) lookup, no eviction needed for session-scale usage
        self._store: Dict[str, Any] = {}

    def _key(self, query: str, prefix: str = "") -> str:
        """
        Produce a stable, normalised cache key.

        Normalisation steps:
            1. Lowercase — "Pipelines" and "pipelines" should hit the same entry
            2. Collapse whitespace — extra spaces / tabs are irrelevant
            3. Strip punctuation — trailing "?" or "." should not create distinct keys
            4. Prepend prefix — keeps "query:" and "reasoning:" namespaces separate
        """
        normalised = re.sub(r'\s+', ' ', query.lower().strip())
        normalised = re.sub(r'[^\w\s]', '', normalised)
        return f"{prefix}:{normalised}" if prefix else normalised

    def get(self, query: str, prefix: str = "") -> Optional[Any]:
        """Return cached result or None if not found."""
        return self._store.get(self._key(query, prefix))

    def set(self, query: str, result: Any, prefix: str = "") -> None:
        """Store a result under the normalised query key."""
        self._store[self._key(query, prefix)] = result

    def clear(self) -> None:
        """Wipe all cached entries (e.g. after reloading KG data)."""
        self._store.clear()

    def size(self) -> int:
        """Return number of cached entries across all prefixes."""
        return len(self._store)
