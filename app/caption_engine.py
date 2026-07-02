from __future__ import annotations

from hashlib import sha1
from typing import Any


TONES = ["沙雕", "社畜", "阴阳怪气", "可爱", "冷幽默", "治愈", "发疯文学", "打工人", "反差萌"]
STYLES = ["经典白字黑边", "微博热评风", "聊天截图风", "3D 软胶贴纸", "手绘漫画", "水彩质感", "厚涂插画", "国风水墨", "像素贴纸", "微信透明贴纸"]


CAPTION_BANK = {
    "沙雕": ["笑不活了", "这也太离谱", "我先笑为敬", "精神状态良好"],
    "社畜": ["收到马上改", "今天也在努力", "先别催我", "下班再说"],
    "阴阳怪气": ["你说得都对", "真是太合理了", "我悟了", "这很难评"],
    "可爱": ["贴贴", "收到啦", "嘿嘿", "给你小花"],
    "冷幽默": ["问题不大，只是很大", "稳定发挥", "已读但在缓冲", "我选择重启"],
    "治愈": ["慢慢来", "辛苦啦", "抱抱你", "今天也很好"],
    "发疯文学": ["我直接起飞", "别管我了", "世界重启中", "让我尖叫三秒"],
    "打工人": ["打工魂启动", "需求又变了", "我还能改", "上线见"],
    "反差萌": ["看起来很凶其实很乖", "认真可爱中", "小声顶嘴", "乖巧但不多"],
}


def generate_captions(payload: dict[str, Any]) -> dict[str, Any]:
    tone = str(payload.get("tone") or "打工人")
    if tone not in TONES:
        tone = "打工人"
    style = str(payload.get("style") or "经典白字黑边")
    theme = str(payload.get("theme") or payload.get("image_summary") or "表情包")
    platform = str(payload.get("platform") or "WeChat")
    seed = int(sha1((theme + tone + style).encode("utf-8")).hexdigest(), 16)
    bank = CAPTION_BANK[tone]
    captions = [bank[(seed + index) % len(bank)] for index in range(4)]
    captions.append(f"{theme[:6]}也太会了")
    return {
        "tone": tone,
        "style": style if style in STYLES else "经典白字黑边",
        "platform": platform,
        "captions": captions,
        "safe_area": {"preferred": "bottom", "avoid_subject": True, "padding": 24},
        "font_plan": {"font_size": 42, "stroke_width": 5, "shadow": True, "line_spacing": 1.12},
        "layout_plan": {"position": "bottom", "align": "center", "max_width_ratio": 0.86},
    }
