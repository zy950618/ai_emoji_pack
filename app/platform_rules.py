from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class 平台规则:
    平台名称: str
    规则版本: str
    规则来源: str
    最少数量: int
    最多数量: int
    宽度: int
    高度: int
    允许格式: tuple[str, ...]
    最大文件大小KB: int
    要求透明背景: bool
    支持自动发布: bool
    需要人工复核: bool
    合法样例: dict[str, object]
    非法样例: dict[str, object]

    def 转字典(self) -> dict[str, object]:
        data = asdict(self)
        data["允许格式"] = list(self.允许格式)
        return data


规则来源 = "项目第一阶段内置基线规则，真实发布前必须人工复核平台最新规则"

平台规则库: dict[str, 平台规则] = {
    "微信": 平台规则("微信", "baseline-2026-06", 规则来源, 16, 24, 240, 240, ("PNG", "GIF"), 500, True, False, True, {"数量": 16, "格式": "PNG"}, {"数量": 3, "原因": "数量不足"}),
    "LINE": 平台规则("LINE", "baseline-2026-06", 规则来源, 8, 40, 370, 320, ("PNG",), 1000, True, False, True, {"数量": 8, "格式": "PNG"}, {"格式": "JPG", "原因": "格式不允许"}),
    "Telegram": 平台规则("Telegram", "baseline-2026-06", 规则来源, 1, 120, 512, 512, ("PNG", "WEBP"), 512, True, True, True, {"数量": 1, "格式": "PNG"}, {"宽度": 240, "原因": "尺寸不符合"}),
    "WhatsApp": 平台规则("WhatsApp", "baseline-2026-06", 规则来源, 3, 30, 512, 512, ("WEBP",), 100, True, False, True, {"数量": 3, "格式": "WEBP"}, {"文件大小KB": 500, "原因": "文件过大"}),
    "Discord": 平台规则("Discord", "baseline-2026-06", 规则来源, 1, 50, 320, 320, ("PNG", "GIF", "WEBP"), 256, True, False, True, {"数量": 1, "格式": "PNG"}, {"是否透明背景": False, "原因": "背景不透明"}),
    "GIPHY": 平台规则("GIPHY", "baseline-2026-06", 规则来源, 1, 50, 500, 500, ("GIF", "WEBP"), 8000, False, False, True, {"数量": 1, "格式": "GIF"}, {"格式": "BMP", "原因": "格式不允许"}),
    "iMessage": 平台规则("iMessage", "baseline-2026-06", 规则来源, 3, 30, 408, 408, ("PNG", "GIF"), 500, True, False, True, {"数量": 3, "格式": "PNG"}, {"高度": 200, "原因": "尺寸不符合"}),
}


def 获取平台规则(平台名称: str) -> 平台规则:
    if 平台名称 not in 平台规则库:
        from app.exceptions import 业务异常

        raise 业务异常("平台规则不存在", "平台不存在", 404)
    return 平台规则库[平台名称]


def 列出平台规则() -> list[dict[str, object]]:
    return [rule.转字典() for rule in 平台规则库.values()]
