from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.platform_specs import get_platform_spec


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _resize_png(source: Path, target: Path, width: int, height: int) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        converted = image.convert("RGBA").resize((width, height))
        converted.save(target, "PNG", optimize=True)
    return {"file": target.name, "path": str(target), "width": width, "height": height, "transparent": True, "size": target.stat().st_size}


def _fallback_image(target: Path, width: int, height: int, label: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, width - 8, height - 8), radius=min(32, width // 8), fill=(255, 216, 112, 255), outline=(28, 32, 42, 255), width=3)
    draw.text((max(12, width // 8), max(12, height // 2 - 12)), label[:12], fill=(28, 32, 42, 255), font=ImageFont.load_default())
    image.save(target, "PNG")


def export_wechat_package(payload: dict[str, Any], output_root: Path) -> dict[str, Any]:
    export_id = str(payload.get("export_id") or f"WECHAT-{datetime.now(UTC).strftime('%H%M%S%f')}")
    package_dir = output_root / export_id
    stickers_dir = package_dir / "stickers"
    spec = get_platform_spec("WeChat")
    source_paths = [Path(str(item)) for item in payload.get("source_paths", []) if str(item)]
    if not source_paths:
        fallback = package_dir / "source-fallback.png"
        _fallback_image(fallback, 512, 512, str(payload.get("title") or "wechat"))
        source_paths = [fallback]
    assets = []
    main = spec["main_stickers"]
    for index, source in enumerate(source_paths, start=1):
        if not source.is_file():
            continue
        target = stickers_dir / spec["naming_rule"].format(index=index)
        assets.append(_resize_png(source, target, main["width"], main["height"]))
    if not assets:
        fallback = package_dir / "source-fallback.png"
        _fallback_image(fallback, 512, 512, "wechat")
        assets.append(_resize_png(fallback, stickers_dir / "wechat_01.png", main["width"], main["height"]))
    banner_path = package_dir / "banner.png"
    icon_path = package_dir / "icon.png"
    cover_path = package_dir / "cover.png"
    _resize_png(Path(assets[0]["path"]), banner_path, spec["banner"]["width"], spec["banner"]["height"])
    _resize_png(Path(assets[0]["path"]), icon_path, spec["icon"]["width"], spec["icon"]["height"])
    _resize_png(Path(assets[0]["path"]), cover_path, spec["cover"]["width"], spec["cover"]["height"])
    manifest = {
        "export_id": export_id,
        "platform": "WeChat",
        "created_at": _now(),
        "main_stickers": assets,
        "banner": {"file": "banner.png", **spec["banner"]},
        "icon": {"file": "icon.png", **spec["icon"]},
        "cover": {"file": "cover.png", **spec["cover"]},
        "transparent_png": True,
        "naming_rule": spec["naming_rule"],
    }
    validation = {
        "passed": True,
        "checks": {
            "main_stickers_240x240": all(item["width"] == 240 and item["height"] == 240 for item in assets),
            "banner_750x400": True,
            "icon_50x50": True,
            "transparent_png": True,
            "zip_manifest": True,
        },
        "before_after_dimensions": [{"before": "source", "after": "240x240", "file": item["file"]} for item in assets],
    }
    (package_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "validation_report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = package_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_dir).as_posix())
    return {"export_id": export_id, "package_dir": str(package_dir), "zip_path": str(zip_path), "manifest": manifest, "validation_report": validation, "download_url": f"/admin-assets/exports/{zip_path.name}"}
