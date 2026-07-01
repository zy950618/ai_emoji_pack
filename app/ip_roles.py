import json
import sqlite3
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.schemas import 创建原创角色请求


class 原创角色服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 创建(self, 操作人编号: str, 请求: 创建原创角色请求) -> dict[str, object]:
        if 请求.是否依赖真人肖像:
            raise 业务异常("原创角色不能依赖真人肖像", "肖像风险", 409)
        if 请求.是否疑似已有IP:
            raise 业务异常("原创角色不能疑似已有 IP", "版权风险", 409)

        角色编号 = f"ROLE-{uuid.uuid4().hex[:12]}"
        try:
            self.数据库.执行(
                """
                INSERT INTO original_roles
                (角色编号, 角色名称, 人设, 动作库, 口头禅, 风格关键词, 可复用)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    角色编号,
                    请求.角色名称,
                    请求.人设,
                    json.dumps(请求.动作库, ensure_ascii=False),
                    json.dumps(请求.口头禅, ensure_ascii=False),
                    json.dumps(请求.风格关键词, ensure_ascii=False),
                    1,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise 业务异常("原创角色已存在", "重复数据", 409) from exc

        self.审计.记录(操作人编号, "创建原创角色", "原创角色", 角色编号, {"角色名称": 请求.角色名称})
        return self._获取(角色编号)

    def 列表(self) -> list[dict[str, object]]:
        return [self._转字典(row) for row in self.数据库.查询全部("SELECT * FROM original_roles ORDER BY 创建时间 ASC")]

    def _获取(self, 角色编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM original_roles WHERE 角色编号 = ?", (角色编号,))
        if not row:
            raise 业务异常("原创角色不存在", "角色不存在", 404)
        return self._转字典(row)

    @staticmethod
    def _转字典(row) -> dict[str, object]:
        return {
            "角色编号": row["角色编号"],
            "角色名称": row["角色名称"],
            "人设": row["人设"],
            "动作库": json.loads(row["动作库"]),
            "口头禅": json.loads(row["口头禅"]),
            "风格关键词": json.loads(row["风格关键词"]),
            "可复用": bool(row["可复用"]),
        }
