from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.admin_store import AdminStore


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class AdminService:
    def __init__(self, store: AdminStore) -> None:
        self.store = store

    def list_issues(self, filters: dict[str, Any], sort: str) -> dict[str, Any]:
        rows = list(self.store.load()["issues"])
        q = filters.get("q")
        if q:
            rows = [row for row in rows if str(q).lower() in (row["title"] + row["reason"]).lower()]
        for key in ("priority", "type", "platform", "status"):
            value = filters.get(key)
            if value:
                rows = [row for row in rows if row.get(key) == value]
        rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        rows.sort(key=lambda row: (rank.get(row["priority"], 9), row["updated_at"]))
        return {"items": rows, "total": len(rows), "sort": sort}

    def set_issue_status(self, issue_id: str, status: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            for row in state["issues"]:
                if row["id"] == issue_id:
                    row["status"] = status
                    row["updated_at"] = _now()
                    row.setdefault("logs", []).append(f"status changed to {status}")
                    return row
            raise KeyError(issue_id)

        return self.store.update(mutate)

    def list_failures(self, filters: dict[str, Any], sort: str) -> dict[str, Any]:
        rows = list(self.store.load()["failures"])
        q = filters.get("q")
        if q:
            rows = [row for row in rows if str(q).lower() in (row["task_name"] + row["reason"]).lower()]
        for key in ("stage", "platform", "status"):
            value = filters.get(key)
            if value:
                rows = [row for row in rows if row.get(key) == value]
        rows.sort(key=lambda row: row["updated_at"], reverse=True)
        return {"items": rows, "total": len(rows), "sort": sort}

    def set_failure_status(self, failure_id: str, status: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            for row in state["failures"]:
                if row["id"] == failure_id:
                    row["status"] = status
                    row["updated_at"] = _now()
                    row.setdefault("logs", []).append(f"status changed to {status}")
                    return row
            raise KeyError(failure_id)

        return self.store.update(mutate)

    def sticker_packs(self) -> list[dict[str, Any]]:
        rows = [
            ("PACK-001", "Office cat meeting pack", "office-cat", "Telegram", "approved", 92, "low", "exported", "approved", False, "SET-12e19461c7cf/01-ITEM-7de75396b177.png"),
            ("PACK-002", "Summer rabbit drink pack", "summer-rabbit", "WeChat", "qa_pending", 86, "medium", "none", "approved", False, "SET-19c4236f8460/02-ITEM-7e26a66fc740.png"),
            ("PACK-003", "Forest bear weekend pack", "forest-bear", "LINE", "qa_pending", 78, "medium", "export_failed", "pending", False, "SET-238e97b1f6d3/03-ITEM-1791c890a877.png"),
            ("PACK-004", "Sleepy raccoon dynamic pack", "sleepy-raccoon", "WhatsApp", "approved", 89, "low", "exporting", "approved", True, "SET-5f0d7dfaff75/04-ITEM-1e2788bc5917.png"),
            ("PACK-005", "Fox retrospective pack", "fox-review", "Telegram", "rejected", 72, "high", "none", "review", False, "SET-72b36230c4aa/05-ITEM-71f48419fbe0.png"),
            ("PACK-006", "Sakura dog encouragement pack", "sakura-dog", "WeChat", "approved", 94, "low", "exported", "approved", False, "SET-7338ad4e3413/06-ITEM-885515f98155.png"),
        ]
        result = []
        for pack_id, name, tag, platform, status, quality, risk, export_status, license_status, animated, asset_path in rows:
            result.append(
                {
                    "id": pack_id,
                    "name": name,
                    "pack_name": name,
                    "thumbnail_url": f"/admin-assets/{asset_path}",
                    "media_url": f"/admin-assets/{asset_path}",
                    "platforms": [platform],
                    "status": status,
                    "quality_score": quality,
                    "duplicate_risk": risk,
                    "export_status": export_status,
                    "created_at": "2026-07-01T08:00:00Z",
                    "updated_at": "2026-07-01T09:00:00Z",
                    "tags": [tag],
                    "format": "webp" if animated else "png",
                    "width": 512,
                    "height": 512,
                    "file_size": 798720 if animated else 253952,
                    "is_animated": animated,
                    "license_status": license_status,
                }
            )
        return result

    def list_sticker_packs(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        rows = self.sticker_packs()
        q = filters.get("q")
        if q:
            rows = [row for row in rows if str(q).lower() in (row["name"] + row["pack_name"]).lower()]
        platform = filters.get("platform")
        if platform:
            rows = [row for row in rows if str(platform).lower() in [item.lower() for item in row["platforms"]]]
        status = filters.get("status")
        if status:
            rows = [row for row in rows if row["status"] == status]
        pack_type = filters.get("type")
        if pack_type:
            rows = [row for row in rows if pack_type in row["tags"]]
        quality_min = filters.get("quality_min")
        if quality_min is not None:
            rows = [row for row in rows if row["quality_score"] >= int(quality_min)]
        quality_max = filters.get("quality_max")
        if quality_max is not None:
            rows = [row for row in rows if row["quality_score"] <= int(quality_max)]
        export_status = filters.get("export_status")
        if export_status:
            rows = [row for row in rows if row["export_status"] == export_status]
        risk = filters.get("risk")
        if risk:
            rows = [row for row in rows if row["duplicate_risk"] == risk]
        start = max(page - 1, 0) * page_size
        return {"items": rows[start:start + page_size], "total": len(rows), "page": page, "page_size": page_size}

    def prompt_for(self, theme: str, style: str, platform: str) -> str:
        subject = theme.strip() or "sticker character"
        style_text = style.strip() or "funny daily-life, tactile, non-flat"
        platform_text = platform.strip() or "WeChat"
        return (
            f"{subject}; style: {style_text}; target platform: {platform_text}. "
            "Use a clear expressive character, tactile sticker material, layered foreground/midground/background, "
            "transparent-background friendly edges, readable short caption space, 1:1 mobile thumbnail composition. "
            "Avoid flat vector, generic corporate illustration, plain icon, text-only image, low detail, and empty white avatar."
        )

    def record_prompt(self, prompt: str, source: str, provider: str, fallback: bool, fallback_reason: str | None = None) -> dict[str, Any]:
        entry = {
            "id": f"PROMPT-{datetime.now(UTC).strftime('%H%M%S%f')}",
            "prompt": prompt,
            "source": source,
            "provider": provider,
            "fallback": fallback,
            "fallback_reason": fallback_reason,
            "created_at": _now(),
        }

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state["prompt_history"].insert(0, entry)
            state["prompt_history"] = state["prompt_history"][:20]
            return entry

        return self.store.update(mutate)

    def generate_prompt(self, theme: str, style: str, platform: str) -> dict[str, Any]:
        prompt = self.prompt_for(theme, style, platform)
        entry = self.record_prompt(prompt, "local", "local-rules", False)
        return {"prompt": prompt, "source": "local", "provider": "local-rules", "fallback": False, "history_entry": entry}

    def optimize_prompt(self, prompt: str) -> dict[str, Any]:
        optimized = (
            f"{prompt}\n\n"
            "Local optimization: add prop interaction, gaze direction, stronger emotion peak, platform size constraints, "
            "OCR-readable caption space, transparent background edges, and non-flat material detail."
        )
        entry = self.record_prompt(optimized, "local", "local-rules", False)
        return {"prompt": optimized, "source": "local", "provider": "local-rules", "fallback": False, "history_entry": entry}

    def optimize_prompt_remote(self, prompt: str) -> dict[str, Any]:
        optimized = (
            f"{prompt}\n\n"
            "Fallback optimization: remote free endpoint unavailable; preserved non-flat material, platform size, transparent background, "
            "caption readability, and sticker-pack consistency constraints."
        )
        entry = self.record_prompt(optimized, "fallback", "local-rules", True, "remote_timeout")
        return {
            "prompt": optimized,
            "source": "fallback",
            "provider": "local-rules",
            "fallback": True,
            "fallback_reason": "remote_timeout",
            "history_entry": entry,
        }

    def prompt_history(self) -> list[dict[str, Any]]:
        return list(self.store.load()["prompt_history"])

    def list_exports(self, page: int, page_size: int, status: str | None = None, platform: str | None = None) -> dict[str, Any]:
        rows = list(self.store.load()["exports"])
        if status:
            rows = [row for row in rows if row["status"] == status]
        if platform:
            rows = [row for row in rows if row["platform"].lower() == platform.lower()]
        start = max(page - 1, 0) * page_size
        return {"items": rows[start:start + page_size], "total": len(rows), "page": page, "page_size": page_size}

    def run_export(self, export_id: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            for row in state["exports"]:
                if row["id"] == export_id:
                    row["status"] = "succeeded"
                    row["progress"] = 100
                    row["current_stage"] = "completed"
                    row["validation_result"] = "passed"
                    row["updated_at"] = _now()
                    row.setdefault("logs", []).append(f"{_now()} single export succeeded")
                    return row
            raise KeyError(export_id)

        return self.store.update(mutate)

    def batch_export(self, export_ids: list[str]) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            changed = []
            target_ids = set(export_ids)
            for row in state["exports"]:
                if row["id"] in target_ids:
                    row["status"] = "exporting"
                    row["progress"] = max(int(row.get("progress", 0)), 10)
                    row["current_stage"] = "exporting"
                    row["updated_at"] = _now()
                    row.setdefault("logs", []).append(f"{_now()} batch export queued")
                    changed.append(row)
            return {"items": changed, "status": "exporting"}

        return self.store.update(mutate)
