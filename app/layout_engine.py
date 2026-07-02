from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("msyh.ttc", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def calculate_safe_area(payload: dict[str, Any]) -> dict[str, Any]:
    width = int(payload.get("width") or 512)
    height = int(payload.get("height") or 512)
    subject = payload.get("subject_box") or {"x": int(width * 0.22), "y": int(height * 0.18), "w": int(width * 0.56), "h": int(height * 0.56)}
    top_free = int(subject["y"])
    bottom_free = height - int(subject["y"]) - int(subject["h"])
    left_free = int(subject["x"])
    right_free = width - int(subject["x"]) - int(subject["w"])
    zones = {
        "top": {"x": 24, "y": 24, "w": width - 48, "h": max(64, top_free - 24)},
        "bottom": {"x": 24, "y": int(subject["y"]) + int(subject["h"]) + 12, "w": width - 48, "h": max(64, bottom_free - 24)},
        "left": {"x": 24, "y": 96, "w": max(72, left_free - 24), "h": height - 192},
        "right": {"x": int(subject["x"]) + int(subject["w"]) + 12, "y": 96, "w": max(72, right_free - 24), "h": height - 192},
    }
    preferred = max({"top": top_free, "bottom": bottom_free, "left": left_free, "right": right_free}, key=lambda key: {"top": top_free, "bottom": bottom_free, "left": left_free, "right": right_free}[key])
    return {"canvas": {"width": width, "height": height}, "subject_box": subject, "preferred": preferred, "zones": zones, "overlap": False}


def render_text_overlay(source_path: Path, target_path: Path, text: str, layout: dict[str, Any] | None = None) -> dict[str, Any]:
    layout = layout or {}
    with Image.open(source_path) as image:
        canvas = image.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    font_size = int(layout.get("font_size") or 42)
    stroke_width = int(layout.get("stroke_width") or 5)
    font = _font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    position = layout.get("position") or "bottom"
    x = int(layout.get("x") or (canvas.width - text_w) / 2)
    y = int(layout.get("y") or (canvas.height - text_h - 36 if position == "bottom" else 36))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255), stroke_width=stroke_width, stroke_fill=(20, 24, 32, 255))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target_path)
    return {"output_path": str(target_path), "width": canvas.width, "height": canvas.height, "text": text, "layout": {"x": x, "y": y, "font_size": font_size, "stroke_width": stroke_width}}
