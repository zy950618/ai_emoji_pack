import json
import sqlite3
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.platform_rules import 平台规则, 平台规则库
from app.schemas import 创建平台规则版本请求


class 平台规则治理服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 初始化基线规则(self) -> None:
        for rule in 平台规则库.values():
            exists = self.数据库.查询一条(
                "SELECT 1 FROM platform_rule_versions WHERE 平台名称 = ? AND 规则版本 = ?",
                (rule.平台名称, rule.规则版本),
            )
            if exists:
                continue
            self._插入版本(rule, "启用", "system")
            self._写变更日志(rule.平台名称, None, rule.规则版本, "初始化基线规则", "应用启动时写入内置基线规则", "system")

    def 列出当前规则(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM platform_rule_versions WHERE 状态 = ? ORDER BY 平台名称 ASC", ("启用",))
        return [self._row_to_rule(row).转字典() | {"状态": row["状态"]} for row in rows]

    def 获取当前规则(self, 平台名称: str) -> 平台规则:
        row = self.数据库.查询一条(
            "SELECT * FROM platform_rule_versions WHERE 平台名称 = ? AND 状态 = ?",
            (平台名称, "启用"),
        )
        if not row:
            raise 业务异常("平台规则不存在", "平台不存在", 404)
        return self._row_to_rule(row)

    def 列出版本(self, 平台名称: str) -> list[dict[str, object]]:
        rows = self.数据库.查询全部(
            "SELECT * FROM platform_rule_versions WHERE 平台名称 = ? ORDER BY 创建时间 ASC",
            (平台名称,),
        )
        return [self._版本字典(row) for row in rows]

    def 创建版本(self, 操作人编号: str, 请求: 创建平台规则版本请求) -> dict[str, object]:
        if 请求.最少数量 > 请求.最多数量:
            raise 业务异常("最少数量不能大于最多数量", "规则不合法", 422)
        rule = 平台规则(
            请求.平台名称,
            请求.规则版本,
            请求.规则来源,
            请求.最少数量,
            请求.最多数量,
            请求.宽度,
            请求.高度,
            tuple(格式.upper() for 格式 in 请求.允许格式),
            请求.最大文件大小KB,
            请求.要求透明背景,
            请求.支持自动发布,
            请求.需要人工复核,
            请求.合法样例,
            请求.非法样例,
        )
        try:
            self._插入版本(rule, "待启用", 操作人编号)
        except sqlite3.IntegrityError as exc:
            raise 业务异常("平台规则版本已存在", "重复数据", 409) from exc
        self._写变更日志(rule.平台名称, self._当前版本号(rule.平台名称), rule.规则版本, "创建规则版本", 请求.变更原因, 操作人编号)
        self.审计.记录(操作人编号, "创建平台规则版本", "平台规则", rule.平台名称, {"规则版本": rule.规则版本})
        return self._版本字典(
            self.数据库.查询一条(
                "SELECT * FROM platform_rule_versions WHERE 平台名称 = ? AND 规则版本 = ?",
                (rule.平台名称, rule.规则版本),
            )
        )

    def 启用版本(self, 操作人编号: str, 平台名称: str, 规则版本: str, 原因: str) -> dict[str, object]:
        row = self._获取版本行(平台名称, 规则版本)
        rule = self._row_to_rule(row)
        if not rule.规则来源 or not rule.合法样例 or not rule.非法样例:
            raise 业务异常("规则来源和正反样例齐全后才能启用", "规则不完整", 409)
        old_version = self._当前版本号(平台名称)
        self.数据库.执行("UPDATE platform_rule_versions SET 状态 = ? WHERE 平台名称 = ?", ("停用", 平台名称))
        self.数据库.执行(
            "UPDATE platform_rule_versions SET 状态 = ? WHERE 平台名称 = ? AND 规则版本 = ?",
            ("启用", 平台名称, 规则版本),
        )
        self._写变更日志(平台名称, old_version, 规则版本, "启用规则版本", 原因, 操作人编号)
        self.审计.记录(操作人编号, "启用平台规则版本", "平台规则", 平台名称, {"原版本": old_version, "新版本": 规则版本})
        return self.获取当前规则(平台名称).转字典() | {"状态": "启用"}

    def 回滚版本(self, 操作人编号: str, 平台名称: str, 目标版本: str, 原因: str) -> dict[str, object]:
        current = self._当前版本号(平台名称)
        if current == 目标版本:
            raise 业务异常("目标版本已经是当前启用版本", "无需回滚", 409)
        self._获取版本行(平台名称, 目标版本)
        self.数据库.执行("UPDATE platform_rule_versions SET 状态 = ? WHERE 平台名称 = ?", ("停用", 平台名称))
        self.数据库.执行(
            "UPDATE platform_rule_versions SET 状态 = ? WHERE 平台名称 = ? AND 规则版本 = ?",
            ("启用", 平台名称, 目标版本),
        )
        self._写变更日志(平台名称, current, 目标版本, "回滚规则版本", 原因, 操作人编号)
        self.审计.记录(操作人编号, "回滚平台规则版本", "平台规则", 平台名称, {"原版本": current, "目标版本": 目标版本})
        return self.获取当前规则(平台名称).转字典() | {"状态": "启用"}

    def 变更日志(self, 平台名称: str | None = None) -> list[dict[str, object]]:
        if 平台名称:
            rows = self.数据库.查询全部(
                "SELECT * FROM platform_rule_change_logs WHERE 平台名称 = ? ORDER BY 创建时间 ASC",
                (平台名称,),
            )
        else:
            rows = self.数据库.查询全部("SELECT * FROM platform_rule_change_logs ORDER BY 创建时间 ASC")
        return [dict(row) for row in rows]

    def _插入版本(self, rule: 平台规则, 状态: str, 创建人: str) -> None:
        self.数据库.执行(
            """
            INSERT INTO platform_rule_versions (版本编号, 平台名称, 规则版本, 状态, 规则数据, 创建人)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (f"RULE-{uuid.uuid4().hex[:12]}", rule.平台名称, rule.规则版本, 状态, json.dumps(rule.转字典(), ensure_ascii=False), 创建人),
        )

    def _写变更日志(self, 平台名称: str, 原版本: str | None, 新版本: str, 动作: str, 原因: str, 操作人: str) -> None:
        self.数据库.执行(
            """
            INSERT INTO platform_rule_change_logs (变更编号, 平台名称, 原版本, 新版本, 动作, 原因, 操作人)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (f"LOG-{uuid.uuid4().hex[:12]}", 平台名称, 原版本, 新版本, 动作, 原因, 操作人),
        )

    def _当前版本号(self, 平台名称: str) -> str | None:
        row = self.数据库.查询一条(
            "SELECT 规则版本 FROM platform_rule_versions WHERE 平台名称 = ? AND 状态 = ?",
            (平台名称, "启用"),
        )
        return row["规则版本"] if row else None

    def _获取版本行(self, 平台名称: str, 规则版本: str):
        row = self.数据库.查询一条(
            "SELECT * FROM platform_rule_versions WHERE 平台名称 = ? AND 规则版本 = ?",
            (平台名称, 规则版本),
        )
        if not row:
            raise 业务异常("平台规则版本不存在", "规则版本不存在", 404)
        return row

    @staticmethod
    def _row_to_rule(row) -> 平台规则:
        data = json.loads(row["规则数据"])
        return 平台规则(
            data["平台名称"],
            data["规则版本"],
            data["规则来源"],
            data["最少数量"],
            data["最多数量"],
            data["宽度"],
            data["高度"],
            tuple(data["允许格式"]),
            data["最大文件大小KB"],
            data["要求透明背景"],
            data["支持自动发布"],
            data["需要人工复核"],
            data["合法样例"],
            data["非法样例"],
        )

    @staticmethod
    def _版本字典(row) -> dict[str, object]:
        data = json.loads(row["规则数据"])
        return data | {"状态": row["状态"], "创建人": row["创建人"], "创建时间": row["创建时间"]}
