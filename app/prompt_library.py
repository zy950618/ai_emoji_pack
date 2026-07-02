from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY_VERSION = "loop5.4-local-v1"


def default_meme_prompt_library() -> dict[str, Any]:
    return {
        "version": DEFAULT_LIBRARY_VERSION,
        "raw_source_exposed": False,
        "principles": [
            "define audience, platform, subject, emotion, action, and final asset constraints",
            "prefer layered character, prop, light, shadow, and material detail over flat icon language",
            "include negative constraints for logos, real-person likeness, bland vector art, and unreadable text",
            "separate static composition from dynamic motion planning",
        ],
        "style_blocks": {
            "3D soft sticker": ["rounded volume", "soft rim light", "clay-like material", "clean transparent edge"],
            "watercolor": ["paper grain", "wet edge", "layered pigment", "soft background wash"],
            "pixel sticker": ["crisp pixel clusters", "limited palette", "chunky silhouette", "no antialias blur"],
            "ink comic": ["bold contour", "screen tone", "expressive motion line", "high contrast"],
            "premium meme": ["large readable face", "clear gesture", "foreground prop", "mobile thumbnail readable"],
        },
        "platform_rules": {
            "WeChat": {"size": "512x512", "format": "PNG/GIF", "text": "short Chinese caption, readable at 96px"},
            "Telegram": {"size": "512x512", "format": "transparent PNG or animated GIF", "text": "minimal caption"},
            "LINE": {"size": "512x512", "format": "PNG/GIF", "text": "clear emotional expression"},
            "WhatsApp": {"size": "512x512", "format": "PNG/GIF", "text": "bold silhouette and small file size"},
        },
        "dynamic_motions": {
            "bounce": ["anticipation squash", "upward lift", "settle with secondary prop motion"],
            "wave": ["arm arc", "face follows motion", "small highlight flicker"],
            "shake": ["two-sided offset", "motion blur hint", "final stable pose"],
            "spark": ["accent pop", "glow pulse", "fade particles"],
        },
    }


def ensure_meme_prompt_library(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if data.get("version") == DEFAULT_LIBRARY_VERSION and data.get("raw_source_exposed") is False:
            return data
    data = default_meme_prompt_library()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return data
