from __future__ import annotations

from typing import Any


PLATFORM_SPECS: dict[str, dict[str, Any]] = {
    "WeChat": {
        "main_stickers": {"width": 240, "height": 240, "format": "PNG"},
        "banner": {"width": 750, "height": 400, "format": "PNG"},
        "icon": {"width": 50, "height": 50, "format": "PNG"},
        "cover": {"width": 240, "height": 240, "format": "PNG"},
        "transparent_png": True,
        "naming_rule": "wechat_{index:02d}.png",
    },
    "Telegram": {"main_stickers": {"width": 512, "height": 512, "format": "WEBP"}, "transparent_png": True},
    "LINE": {"main_stickers": {"width": 370, "height": 320, "format": "PNG"}, "transparent_png": True},
    "WhatsApp": {"main_stickers": {"width": 512, "height": 512, "format": "WEBP"}, "transparent_png": True},
}


def get_platform_spec(platform: str) -> dict[str, Any]:
    return dict(PLATFORM_SPECS.get(platform, PLATFORM_SPECS["WeChat"]))
