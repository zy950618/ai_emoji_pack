from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any

from app.character_dna import CONSISTENCY_LOCKS


EMOTION_ACTIONS = [
    ("开心", "挥手", "今天也要开工", "清晨打开聊天窗口"),
    ("震惊", "后仰", "真的假的", "消息弹窗突然出现"),
    ("无语", "抱臂", "我先沉默一下", "会议室冷场"),
    ("加油", "握拳", "撑住就赢了", "桌面前打气"),
    ("委屈", "低头", "我真的尽力了", "角落小声解释"),
    ("得意", "叉腰", "这波我懂", "任务完成后展示成果"),
    ("困倦", "揉眼", "先让我缓缓", "深夜电脑旁"),
    ("庆祝", "跳起", "下班快乐", "彩带和灯光"),
    ("拒绝", "摆手", "这个不行", "需求评审现场"),
    ("疑问", "歪头", "你确定吗", "看着屏幕思考"),
    ("治愈", "递茶", "慢慢来", "温暖台灯下"),
    ("催促", "举牌", "快交付", "任务看板前"),
    ("尴尬", "挠头", "场面有点复杂", "聊天气泡旁"),
    ("点赞", "竖拇指", "可以上线", "发布前确认"),
    ("爆笑", "拍桌", "笑不活了", "群聊热闹场景"),
    ("晚安", "盖被", "今天收工", "月光窗边"),
    ("灵感", "举灯泡", "想到办法了", "白板前"),
    ("焦虑", "抱头", "又改需求", "堆叠便签旁"),
    ("摸鱼", "偷看", "我不在", "办公桌下"),
    ("感谢", "鞠躬", "收到谢谢", "干净背景中"),
    ("生气", "跺脚", "别再催了", "红色动势线"),
    ("惊喜", "捧脸", "还有这种好事", "礼物盒旁"),
    ("思考", "托腮", "让我想想", "空白便签旁"),
    ("胜利", "举杯", "拿下", "小型庆功场景"),
]


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _digest(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class StickerPlanItem:
    id: str
    index: int
    emotion: str
    action: str
    caption: str
    scene: str
    prompt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_sticker_plan(payload: dict[str, Any], dna: dict[str, Any]) -> dict[str, Any]:
    requested = int(payload.get("quantity") or payload.get("count") or 16)
    quantity = max(1, min(48, requested))
    platform = str(payload.get("platform") or "WeChat")
    tone = str(payload.get("tone") or "打工人")
    style = str(payload.get("style") or dna.get("art_style") or "微信透明贴纸")
    background_style = str(payload.get("background_style") or dna.get("background_style") or "经典贴纸风")
    dynamic = bool(payload.get("dynamic") or payload.get("is_animated"))
    plan_id = f"PLAN-{_digest(str(dna.get('id', 'dna')) + platform + str(quantity) + tone + style)}"
    items = []
    for index in range(quantity):
        emotion, action, caption, scene = EMOTION_ACTIONS[index % len(EMOTION_ACTIONS)]
        prompt = (
            f"{dna.get('name')}，{dna.get('role_positioning')}，{style}，{background_style}，"
            f"emotion={emotion}，action={action}，caption={caption}，scene={scene}，"
            f"{'; '.join(dna.get('consistency_lock') or CONSISTENCY_LOCKS)}，"
            f"palette={', '.join(dna.get('color_palette') or [])}，"
            "rich foreground/midground/background depth, soft volumetric lighting, sticker outline, "
            "mobile thumbnail readability, transparent PNG friendly edge, no flat vector, no generic emoji placeholder"
        )
        items.append(
            StickerPlanItem(
                id=f"{plan_id}-ITEM-{index + 1:02d}",
                index=index + 1,
                emotion=emotion,
                action=action,
                caption=caption,
                scene=scene,
                prompt=prompt,
            ).to_dict()
        )
    now = _now()
    return {
        "id": plan_id,
        "dna_id": dna.get("id"),
        "platform": platform,
        "quantity": quantity,
        "tone": tone,
        "style": style,
        "background_style": background_style,
        "dynamic": dynamic,
        "workflow_stages": [
            "api_source_config",
            "requirements_input",
            "reference_upload",
            "character_dna",
            "plan_confirm",
            "preview_iteration",
            "batch_generation",
            "promotion_assets",
            "platform_conversion",
            "library_export",
        ],
        "items": items,
        "created_at": now,
        "updated_at": now,
    }
