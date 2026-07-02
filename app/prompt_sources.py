from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROMPTS_CHAT_URL = "https://raw.githubusercontent.com/f/prompts.chat/main/prompts.csv"
SYSTEM_PROMPTS_REPO_URL = "https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools"


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def prompt_source_paths(root: Path) -> dict[str, Path]:
    return {
        "prompts_chat_cache": root / "data" / "prompt_sources" / "prompts_chat_cache.json",
        "prompts_chat_import_report": root / "data" / "prompt_sources" / "prompts_chat_import_report.json",
        "system_prompt_patterns": root / "data" / "prompt_sources" / "system_prompt_patterns.json",
        "meme_prompt_library": root / "data" / "prompt_library" / "meme_prompt_library.json",
    }


def _fallback_prompts_chat_cache(reason: str) -> dict[str, Any]:
    return {
        "source": "f/prompts.chat",
        "url": PROMPTS_CHAT_URL,
        "refreshed_at": _now(),
        "mode": "fallback-sanitized-patterns",
        "raw_source_exposed": False,
        "fallback_reason": reason,
        "patterns": [
            {"name": "role-task-output", "usage": "assign role, specify task, constrain output"},
            {"name": "context-examples-rules", "usage": "provide context, examples, hard rules"},
            {"name": "critique-refine", "usage": "ask for self-check and refined final answer"},
            {"name": "format-first", "usage": "separate content requirements from response format"},
        ],
    }


def _parse_prompts_chat_csv(text: str, limit: int = 40) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(text))
    categories: dict[str, int] = {}
    rows_seen = 0
    for row in reader:
        rows_seen += 1
        title = str(row.get("act") or row.get("title") or row.get("name") or "").lower()
        if any(token in title for token in ["artist", "designer", "story", "writer", "emoji", "social"]):
            key = "creative-design"
        elif any(token in title for token in ["critic", "review", "quality"]):
            key = "critique-quality"
        elif any(token in title for token in ["prompt", "generator"]):
            key = "prompt-building"
        else:
            key = "general-structure"
        categories[key] = categories.get(key, 0) + 1
        if rows_seen >= limit:
            break
    patterns = [{"name": key, "usage": f"observed {count} matching prompt structures"} for key, count in sorted(categories.items())]
    return {
        "source": "f/prompts.chat",
        "url": PROMPTS_CHAT_URL,
        "refreshed_at": _now(),
        "mode": "network-sanitized-patterns",
        "raw_source_exposed": False,
        "rows_sampled": rows_seen,
        "patterns": patterns,
    }


def refresh_prompt_sources(root: Path, allow_network: bool = True, timeout: float = 2.5) -> dict[str, Any]:
    paths = prompt_source_paths(root)
    errors: list[str] = []
    if allow_network:
        try:
            with urllib.request.urlopen(PROMPTS_CHAT_URL, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
            prompts_chat_cache = _parse_prompts_chat_csv(text)
        except (OSError, UnicodeError, urllib.error.URLError) as exc:
            errors.append(f"prompts.chat:{exc.__class__.__name__}")
            prompts_chat_cache = _fallback_prompts_chat_cache(exc.__class__.__name__)
    else:
        prompts_chat_cache = _fallback_prompts_chat_cache("network_disabled")

    system_patterns = {
        "source": "x1xhlol/system-prompts-and-models-of-ai-tools",
        "url": SYSTEM_PROMPTS_REPO_URL,
        "refreshed_at": _now(),
        "mode": "sanitized-architectural-patterns",
        "raw_source_exposed": False,
        "patterns": [
            {"name": "hard-boundaries", "usage": "state forbidden output and safety boundaries explicitly"},
            {"name": "tool-contract", "usage": "define exact required fields and fallback behavior"},
            {"name": "verification-loop", "usage": "require inspect, act, verify, and report evidence"},
            {"name": "state-machine", "usage": "make lifecycle states visible and recoverable"},
        ],
    }
    import_report = {
        "refreshed_at": _now(),
        "sources": [
            {"name": "prompts.chat", "url": "https://github.com/f/prompts.chat", "status": prompts_chat_cache["mode"]},
            {"name": "system prompt patterns", "url": SYSTEM_PROMPTS_REPO_URL, "status": "sanitized-patterns"},
        ],
        "raw_source_exposed": False,
        "errors": errors,
    }
    _write_json(paths["prompts_chat_cache"], prompts_chat_cache)
    _write_json(paths["system_prompt_patterns"], system_patterns)
    _write_json(paths["prompts_chat_import_report"], import_report)
    return {
        "items": [prompts_chat_cache, system_patterns],
        "report": import_report,
        "paths": {key: str(path) for key, path in paths.items()},
        "raw_source_exposed": False,
    }


def prompt_sources_status(root: Path) -> dict[str, Any]:
    paths = prompt_source_paths(root)
    if not paths["prompts_chat_cache"].exists() or not paths["system_prompt_patterns"].exists():
        refresh_prompt_sources(root, allow_network=False)
    items = [
        _read_json(paths["prompts_chat_cache"]) or _fallback_prompts_chat_cache("missing_cache"),
        _read_json(paths["system_prompt_patterns"]) or {},
    ]
    report = _read_json(paths["prompts_chat_import_report"]) or {"raw_source_exposed": False, "sources": []}
    return {
        "items": items,
        "report": report,
        "paths": {key: str(path) for key, path in paths.items()},
        "raw_source_exposed": False,
    }
