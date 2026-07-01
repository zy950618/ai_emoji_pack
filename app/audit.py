import json
from typing import Any

from app.database import 数据库


class 审计服务:
    def __init__(self, 数据库实例: 数据库) -> None:
        self.数据库 = 数据库实例

    def 记录(self, 操作人: str, 动作: str, 目标类型: str, 目标编号: str, 详情: dict[str, Any]) -> None:
        self.数据库.执行(
            """
            INSERT INTO audit_logs (操作人, 动作, 目标类型, 目标编号, 详情)
            VALUES (?, ?, ?, ?, ?)
            """,
            (操作人, 动作, 目标类型, 目标编号, json.dumps(详情, ensure_ascii=False)),
        )

    def 列表(self) -> list[dict[str, Any]]:
        rows = self.数据库.查询全部("SELECT * FROM audit_logs ORDER BY id ASC")
        return [dict(row) for row in rows]
