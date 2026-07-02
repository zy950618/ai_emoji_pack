from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def admin_ok(data: Any, *, dev_mock: bool = False) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "request_id": f"req_{uuid4().hex}",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "dev_mock": dev_mock,
    }
    if isinstance(data, dict):
        for key in ("page", "page_size", "total"):
            if key in data:
                meta[key] = data[key]
    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": meta,
    }


def admin_error(
    *,
    code: str,
    message: str,
    stage: str,
    recoverable: bool,
    actions: list[str],
    dev_mock: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "stage": stage,
            "recoverable": recoverable,
            "actions": actions,
        },
        "meta": {
            "request_id": f"req_{uuid4().hex}",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "dev_mock": dev_mock,
        },
    }
