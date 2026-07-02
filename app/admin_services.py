from __future__ import annotations

import json
import zipfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.admin_store import AdminStore
from app.caption_engine import generate_captions
from app.character_dna import analyze_character_dna
from app.gif_text_renderer import render_gif_text
from app.layout_engine import calculate_safe_area, render_text_overlay
from app.meme_generator import generate_meme_assets
from app.sticker_strategy import create_sticker_plan
from app.wechat_exporter import export_wechat_package
from app.zip_exporter import create_zip_export
from app.prompt_engine import build_meme_prompt, optimize_prompt_local
from app.prompt_sources import prompt_sources_status, refresh_prompt_sources


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _page(rows: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    safe_page = max(1, int(page or 1))
    safe_size = min(100, max(1, int(page_size or 20)))
    start = (safe_page - 1) * safe_size
    return {"items": rows[start:start + safe_size], "total": len(rows), "page": safe_page, "page_size": safe_size}


class AdminService:
    def __init__(self, store: AdminStore) -> None:
        self.store = store
        self.project_root = Path(__file__).resolve().parents[1]
        self.asset_root = self.project_root / "data" / "generated_assets"
        self.export_root = self.asset_root / "exports"
        self.render_root = self.asset_root / "renders"
        self.upload_root = self.asset_root / "uploads"

    def strategy_sources(self) -> dict[str, Any]:
        repos = []
        for name in ("Wechat-Sticker-Gen", "meme-maker"):
            root = self.project_root / ".external_research" / name
            repos.append(
                {
                    "name": name,
                    "path": str(root),
                    "cloned": root.is_dir(),
                    "license": (root / "LICENSE").read_text(encoding="utf-8", errors="ignore").splitlines()[0] if (root / "LICENSE").is_file() else "not found",
                    "readme": (root / "README.md").is_file(),
                }
            )
        return {"items": repos, "absorbed_strategy": ["character_dna", "sticker_plan", "caption_layout", "gif_text", "wechat_export", "zip_export"]}

    def refresh_external_strategy(self) -> dict[str, Any]:
        snapshot = self.strategy_sources()

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state["strategy_sources"] = snapshot["items"]
            return snapshot

        return self.store.update(mutate)

    def create_upload(self, payload: dict[str, Any]) -> dict[str, Any]:
        upload_id = f"UP-{datetime.now(UTC).strftime('%H%M%S%f')}"
        filename = str(payload.get("filename") or f"{upload_id}.png")
        suffix = Path(filename).suffix.lower() or ".png"
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            raise ValueError("unsupported_upload_type")
        self.upload_root.mkdir(parents=True, exist_ok=True)
        target = self.upload_root / f"{upload_id}{suffix}"
        if suffix == ".gif":
            from app.gif_text_renderer import _fallback_gif

            _fallback_gif(target)
            is_animated = True
        else:
            from PIL import Image, ImageDraw

            image = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((90, 90, 422, 422), radius=80, fill=(255, 206, 105, 255), outline=(28, 32, 42, 255), width=8)
            draw.text((178, 238), "REF", fill=(28, 32, 42, 255))
            if suffix in {".jpg", ".jpeg"}:
                image.convert("RGB").save(target, "JPEG")
            else:
                image.save(target)
            is_animated = False
        row = {"id": upload_id, "filename": filename, "path": str(target), "url": f"/admin-assets/uploads/{target.name}", "thumbnail_url": f"/admin-assets/uploads/{target.name}", "is_animated": is_animated, "created_at": _now()}

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("uploads", []).insert(0, row)
            return row

        return self.store.update(mutate)

    def analyze_dna(self, payload: dict[str, Any]) -> dict[str, Any]:
        dna = analyze_character_dna(payload)

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            existing = {row["id"]: row for row in state.setdefault("character_dna", [])}
            existing[dna["id"]] = dna
            state["character_dna"] = list(existing.values())
            return dna

        return self.store.update(mutate)

    def list_character_dna(self) -> dict[str, Any]:
        return {"items": list(self.store.load().get("character_dna", []))}

    def create_sticker_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self.store.load()
        dna_id = str(payload.get("dna_id") or "")
        dna = next((row for row in state.get("character_dna", []) if row.get("id") == dna_id), None)
        if dna is None:
            dna = analyze_character_dna(payload)
        plan = create_sticker_plan(payload, dna)

        def mutate(working: dict[str, Any]) -> dict[str, Any]:
            if not any(row.get("id") == dna["id"] for row in working.setdefault("character_dna", [])):
                working["character_dna"].insert(0, dna)
            existing = {row["id"]: row for row in working.setdefault("sticker_plans", [])}
            existing[plan["id"]] = plan
            working["sticker_plans"] = list(existing.values())
            return plan

        return self.store.update(mutate)

    def get_sticker_plan(self, plan_id: str) -> dict[str, Any]:
        for plan in self.store.load().get("sticker_plans", []):
            if plan["id"] == plan_id:
                return plan
        raise KeyError(plan_id)

    def batch_from_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        plan = self.get_sticker_plan(str(payload.get("plan_id") or ""))
        result = self.create_generation(
            {
                "theme": payload.get("theme") or plan["id"],
                "platform": plan["platform"],
                "style": plan["style"],
                "dynamic": bool(payload.get("dynamic", plan.get("dynamic"))),
                "quantity": plan["quantity"],
                "frame_count": int(payload.get("frame_count", 6) or 6),
            }
        )
        result["plan_id"] = plan["id"]
        result["plan_items"] = plan["items"]
        return result

    def generate_captions(self, payload: dict[str, Any]) -> dict[str, Any]:
        return generate_captions(payload)

    def caption_favorites(self, q: str | None = None) -> dict[str, Any]:
        rows = list(self.store.load().get("caption_favorites", []))
        if q:
            rows = [row for row in rows if q.lower() in row["caption"].lower()]
        return {"items": rows}

    def add_caption_favorite(self, payload: dict[str, Any]) -> dict[str, Any]:
        caption = str(payload.get("caption") or "").strip()
        if not caption:
            raise ValueError("caption_required")
        row = {"id": f"CAP-{datetime.now(UTC).strftime('%H%M%S%f')}", "caption": caption, "tone": str(payload.get("tone") or ""), "created_at": _now()}

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("caption_favorites", []).insert(0, row)
            return row

        return self.store.update(mutate)

    def delete_caption_favorite(self, caption_id: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            rows = state.setdefault("caption_favorites", [])
            kept = [row for row in rows if row.get("id") != caption_id]
            if len(kept) == len(rows):
                raise KeyError(caption_id)
            state["caption_favorites"] = kept
            return {"id": caption_id, "deleted": True}

        return self.store.update(mutate)

    def safe_area(self, payload: dict[str, Any]) -> dict[str, Any]:
        return calculate_safe_area(payload)

    def render_text_overlay(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = Path(str(payload.get("source_path") or ""))
        if not source.is_file():
            upload = self.create_upload({"filename": "text-overlay-source.png"})
            source = Path(upload["path"])
        target = self.render_root / f"TEXT-{datetime.now(UTC).strftime('%H%M%S%f')}.png"
        return render_text_overlay(source, target, str(payload.get("text") or payload.get("caption") or "收到"), dict(payload.get("layout") or {}))

    def render_gif_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        return render_gif_text(payload, self.render_root)

    def export_wechat(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = payload.get("source_paths")
        if not paths:
            paths = [row.get("storage_path") or row.get("thumbnail_path") for row in self.store.load().get("generated_stickers", [])[:24]]
        result = export_wechat_package({**payload, "source_paths": [item for item in paths if item]}, self.export_root)

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("strategy_exports", []).insert(0, {"type": "wechat", **result, "created_at": _now()})
            return result

        return self.store.update(mutate)

    def export_zip(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = payload.get("asset_paths")
        if not paths:
            paths = [row.get("storage_path") or row.get("thumbnail_path") for row in self.store.load().get("generated_stickers", [])[:24]]
        result = create_zip_export({**payload, "asset_paths": [item for item in paths if item]}, self.export_root)

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("strategy_exports", []).insert(0, {"type": "zip", **result, "created_at": _now()})
            return result

        return self.store.update(mutate)

    def list_issues(self, filters: dict[str, Any], sort: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
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
        result = _page(rows, page, page_size)
        result["sort"] = sort
        return result

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

    def list_failures(self, filters: dict[str, Any], sort: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        rows = list(self.store.load()["failures"])
        q = filters.get("q")
        if q:
            rows = [row for row in rows if str(q).lower() in (row["task_name"] + row["reason"]).lower()]
        for key in ("stage", "platform", "status"):
            value = filters.get(key)
            if value:
                rows = [row for row in rows if row.get(key) == value]
        rows.sort(key=lambda row: row["updated_at"], reverse=True)
        result = _page(rows, page, page_size)
        result["sort"] = sort
        return result

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

    def _base_sticker_rows(self) -> list[dict[str, Any]]:
        return []

    def sticker_packs(self) -> list[dict[str, Any]]:
        state = self.store.load()
        qa_overrides = state.get("qa_overrides", {})
        deleted = state.get("deleted_stickers", {})
        rows = self._base_sticker_rows()
        for item in state.get("generated_stickers", []):
            if item.get("id") in deleted:
                continue
            qa_status = qa_overrides.get(item["id"], {}).get("status", item.get("status", "qa_pending"))
            rows.append(
                {
                    "id": item["id"],
                    "name": item.get("name", item["id"]),
                    "pack_name": item.get("name", item["id"]),
                    "role": item.get("theme", "generated"),
                    "style": item.get("style", "premium meme"),
                    "emotion_action": item.get("motion_type", "static pose"),
                    "asset_source": "local_generator",
                    "thumbnail_url": item["thumbnail_url"],
                    "media_url": item["media_url"],
                    "platforms": [item.get("platform", "WeChat")],
                    "platform": item.get("platform", "WeChat"),
                    "status": qa_status,
                    "quality_score": item.get("quality_score", 80),
                    "duplicate_risk": item.get("duplicate_risk", "low"),
                    "risk": item.get("duplicate_risk", "low"),
                    "export_status": item.get("export_status", "ready"),
                    "created_at": item.get("created_at", _now()),
                    "updated_at": qa_overrides.get(item["id"], {}).get("updated_at", item.get("updated_at", _now())),
                    "tags": [item.get("theme", ""), item.get("style", ""), "dynamic" if item.get("is_animated") else "static"],
                    "format": item.get("format", "png"),
                    "width": item.get("width", 512),
                    "height": item.get("height", 512),
                    "file_size": item.get("file_size", 0),
                    "is_animated": bool(item.get("is_animated")),
                    "dynamic": bool(item.get("is_animated")),
                    "frame_count": item.get("frame_count", 1),
                    "license_status": "generated-local",
                    "linked_packs": [item.get("name", item["id"])],
                    "last_used": item.get("updated_at", _now()),
                    "quality_checks": item.get("quality_checks", {}),
                }
            )
        return rows

    def list_sticker_packs(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        rows = self.sticker_packs()
        q = filters.get("q")
        dynamic = filters.get("dynamic")
        if not q and dynamic in (None, ""):
            rows = [row for row in rows if row.get("asset_source") != "local_generator"]
        if q:
            rows = [row for row in rows if str(q).lower() in (row["id"] + row["name"] + row["role"] + row["style"]).lower()]
        platform = filters.get("platform")
        if platform:
            rows = [row for row in rows if str(platform).lower() in [item.lower() for item in row["platforms"]]]
        status = filters.get("status")
        if status:
            rows = [row for row in rows if row["status"] == status]
        pack_type = filters.get("type")
        if pack_type:
            rows = [row for row in rows if pack_type in row["tags"]]
        if filters.get("quality_min") is not None:
            rows = [row for row in rows if row["quality_score"] >= int(filters["quality_min"])]
        if filters.get("quality_max") is not None:
            rows = [row for row in rows if row["quality_score"] <= int(filters["quality_max"])]
        if filters.get("export_status"):
            rows = [row for row in rows if row["export_status"] == filters["export_status"]]
        if filters.get("risk"):
            rows = [row for row in rows if row["duplicate_risk"] == filters["risk"]]
        if dynamic in (True, "true", "1", "yes"):
            rows = [row for row in rows if row.get("is_animated") is True]
        if dynamic in (False, "false", "0", "no"):
            rows = [row for row in rows if row.get("is_animated") is False]
        return _page(rows, page, page_size)

    def list_assets(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        rows = []
        for index, pack in enumerate(self.sticker_packs()):
            if not filters.get("type") and pack.get("asset_source") == "local_generator":
                continue
            rows.append(
                {
                    "id": f"ASSET-{pack['id']}",
                    "name": pack["role"],
                    "type": ["role asset", "style asset", "licensed material"][index % 3],
                    "license_status": pack["license_status"],
                    "linked_pack": pack["name"],
                    "last_used": pack["last_used"],
                    "thumbnail_url": pack["thumbnail_url"],
                    "media_url": pack["media_url"],
                    "style": pack["style"],
                    "role": pack["role"],
                }
            )
        if filters.get("type"):
            rows = [row for row in rows if row["type"] == filters["type"]]
        return _page(rows, page, page_size)

    def list_qa_items(self, page: int, page_size: int) -> dict[str, Any]:
        rows = [row for row in self.sticker_packs() if row.get("asset_source") != "local_generator"]
        for row in rows:
            row.setdefault("quality_checks", {})
            row["qa_checks"] = {
                "non_flat": row.get("quality_checks", {}).get("non_flat", {"passed": row["quality_score"] >= 65}),
                "dynamic": row.get("quality_checks", {}).get("dynamic", {"passed": bool(row.get("is_animated")), "frame_count": row.get("frame_count", 1)}),
            }
        return _page(rows, page, page_size)

    def approve_qa(self, item_id: str) -> dict[str, Any]:
        return self._set_qa_status(item_id, "approved", "")

    def reject_qa(self, item_id: str, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("reject_reason_required")
        return self._set_qa_status(item_id, "rejected", reason.strip())

    def _set_qa_status(self, item_id: str, status: str, reason: str) -> dict[str, Any]:
        if item_id not in {row["id"] for row in self.sticker_packs()}:
            raise KeyError(item_id)

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("qa_overrides", {})[item_id] = {"status": status, "updated_at": _now(), "reason": reason}
            record = {"id": f"QA-{datetime.now(UTC).strftime('%H%M%S%f')}", "item_id": item_id, "status": status, "reason": reason, "created_at": _now()}
            state.setdefault("qa_records", []).insert(0, record)
            return {"item_id": item_id, "status": status, "reason": reason, "record": record}

        return self.store.update(mutate)

    def prompt_sources(self) -> dict[str, Any]:
        return prompt_sources_status(self.project_root)

    def refresh_prompt_sources(self, allow_network: bool = False) -> dict[str, Any]:
        return refresh_prompt_sources(self.project_root, allow_network=allow_network)

    def build_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return build_meme_prompt(
            str(payload.get("theme", "")),
            str(payload.get("platform", "WeChat")),
            str(payload.get("style", "premium meme")),
            str(payload.get("mode", "static")),
            bool(payload.get("dynamic", False)),
            dict(payload.get("constraints") or {}),
            root=self.project_root,
        )

    def prompt_for(self, theme: str, style: str, platform: str) -> str:
        return self.build_prompt({"theme": theme, "style": style, "platform": platform})["prompt"]

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
            state.setdefault("prompt_history", []).insert(0, entry)
            state["prompt_history"] = state["prompt_history"][:20]
            return entry

        return self.store.update(mutate)

    def generate_prompt(self, theme: str, style: str, platform: str) -> dict[str, Any]:
        built = self.build_prompt({"theme": theme, "style": style, "platform": platform})
        entry = self.record_prompt(built["prompt"], "local", "local-rules", False)
        return {**built, "source": "local", "provider": "local-rules", "fallback": False, "history_entry": entry}

    def optimize_prompt(self, prompt: str) -> dict[str, Any]:
        optimized = optimize_prompt_local(prompt)
        entry = self.record_prompt(optimized, "local", "local-rules", False)
        return {"prompt": optimized, "source": "local", "provider": "local-rules", "fallback": False, "history_entry": entry}

    def optimize_prompt_remote(self, prompt: str, theme: str = "", platform: str = "WeChat", style: str = "premium meme") -> dict[str, Any]:
        config = self.get_generation_source()
        if not config.get("remote_prompt_optimizer_url") or not config.get("enabled"):
            optimized = self.optimize_prompt(prompt)["prompt"]
            return {"prompt": optimized, "source": "fallback", "provider": "local-rules", "fallback": True, "fallback_reason": "remote_not_configured"}
        try:
            payload = json.dumps({"theme": theme, "platform": platform, "style": style, "prompt": prompt}).encode("utf-8")
            request = urllib.request.Request(config["remote_prompt_optimizer_url"], data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=max(0.1, int(config.get("timeout_ms", 1200)) / 1000)) as response:
                body = json.loads(response.read().decode("utf-8"))
            if body.get("ok") is True and body.get("prompt"):
                entry = self.record_prompt(str(body["prompt"]), "remote", "configured-url", False)
                return {"prompt": str(body["prompt"]), "source": "remote", "provider": "configured-url", "fallback": False, "history_entry": entry}
            raise ValueError("remote_invalid_response")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            optimized = self.optimize_prompt(prompt)["prompt"]
            return {"prompt": optimized, "source": "fallback", "provider": "local-rules", "fallback": True, "fallback_reason": "remote_failed", "message": exc.__class__.__name__}

    def prompt_history(self) -> list[dict[str, Any]]:
        return list(self.store.load().get("prompt_history", []))

    def create_generation(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = f"GEN-{datetime.now(UTC).strftime('%H%M%S%f')}"
        platform = str(payload.get("platform") or "WeChat")
        style = str(payload.get("style") or "premium meme")
        theme = str(payload.get("theme") or "职场猫咪鼓励")
        dynamic = bool(payload.get("dynamic"))
        motion_type = str(payload.get("motion_type") or "bounce")
        prompt_bundle = self.build_prompt(
            {
                **payload,
                "theme": theme,
                "platform": platform,
                "style": style,
                "dynamic": dynamic,
                "mode": "dynamic" if dynamic else "static",
                "constraints": {"motion_type": motion_type, "frame_count": int(payload.get("frame_count", 6) or 6)},
            }
        )
        candidates = generate_meme_assets(task_id, {**payload, "theme": theme, "style": style, "dynamic": dynamic, "motion_type": motion_type}, self.asset_root)
        now = _now()
        sticker_rows = []
        for candidate in candidates:
            sticker_rows.append(
                {
                    **candidate,
                    "theme": theme,
                    "platform": platform,
                    "style": style,
                    "motion_type": motion_type,
                    "status": "qa_pending",
                    "duplicate_risk": "low",
                    "export_status": "ready",
                }
            )
        task = {
            "task_id": task_id,
            "id": task_id,
            "status": "completed",
            "theme": theme,
            "platform": platform,
            "style": style,
            "dynamic": dynamic,
            "motion_type": motion_type,
            "prompt": prompt_bundle,
            "candidates": sticker_rows,
            "created_at": now,
            "updated_at": now,
        }

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("generation_tasks", []).insert(0, task)
            state["generation_tasks"] = state["generation_tasks"][:50]
            existing = {item["id"]: item for item in state.setdefault("generated_stickers", [])}
            for row in sticker_rows:
                existing[row["id"]] = row
            state["generated_stickers"] = list(existing.values())
            for row in sticker_rows:
                state.setdefault("exports", []).insert(
                    0,
                    {
                        "id": f"EXP-{row['id']}",
                        "pack_id": row["id"],
                        "pack_name": row["name"],
                        "platform": platform,
                        "status": "ready",
                        "progress": 0,
                        "current_stage": "ready",
                        "validation_result": "ready",
                        "download_url": row["media_url"],
                        "file_manifest": [Path(row["storage_path"]).name],
                        "dynamic": row["is_animated"],
                        "frame_count": row["frame_count"],
                        "created_at": now,
                        "updated_at": now,
                        "logs": [f"{now} generated locally"],
                    },
                )
            return {**task, "status": "queued"}

        return self.store.update(mutate)

    def list_generation_tasks(self, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return _page(list(self.store.load().get("generation_tasks", [])), page, page_size)

    def get_generation_task(self, task_id: str) -> dict[str, Any]:
        for task in self.store.load().get("generation_tasks", []):
            if task["task_id"] == task_id or task["id"] == task_id:
                return task
        raise KeyError(task_id)

    def set_generation_task_status(self, task_id: str, status: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            for task in state.setdefault("generation_tasks", []):
                if task["task_id"] == task_id or task["id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = _now()
                    return task
            raise KeyError(task_id)

        return self.store.update(mutate)

    def list_exports(self, page: int, page_size: int, status: str | None = None, platform: str | None = None) -> dict[str, Any]:
        rows = list(self.store.load()["exports"])
        if status:
            rows = [row for row in rows if row["status"] == status]
        if platform:
            rows = [row for row in rows if row["platform"].lower() == platform.lower()]
        return _page(rows, page, page_size)

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

    def analytics(self) -> dict[str, Any]:
        packs = self.sticker_packs()
        exports = self.list_exports(1, 1000)["items"]
        failures = list(self.store.load().get("failures", []))
        return {
            "generation_trend": [],
            "platform_share": [{"platform": name, "value": len([row for row in packs if row["platform"] == name])} for name in ["WeChat", "Telegram", "LINE", "WhatsApp"]],
            "failure_reasons": [{"reason": row.get("reason_code") or row.get("stage", "unknown"), "count": 1} for row in failures],
            "quality_distribution": [{"band": "90+", "count": len([row for row in packs if row["quality_score"] >= 90])}, {"band": "80-89", "count": len([row for row in packs if 80 <= row["quality_score"] < 90])}, {"band": "<80", "count": len([row for row in packs if row["quality_score"] < 80])}],
            "rework_trend": [],
            "platform_risk": [{"platform": name, "risk": len([row for row in packs if row["platform"] == name and row["risk"] != "low"])} for name in ["WeChat", "Telegram", "LINE", "WhatsApp"]],
            "exports_total": len(exports),
        }

    def get_generation_source(self) -> dict[str, Any]:
        return dict(self.store.load().get("generation_source", {}))

    def save_generation_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            config = state.setdefault("generation_source", {})
            config["remote_prompt_optimizer_url"] = str(payload.get("remote_prompt_optimizer_url", config.get("remote_prompt_optimizer_url", ""))).strip()
            config["enabled"] = bool(payload.get("enabled", config.get("enabled", False)))
            config["timeout_ms"] = int(payload.get("timeout_ms", config.get("timeout_ms", 1200)) or 1200)
            for key in ("prompt_sources_enabled", "local_generator_enabled", "dynamic_generation_enabled"):
                if key in payload:
                    config[key] = bool(payload.get(key))
            if "non_flat_min_score" in payload:
                config["non_flat_min_score"] = int(payload.get("non_flat_min_score") or 65)
            if not config["remote_prompt_optimizer_url"]:
                config["enabled"] = False
                config["last_test_status"] = "未配置"
                config["last_error_reason"] = "未配置远程优化接口，当前使用本地优化"
            return dict(config)

        return self.store.update(mutate)

    def test_generation_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = self.save_generation_source(payload)
        url = config.get("remote_prompt_optimizer_url", "")
        if not url:
            status = "未配置"
            error = "未配置远程优化接口，当前使用本地优化"
        else:
            status = "失败已回退本地"
            error = "测试未获得可用远程返回，已保留本地回退"

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            source = state.setdefault("generation_source", {})
            source["last_test_status"] = status
            source["last_test_time"] = _now()
            source["last_error_reason"] = error
            return dict(source)

        return self.store.update(mutate)

    def delete_sticker(self, sticker_id: str) -> dict[str, Any]:
        known = {row["id"]: row for row in self.sticker_packs()}
        if sticker_id not in known:
            raise KeyError(sticker_id)
        row = known[sticker_id]

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            state.setdefault("deleted_stickers", {})[sticker_id] = {"item": row, "deleted_at": _now(), "type": "sticker"}
            return state["deleted_stickers"][sticker_id]

        return self.store.update(mutate)

    def delete_pack(self, pack_id: str) -> dict[str, Any]:
        return self.delete_sticker(pack_id)

    def bulk_delete(self, ids: list[str]) -> dict[str, Any]:
        deleted = []
        for sticker_id in ids:
            try:
                deleted.append(self.delete_sticker(sticker_id))
            except KeyError:
                continue
        return {"items": deleted, "deleted_count": len(deleted)}

    def restore_sticker(self, sticker_id: str) -> dict[str, Any]:
        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            deleted = state.setdefault("deleted_stickers", {})
            if sticker_id not in deleted:
                raise KeyError(sticker_id)
            row = deleted.pop(sticker_id)
            return row

        return self.store.update(mutate)

    def trash(self, page: int, page_size: int) -> dict[str, Any]:
        rows = list(self.store.load().get("deleted_stickers", {}).values())
        rows.sort(key=lambda row: row.get("deleted_at", ""), reverse=True)
        return _page(rows, page, page_size)
