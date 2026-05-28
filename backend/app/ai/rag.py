"""
Simple file-based RAG — reads context/ markdown files directly.
No vector database needed. Works on all Python versions.
For a demo with 5-6 small files, this is perfectly adequate.
"""
import os

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "context")

# Keywords that map to specific context files
FILE_KEYWORDS = {
    "business_rules.md": ["alert", "threshold", "kpi", "dwell", "battery", "shift", "resolve", "sop", "stale", "clearance", "sla", "escalat"],
    "facility_context.md": ["zone", "dock", "receiving", "shipping", "inspection", "storage", "assembly", "floor", "facility", "meridian", "asset", "category"],
    "system_reference.md": ["tag", "ble", "bluetooth", "rtls", "api", "event", "position", "signal", "pipeline", "endpoint", "tool", "sitetrack"],
}

_file_cache: dict[str, str] = {}


def _load_file(filename: str) -> str:
    if filename in _file_cache:
        return _file_cache[filename]
    path = os.path.join(CONTEXT_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    _file_cache[filename] = content
    return content


def retrieve(query: str, n_files: int = 3) -> str:
    """
    Return relevant context for a query by keyword matching against file topics.
    Returns up to n_files files worth of context, truncated to stay within token limits.
    """
    query_lower = query.lower()
    scored: list[tuple[int, str]] = []

    for filename, keywords in FILE_KEYWORDS.items():
        if filename == "GAMEPLAN.md":
            continue
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scored.append((score, filename))

    # Sort by relevance score, take top n_files
    scored.sort(reverse=True)
    top_files = [f for _, f in scored[:n_files]]

    # If nothing matched, include business_rules and facility_context as defaults
    if not top_files:
        top_files = ["business_rules.md", "facility_context.md"]

    parts = []
    for filename in top_files:
        content = _load_file(filename)
        if content:
            # Truncate each file to ~800 chars to avoid bloating the prompt
            truncated = content[:800] + ("…" if len(content) > 800 else "")
            parts.append(f"[From {filename}]\n{truncated}")

    return "\n\n".join(parts)


def reload():
    """Clear file cache so files are re-read on next retrieve()."""
    _file_cache.clear()
