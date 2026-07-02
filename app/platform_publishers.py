from app.exceptions import 业务异常


class 开放发布适配器:
    def 发布(self, 发布平台: str, 发布账号: str, 提交包: dict[str, object]) -> dict[str, object]:
        raise 业务异常(
            f"{发布平台} 真实发布适配器未配置，不能使用本地回执标记发布成功",
            "发布适配器未配置",
            502,
        )
