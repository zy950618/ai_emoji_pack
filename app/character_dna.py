from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any


CONSISTENCY_LOCKS = [
    "IDENTICAL_CHARACTER_DESIGN",
    "consistent face",
    "consistent outfit",
    "consistent color palette",
    "consistent body ratio",
    "consistent sticker border",
    "consistent rendering style",
]


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _digest(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class CharacterDNA:
    id: str
    name: str
    role_positioning: str
    head_features: str
    face_features: str
    body_ratio: str
    outfit: str
    color_palette: list[str]
    personality: str
    expression_style: str
    art_style: str
    background_style: str
    consistency_lock: list[str]
    negative_rules: list[str]
    source_image_url: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_character_dna(payload: dict[str, Any]) -> dict[str, Any]:
    theme = str(payload.get("theme") or payload.get("name") or "打工猫日常").strip()
    style = str(payload.get("style") or "3D 软胶贴纸").strip()
    source_image_url = str(payload.get("source_image_url") or payload.get("reference_url") or "").strip()
    palette_seed = int(_digest(theme + style), 16)
    palettes = [
        ["warm cream", "coral red", "soft graphite", "sunny yellow"],
        ["milk white", "aurora blue", "ink black", "mint green"],
        ["sakura pink", "warm gray", "berry red", "paper white"],
        ["bamboo green", "tea brown", "ivory", "deep ink"],
    ]
    palette = palettes[palette_seed % len(palettes)]
    now = _now()
    name = str(payload.get("name") or f"{theme[:8]}角色").strip()
    dna = CharacterDNA(
        id=f"DNA-{_digest(theme + style + source_image_url)}",
        name=name,
        role_positioning=str(payload.get("role_positioning") or f"{theme}的主角，适合聊天场景连续表达"),
        head_features=str(payload.get("head_features") or "圆润头部，清晰外轮廓，贴纸边缘干净"),
        face_features=str(payload.get("face_features") or "大眼睛，高识别度表情，嘴型随情绪变化"),
        body_ratio=str(payload.get("body_ratio") or "2.5 头身 Q 版比例，重心稳定"),
        outfit=str(payload.get("outfit") or "固定主题服装和小道具，便于套图保持一致"),
        color_palette=list(payload.get("color_palette") or palette),
        personality=str(payload.get("personality") or "夸张、幽默、亲近，有清晰情绪峰值"),
        expression_style=str(payload.get("expression_style") or "喜怒哀乐动作夸张，适合小尺寸识别"),
        art_style=style,
        background_style=str(payload.get("background_style") or "经典贴纸风：透明底 / 白色描边"),
        consistency_lock=list(payload.get("consistency_lock") or CONSISTENCY_LOCKS),
        negative_rules=list(
            payload.get("negative_rules")
            or ["flat vector", "generic emoji placeholder", "plain text sticker", "low detail", "inconsistent outfit"]
        ),
        source_image_url=source_image_url,
        created_at=now,
        updated_at=now,
    )
    return dna.to_dict()
