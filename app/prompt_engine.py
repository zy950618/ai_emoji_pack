from __future__ import annotations

from pathlib import Path
from typing import Any

from app.prompt_library import ensure_meme_prompt_library
from app.prompt_sources import prompt_sources_status, prompt_source_paths


def _clean(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def build_meme_prompt(
    theme: str,
    platform: str = "WeChat",
    style: str = "premium meme",
    mode: str = "static",
    dynamic: bool = False,
    constraints: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or Path(__file__).resolve().parents[1]
    library = ensure_meme_prompt_library(prompt_source_paths(project_root)["meme_prompt_library"])
    sources = prompt_sources_status(project_root)
    theme_text = _clean(theme, "职场猫咪鼓励表情")
    platform_text = _clean(platform, "WeChat")
    style_text = _clean(style, "premium meme")
    constraints = constraints or {}
    platform_rule = library["platform_rules"].get(platform_text, library["platform_rules"]["WeChat"])
    style_terms = library["style_blocks"].get(style_text, library["style_blocks"]["premium meme"])
    motion_type = _clean(constraints.get("motion_type"), "bounce")
    motion_steps = library["dynamic_motions"].get(motion_type, library["dynamic_motions"]["bounce"])
    quality_rules = [
        "主体必须有前景/中景/高光/投影层次，不允许扁平灰块或单一色面",
        "缩略图 96px 仍能辨认表情、动作和短字幕",
        "透明边缘干净，不能出现真实品牌、真人肖像或侵权 IP",
        "输出前执行非扁平、动态帧数、可读性和差异度检查",
    ]
    prompt = (
        f"为单用户表情包后台生成一张{platform_text}表情：主题《{theme_text}》，风格 {style_text}。"
        f"画面包含夸张表情、明确动作、可识别道具、透明背景和干净贴纸描边。"
        f"视觉关键词：{', '.join(style_terms)}。平台约束：{platform_rule['size']}，{platform_rule['format']}，"
        f"{platform_rule['text']}。构图必须分层：角色主体、互动道具、阴影、高光、装饰粒子分别可辨。"
    )
    negative_prompt = (
        "不要生成扁平图标、灰色占位图、纯文字贴图、企业插画模板、低细节头像、品牌 Logo、真实人物肖像、"
        "侵权角色、模糊边缘、不可读小字或单帧伪动态。"
    )
    dynamic_plan = {
        "enabled": bool(dynamic),
        "mode": mode,
        "motion_type": motion_type,
        "frame_count": max(4, int(constraints.get("frame_count", 6) or 6)) if dynamic else 1,
        "steps": motion_steps if dynamic else ["static layered pose"],
    }
    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "quality_rules": quality_rules,
        "platform_rules": platform_rule,
        "dynamic_plan": dynamic_plan,
        "source_mix": [
            {"source": "f/prompts.chat", "usage": "sanitized prompt structure patterns"},
            {"source": "x1xhlol/system-prompts-and-models-of-ai-tools", "usage": "sanitized constraint and verification patterns"},
            {"source": "local meme prompt library", "usage": "platform, style, motion, and quality rules"},
        ],
        "prompt_sources_report": sources["report"],
        "raw_source_exposed": False,
    }


def optimize_prompt_local(prompt: str) -> str:
    base = _clean(prompt, "生成一个可发布的表情包贴纸")
    return (
        f"{base}\n\n本地优化：补充主体动作、表情峰值、前中后景层次、材质高光、透明边缘、"
        "移动端缩略图可读性、平台尺寸、负面约束、动态帧计划和失败回退规则。"
    )
