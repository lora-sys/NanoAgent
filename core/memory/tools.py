"""Memory tools — agent tools for memory operations."""

from core.memory.manager import get_memory_manager


def _get_mm():
    return get_memory_manager()


def register_memory_tools(registry) -> None:
    """Register memory tools with the tool registry."""

    def remember(key: str, value: str, mem_type: str = "long_term") -> dict:
        """
        Store information in long-term memory.
        Args:
            key: The key to store under
            value: The value to store
            mem_type: Memory type (long_term, working, short_term)
        """
        store = _get_mm().get_store(mem_type)
        if store is None:
            return {"status": "error", "message": f"Unknown memory type: {mem_type}"}
        store.set(key, value)
        return {
            "status": "ok",
            "stored": f"{mem_type}.{key}",
            "key": key,
            "value": value,
        }

    def recall(query: str, mem_type: str = "cross_session") -> dict:
        """
        Recall information from cross-session memory.
        Args:
            query: Search query or key to retrieve
            mem_type: Memory type to search (cross_session, long_term)
        """
        store = _get_mm().get_store(mem_type)
        if store is None:
            return {"status": "error", "message": f"Unknown memory type: {mem_type}"}

        # Clean up query - remove common prefixes
        clean_query = query
        if query.startswith("key="):
            clean_query = query[4:]
        elif query.startswith("query="):
            clean_query = query[6:]

        # Check if store has search capability
        if hasattr(store, "search_sessions"):
            results = store.search_sessions(clean_query, limit=5)
            return {"status": "ok", "results": results, "query": clean_query}
        elif hasattr(store, "find_related_context"):
            results = store.find_related_context(clean_query, limit=5)
            return {"status": "ok", "results": results, "query": clean_query}
        elif hasattr(store, "get"):
            val = store.get(clean_query)
            return {"status": "ok", "value": val, "query": clean_query}
        return {"status": "ok", "results": [], "query": clean_query}

    def forget(key: str, mem_type: str = "long_term") -> dict:
        """
        Remove information from memory.
        Args:
            key: The key to delete
            mem_type: Memory type (long_term, working, short_term, preference)
        """
        store = _get_mm().get_store(mem_type)
        if store is None:
            return {"status": "error", "message": f"Unknown memory type: {mem_type}"}
        store.delete(key)
        return {"status": "ok", "forgotten": f"{mem_type}.{key}", "key": key}

    def preference(action: str, key: str = "", value: str = "") -> dict:
        """
        Manage personal preferences: get/set/list.
        Args:
            action: 'get', 'set', or 'list'
            key: Preference key (for get/set)
            value: Preference value (for set)
        """
        store = _get_mm().get_store("preference")
        if store is None:
            return {"status": "error", "message": "Preference store not available"}

        if action == "get":
            val = store.get_preference(key)
            return {"status": "ok", "key": key, "value": val}
        elif action == "set":
            store.set_preference(key, value)
            return {"status": "ok", "set": f"{key}={value}", "key": key, "value": value}
        elif action == "list":
            all_prefs = store.get_all_preferences()
            return {"status": "ok", "preferences": all_prefs}
        return {
            "status": "error",
            "message": f"Invalid action: {action}. Use get/set/list.",
        }

    def memory_status() -> dict:
        """Get memory system status and statistics."""
        mm = _get_mm()
        stores = {}
        for name in [
            "short_term",
            "working",
            "long_term",
            "cross_session",
            "preference",
        ]:
            store = mm.get_store(name)
            if store:
                stores[name] = {
                    "memory_type": store.memory_type,
                    "stats": store.stats.__dict__
                    if hasattr(store.stats, "__dict__")
                    else {},
                }
        return {"status": "ok", "stores": stores, "budgets": mm.optimizer._budgets}

    registry.register("remember", remember, "Store information in long-term memory")
    registry.register("recall", recall, "Recall information from cross-session memory")
    registry.register("forget", forget, "Remove information from memory")
    registry.register(
        "preference", preference, "Manage personal preferences (get/set/list)"
    )
    registry.register("memory_status", memory_status, "Get memory system status")
