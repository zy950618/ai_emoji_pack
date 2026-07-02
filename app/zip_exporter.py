from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def create_zip_export(payload: dict[str, Any], output_root: Path) -> dict[str, Any]:
    export_id = str(payload.get("export_id") or f"ZIP-{datetime.now(UTC).strftime('%H%M%S%f')}")
    export_dir = output_root / export_id
    export_dir.mkdir(parents=True, exist_ok=True)
    asset_paths = [Path(str(item)) for item in payload.get("asset_paths", []) if str(item)]
    copied = []
    for index, path in enumerate(asset_paths, start=1):
        if path.is_file():
            target = export_dir / f"asset_{index:02d}{path.suffix.lower()}"
            target.write_bytes(path.read_bytes())
            copied.append(target.name)
    manifest = {"export_id": export_id, "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"), "assets": copied, "count": len(copied)}
    report = {"passed": bool(copied), "asset_count": len(copied), "contains_manifest": True, "contains_report": True}
    (export_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (export_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = export_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(export_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(export_dir).as_posix())
    return {"export_id": export_id, "zip_path": str(zip_path), "download_url": f"/admin-assets/exports/{zip_path.name}", "manifest": manifest, "report": report}
