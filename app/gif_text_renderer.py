from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageSequence

from app.layout_engine import _font


def _now_id() -> str:
    return datetime.now(UTC).strftime("%H%M%S%f")


def _fallback_gif(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    for index in range(4):
        image = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((140, 120 + index * 8, 372, 352 + index * 8), fill=(115, 174, 255, 255), outline=(25, 29, 38, 255), width=8)
        draw.text((210, 232 + index * 8), "GIF", fill=(255, 255, 255, 255), font=ImageFont.load_default())
        frames.append(image)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)


def render_gif_text(payload: dict[str, Any], output_root: Path) -> dict[str, Any]:
    render_id = str(payload.get("render_id") or f"GIF-{_now_id()}")
    output_root.mkdir(parents=True, exist_ok=True)
    source = Path(str(payload.get("source_path") or ""))
    if not source.is_file():
        source = output_root / f"{render_id}-source.gif"
        _fallback_gif(source)
    target = output_root / f"{render_id}.gif"
    text = str(payload.get("text") or payload.get("caption") or "收到")
    font = _font(int(payload.get("font_size") or 42))
    frames = []
    with Image.open(source) as image:
        duration = image.info.get("duration", 120)
        for frame in ImageSequence.Iterator(image):
            canvas = frame.convert("RGBA").resize((512, 512))
            draw = ImageDraw.Draw(canvas)
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=5)
            x = int((512 - (bbox[2] - bbox[0])) / 2)
            y = 420
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(20, 24, 32, 255))
            frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    if len(frames) < 4:
        frames = frames * (4 // max(1, len(frames)) + 1)
        frames = frames[:4]
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=duration, loop=0, disposal=2)
    return {"render_id": render_id, "source_path": str(source), "output_path": str(target), "download_url": f"/admin-assets/renders/{target.name}", "frame_count": len(frames), "duration_ms": duration * len(frames), "text": text}
