from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.quality_checks import check_dynamic_asset, check_non_flat_asset, check_sticker_readability


def _safe_slug(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return digest


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("msyh.ttc", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_sticker(theme: str, style: str, frame: int, frames: int, dynamic: bool) -> Image.Image:
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    t = frame / max(1, frames - 1)
    bounce = int(math.sin(t * math.pi * 2) * 18) if dynamic else 0
    wobble = int(math.sin(t * math.pi * 4) * 10) if dynamic else 0
    draw_shadow.ellipse((126 + wobble, 380, 388 + wobble, 430), fill=(30, 35, 45, 55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    image.alpha_composite(shadow)
    draw = ImageDraw.Draw(image)
    palette = [
        (255, 205, 88), (255, 126, 126), (89, 174, 255), (90, 211, 132), (168, 124, 255)
    ]
    accent = palette[int(hashlib.sha1((theme + style).encode("utf-8")).hexdigest(), 16) % len(palette)]
    body_box = (138 + wobble, 110 - bounce, 374 + wobble, 360 - bounce)
    draw.ellipse(body_box, fill=accent + (255,), outline=(70, 50, 40, 255), width=9)
    draw.ellipse((176 + wobble, 74 - bounce, 236 + wobble, 150 - bounce), fill=(255, 236, 166, 255), outline=(70, 50, 40, 255), width=7)
    draw.ellipse((276 + wobble, 74 - bounce, 336 + wobble, 150 - bounce), fill=(255, 236, 166, 255), outline=(70, 50, 40, 255), width=7)
    draw.ellipse((188 + wobble, 190 - bounce, 220 + wobble, 228 - bounce), fill=(30, 30, 35, 255))
    draw.ellipse((292 + wobble, 190 - bounce, 324 + wobble, 228 - bounce), fill=(30, 30, 35, 255))
    draw.ellipse((197 + wobble, 198 - bounce, 207 + wobble, 208 - bounce), fill=(255, 255, 255, 235))
    draw.ellipse((301 + wobble, 198 - bounce, 311 + wobble, 208 - bounce), fill=(255, 255, 255, 235))
    draw.rounded_rectangle((218 + wobble, 258 - bounce, 294 + wobble, 294 - bounce), radius=18, fill=(120, 46, 58, 255))
    draw.arc((214 + wobble, 242 - bounce, 298 + wobble, 318 - bounce), start=10, end=170, fill=(50, 35, 35, 255), width=6)
    draw.rounded_rectangle((318 + wobble, 308 - bounce, 430 + wobble, 362 - bounce), radius=20, fill=(255, 255, 255, 238), outline=(68, 68, 72, 255), width=5)
    draw.text((340 + wobble, 321 - bounce), "OK", font=_font(26), fill=(40, 40, 50, 255))
    for i in range(10):
        angle = i * math.pi * 2 / 10 + t * math.pi
        cx = 256 + int(math.cos(angle) * (168 + i % 3 * 7))
        cy = 238 + int(math.sin(angle) * (156 + i % 2 * 8)) - bounce // 2
        color = (255, 255 - i * 8, 120 + i * 8, 210)
        draw.polygon([(cx, cy - 10), (cx + 5, cy), (cx, cy + 10), (cx - 5, cy)], fill=color)
    label = (theme.strip() or "加油")[:6]
    text_font = _font(34)
    box = draw.textbbox((0, 0), label, font=text_font)
    text_w = box[2] - box[0]
    draw.rounded_rectangle((256 - text_w // 2 - 24, 398, 256 + text_w // 2 + 24, 452), radius=20, fill=(255, 255, 255, 238), outline=(45, 45, 50, 255), width=5)
    draw.text((256 - text_w // 2, 407), label, font=text_font, fill=(30, 34, 45, 255))
    highlight = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)
    hdraw.ellipse((178 + wobble, 130 - bounce, 278 + wobble, 206 - bounce), fill=(255, 255, 255, 58))
    image.alpha_composite(highlight.filter(ImageFilter.GaussianBlur(8)))
    return image


def generate_meme_assets(task_id: str, payload: dict[str, Any], output_root: Path) -> list[dict[str, Any]]:
    output_dir = output_root / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    theme = str(payload.get("theme") or "职场猫咪鼓励")
    style = str(payload.get("style") or "premium meme")
    dynamic = bool(payload.get("dynamic"))
    frame_count = max(4, int(payload.get("frame_count", 6) or 6)) if dynamic else 1
    candidates: list[dict[str, Any]] = []
    count = max(1, min(24, int(payload.get("quantity", 2) or 2)))
    for index in range(1, count + 1):
        candidate_id = f"{task_id}-C{index:02d}"
        stem = f"{index:02d}-{_safe_slug(candidate_id + theme)}"
        if dynamic:
            frames = [_draw_sticker(f"{theme}{index}", style, frame, frame_count, True) for frame in range(frame_count)]
            target = output_dir / f"{stem}.gif"
            frames[0].save(target, save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)
            thumb = output_dir / f"{stem}-thumb.png"
            frames[0].save(thumb)
            dynamic_check = check_dynamic_asset(target)
        else:
            image = _draw_sticker(f"{theme}{index}", style, 0, 1, False)
            target = output_dir / f"{stem}.png"
            image.save(target)
            thumb = target
            dynamic_check = {"check": "dynamic_asset", "passed": False, "frame_count": 1, "reason": "static asset"}
        non_flat = check_non_flat_asset(target if target.suffix.lower() != ".gif" else thumb)
        readability = check_sticker_readability(target if target.suffix.lower() != ".gif" else thumb)
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        rel = f"{task_id}/{target.name}"
        thumb_rel = f"{task_id}/{thumb.name}"
        candidates.append(
            {
                "id": candidate_id,
                "task_id": task_id,
                "name": f"{theme} 候选 {index}",
                "format": target.suffix.lower().lstrip("."),
                "storage_path": str(target),
                "thumbnail_path": str(thumb),
                "media_url": f"/admin-assets/{rel}",
                "thumbnail_url": f"/admin-assets/{thumb_rel}",
                "file_size": target.stat().st_size,
                "width": 512,
                "height": 512,
                "is_animated": dynamic,
                "dynamic": dynamic,
                "frame_count": frame_count if dynamic else 1,
                "quality_checks": {
                    "non_flat": non_flat,
                    "readability": readability,
                    "dynamic": dynamic_check,
                },
                "quality_score": min(98, max(60, int((non_flat["score"] + readability["score"]) / 2))),
                "created_at": now,
                "updated_at": now,
            }
        )
    return candidates
