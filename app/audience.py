import json
import sqlite3
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.schemas import 创建受众画像请求


class 受众画像服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 创建(self, 操作人编号: str, 请求: 创建受众画像请求) -> dict[str, object]:
        画像编号 = f"AUD-{uuid.uuid4().hex[:12]}"
        try:
            self.数据库.执行(
                """
                INSERT INTO audience_profiles
                (画像编号, 画像名称, 年龄段, 兴趣标签, 使用场景, 风格偏好, 禁用内容, 风险等级)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    画像编号,
                    请求.画像名称,
                    请求.年龄段,
                    json.dumps(请求.兴趣标签, ensure_ascii=False),
                    json.dumps(请求.使用场景, ensure_ascii=False),
                    json.dumps(请求.风格偏好, ensure_ascii=False),
                    json.dumps(请求.禁用内容, ensure_ascii=False),
                    请求.风险等级,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise 业务异常("受众画像已存在", "重复数据", 409) from exc

        self.审计.记录(操作人编号, "创建受众画像", "受众画像", 画像编号, {"画像名称": 请求.画像名称})
        return self._获取(画像编号)

    def 列表(self) -> list[dict[str, object]]:
        return [self._转字典(row) for row in self.数据库.查询全部("SELECT * FROM audience_profiles ORDER BY 创建时间 ASC")]

    def _获取(self, 画像编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM audience_profiles WHERE 画像编号 = ?", (画像编号,))
        if not row:
            raise 业务异常("受众画像不存在", "画像不存在", 404)
        return self._转字典(row)

    @staticmethod
    def _转字典(row) -> dict[str, object]:
        return {
            "画像编号": row["画像编号"],
            "画像名称": row["画像名称"],
            "年龄段": row["年龄段"],
            "兴趣标签": json.loads(row["兴趣标签"]),
            "使用场景": json.loads(row["使用场景"]),
            "风格偏好": json.loads(row["风格偏好"]),
            "禁用内容": json.loads(row["禁用内容"]),
            "风险等级": row["风险等级"],
        }
