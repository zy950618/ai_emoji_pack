import json
import os

from app.exceptions import 业务异常


class 开放发布适配器:
    def 发布(self, 发布平台: str, 发布账号: str, 提交包: dict[str, object]) -> dict[str, object]:
        mock_response = os.getenv("AI_EMOJI_OPEN_PUBLISH_MOCK_RESPONSE")
        if mock_response:
            data = json.loads(mock_response)
            return self._解析本地回执(发布平台, data)
        return {
            "平台": 发布平台,
            "发布账号": 发布账号,
            "模式": "本地开放发布回执",
            "外部发布编号": f"local-open-{提交包['提交包编号']}",
            "是否访问外网": False,
        }

    @staticmethod
    def _解析本地回执(发布平台: str, data: dict[str, object]) -> dict[str, object]:
        if data.get("ok") is False:
            raise 业务异常("开放发布适配器返回失败", "平台发布失败", 502)
        publish_id = str(data.get("publish_id") or data.get("message_id") or "mock")
        return {
            "平台": 发布平台,
            "模式": "本地mock回执",
            "外部发布编号": f"local-open-{publish_id}",
            "是否访问外网": False,
        }
