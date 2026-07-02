from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any, Callable


def default_admin_state() -> dict[str, Any]:
    return {
        "issues": [],
        "failures": [],
        "exports": [],
        "prompt_history": [],
        "qa_records": [],
        "generation_tasks": [],
        "generated_stickers": [],
        "strategy_sources": [],
        "uploads": [],
        "character_dna": [],
        "sticker_plans": [],
        "caption_favorites": [],
        "render_jobs": [],
        "strategy_exports": [],
        "deleted_stickers": {},
        "deleted_packs": {},
        "qa_overrides": {},
        "generation_source": {
            "remote_prompt_optimizer_url": "",
            "enabled": False,
            "timeout_ms": 1200,
            "prompt_sources_enabled": True,
            "local_generator_enabled": True,
            "dynamic_generation_enabled": True,
            "non_flat_min_score": 80,
            "last_test_status": "not_configured",
            "last_test_time": "",
            "last_error_reason": "remote optimizer not configured; local prompt optimization only",
        },
        "platform_specs": {
            "wechat": {
                "sticker": "240x240",
                "banner": "750x400",
                "icon": "50x50",
                "transparent_png": True,
            },
            "zip": {"manifest_required": True},
        },
        "cleanroom": {
            "state": "reset",
            "production_assets_seeded": False,
            "demo_samples_allowed": False,
            "low_quality_fallback_allowed_as_official": False,
        },
    }


class AdminStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def load(self) -> dict[str, Any]:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                state = default_admin_state()
                self.save(state)
                return state
            with self.path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
            state, changed = self._merge_defaults(state)
            if changed:
                self.save(state)
            return state

    def save(self, state: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2)
            temp_path.replace(self.path)

    def update(self, mutator: Callable[[dict[str, Any]], Any]) -> Any:
        with self._lock:
            state = self.load()
            working = deepcopy(state)
            result = mutator(working)
            self.save(working)
            return result

    def _merge_defaults(self, state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        default = default_admin_state()
        changed = False
        for key, value in default.items():
            if key not in state:
                state[key] = value
                changed = True
                continue
            if isinstance(value, dict) and isinstance(state.get(key), dict):
                for nested_key, nested_value in value.items():
                    if nested_key not in state[key]:
                        state[key][nested_key] = nested_value
                        changed = True
        return state, changed
