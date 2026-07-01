from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


def _issue_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "ISS-1001",
            "priority": "P0",
            "type": "export",
            "title": "Telegram ZIP validation failed",
            "stage": "export_validation",
            "reason": "Manifest is missing the 512px transparent PNG asset.",
            "message": "Regenerate the platform package before validation.",
            "recoverable": True,
            "actions": ["resolve", "cancel", "requeue"],
            "platform": "Telegram",
            "status": "open",
            "created_at": "2026-07-01T08:00:00Z",
            "updated_at": "2026-07-01T16:15:00Z",
        },
        {
            "id": "ISS-1002",
            "priority": "P1",
            "type": "qa",
            "title": "Sticker OCR readability is low",
            "stage": "qa_ocr",
            "reason": "Text edges are too soft in the mobile thumbnail.",
            "message": "Send it to QA review and regenerate the rejected frame.",
            "recoverable": True,
            "actions": ["resolve", "cancel", "requeue"],
            "platform": "WeChat",
            "status": "open",
            "created_at": "2026-07-01T07:30:00Z",
            "updated_at": "2026-07-01T15:44:00Z",
        },
    ]


def _failure_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "FAIL-2001",
            "task_id": "EXP-003",
            "task_name": "Summer rabbit package build",
            "stage": "package_build",
            "reason": "Animated WEBP frame count exceeds the platform rule.",
            "message": "Reduce frames and add the task back to the queue.",
            "recoverable": True,
            "actions": ["cancel", "requeue", "view_logs"],
            "created_at": "2026-07-01T13:10:00Z",
            "updated_at": "2026-07-01T16:02:00Z",
            "platform": "WhatsApp",
            "asset_count": 24,
            "status": "failed",
        },
        {
            "id": "FAIL-2002",
            "task_id": "PROMPT-009",
            "task_name": "Remote prompt optimization",
            "stage": "prompt_remote",
            "reason": "Free remote endpoint timed out and local fallback was used.",
            "message": "Retry remote optimization later if needed.",
            "recoverable": True,
            "actions": ["cancel", "requeue", "view_logs"],
            "created_at": "2026-07-01T12:40:00Z",
            "updated_at": "2026-07-01T15:21:00Z",
            "platform": "WeChat",
            "asset_count": 12,
            "status": "retrying",
        },
    ]


def _export_rows() -> list[dict[str, Any]]:
    rows = [
        ("EXP-001", "SET-12e19461c7cf", "Milk tea cat launch pack", "Telegram", "validating", 64, "validation", "pending validation", "01-ITEM-7de75396b177.png"),
        ("EXP-002", "SET-19c4236f8460", "Office panda meeting pack", "WeChat", "ready", 92, "ready", "ready", "02-ITEM-7e26a66fc740.png"),
        ("EXP-003", "SET-238e97b1f6d3", "Coffee rabbit work pack", "Telegram", "export_failed", 64, "upload", "Telegram manifest field is missing", "03-ITEM-1791c890a877.png"),
        ("EXP-004", "SET-5f0d7dfaff75", "Pixel fox review pack", "Telegram", "succeeded", 100, "published", "passed", "04-ITEM-1e2788bc5917.png"),
        ("EXP-005", "SET-72b36230c4aa", "Work dog LINE pack", "LINE", "queued", 0, "queued", "not generated", "05-ITEM-71f48419fbe0.png"),
        ("EXP-006", "SET-7338ad4e3413", "Cyber frog WeChat pack", "WeChat", "ready", 88, "ready", "ready", "06-ITEM-885515f98155.png"),
        ("EXP-007", "SET-12e19461c7cf", "Milk tea cat retry pack", "LINE", "validating", 51, "manifest", "manifest check running", "01-ITEM-7de75396b177.png"),
        ("EXP-008", "SET-19c4236f8460", "Panda resend pack", "Telegram", "ready", 90, "ready", "ready", "02-ITEM-7e26a66fc740.png"),
        ("EXP-009", "SET-238e97b1f6d3", "Coffee rabbit LINE pack", "LINE", "succeeded", 100, "published", "passed", "03-ITEM-1791c890a877.png"),
    ]
    result = []
    for index, (export_id, set_id, name, platform, status, progress, stage, validation, asset_name) in enumerate(rows, start=1):
        timestamp = f"2026-07-01T{7 + index:02d}:30:00Z"
        result.append(
            {
                "id": export_id,
                "pack_id": set_id,
                "pack_name": name,
                "platform": platform,
                "status": status,
                "progress": progress,
                "current_stage": stage,
                "validation_result": validation,
                "download_url": f"/admin-assets/{set_id}/{asset_name}",
                "file_manifest": ["manifest.json", "cover.png", f"{platform.lower()}-package.zip"],
                "created_at": timestamp,
                "updated_at": timestamp,
                "logs": [f"{timestamp} created", f"{timestamp} {stage}"],
            }
        )
    return result


def default_admin_state() -> dict[str, Any]:
    return {
        "issues": _issue_rows(),
        "failures": _failure_rows(),
        "exports": _export_rows(),
        "prompt_history": [],
    }


class AdminStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
        temp_path.replace(self.path)

    def update(self, mutator: Callable[[dict[str, Any]], Any]) -> Any:
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
            if isinstance(value, list) and value and isinstance(value[0], dict) and "id" in value[0]:
                existing_ids = {str(row.get("id")) for row in state.get(key, [])}
                for row in value:
                    if row["id"] not in existing_ids:
                        state[key].append(row)
                        changed = True
        return state, changed
