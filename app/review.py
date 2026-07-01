import json
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.schemas import 自动初审请求, 二审请求, 表情包审核请求


高风险标签 = {"肖像风险", "版权风险", "低俗", "血腥暴力", "仇恨歧视", "未成年人风险", "政治敏感", "赌博毒品", "违法引导", "医疗误导"}


class 审核服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 自动初审(self, 请求: 自动初审请求) -> dict[str, object]:
        self._确认套装存在(请求.套装编号)
        if not self._最新校验通过(请求.套装编号):
            raise 业务异常("平台规则未通过，不能自动初审", "校验未通过", 409)

        命中高风险 = sorted(高风险标签.intersection(set(请求.风险标签)))
        if 命中高风险:
            状态 = "自动初审失败"
            审核结论 = "失败"
            审核意见 = f"{请求.审核意见}；命中高风险：{','.join(命中高风险)}"
        else:
            状态 = "待审核"
            审核结论 = "通过"
            审核意见 = 请求.审核意见

        record = self._写审核记录("auto-review", 请求.套装编号, "自动初审", 审核结论, 请求.风险标签, 审核意见, False, 状态)
        self.审计.记录("auto-review", "自动初审", "套装", 请求.套装编号, {"审核编号": record["审核编号"], "状态": 状态})
        return record

    def 审核(self, 审核人: str, 请求: 表情包审核请求) -> dict[str, object]:
        self._确认套装存在(请求.套装编号)
        if not self._最新校验通过(请求.套装编号):
            raise 业务异常("平台规则未通过，不能审核通过", "校验未通过", 409)
        if 请求.审核结论 == "失败" and not 请求.审核意见:
            raise 业务异常("审核失败必须填写原因", "审核原因缺失", 422)
        if 请求.审核结论 == "通过" and 高风险标签.intersection(set(请求.风险标签)) and not 请求.是否需要二审:
            raise 业务异常("高风险审核通过必须进入二审", "需要二审", 409)

        状态 = "待二审" if 请求.是否需要二审 else ("审核通过" if 请求.审核结论 == "通过" else "审核失败")
        record = self._写审核记录(审核人, 请求.套装编号, "人工审核", 请求.审核结论, 请求.风险标签, 请求.审核意见, 请求.是否需要二审, 状态)
        self.审计.记录(审核人, "审核表情包", "套装", 请求.套装编号, {"审核编号": record["审核编号"], "审核结论": 请求.审核结论, "状态": 状态})
        return record

    def 二审(self, 审核人: str, 请求: 二审请求) -> dict[str, object]:
        self._确认套装存在(请求.套装编号)
        当前状态 = self._套装状态(请求.套装编号)
        if 当前状态 != "待二审":
            raise 业务异常("只有待二审套装可以执行二审", "状态不允许", 409)
        if 请求.审核结论 == "失败" and not 请求.审核意见:
            raise 业务异常("二审失败必须填写原因", "审核原因缺失", 422)

        状态 = "审核通过" if 请求.审核结论 == "通过" else "审核失败"
        record = self._写审核记录(审核人, 请求.套装编号, "二审", 请求.审核结论, 请求.风险标签, 请求.审核意见, False, 状态)
        self.审计.记录(审核人, "二审表情包", "套装", 请求.套装编号, {"审核编号": record["审核编号"], "审核结论": 请求.审核结论, "状态": 状态})
        return record

    def 记录退回重生成(self, 操作人: str, 原套装编号: str, 退回原因: str, 新策略结果: dict[str, object]) -> dict[str, object]:
        self._确认套装存在(原套装编号)
        退回编号 = f"REG-{uuid.uuid4().hex[:12]}"
        新套装 = 新策略结果["套装"]
        self.数据库.执行(
            """
            INSERT INTO regenerate_requests (退回编号, 原套装编号, 新策略编号, 新套装编号, 退回原因, 操作人)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (退回编号, 原套装编号, 新策略结果["策略编号"], 新套装["套装编号"], 退回原因, 操作人),
        )
        self.数据库.执行("UPDATE sticker_sets SET 状态 = ? WHERE 套装编号 = ?", ("退回重生成", 原套装编号))
        self.审计.记录(操作人, "退回重生成", "套装", 原套装编号, {"退回编号": 退回编号, "新套装编号": 新套装["套装编号"]})
        return {
            "退回编号": 退回编号,
            "原套装编号": 原套装编号,
            "新策略编号": 新策略结果["策略编号"],
            "新套装编号": 新套装["套装编号"],
            "退回原因": 退回原因,
            "原套装状态": "退回重生成",
        }

    def 列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM review_records ORDER BY 创建时间 ASC")
        return [
            {
                "审核编号": row["审核编号"],
                "套装编号": row["套装编号"],
                "审核阶段": row["审核阶段"],
                "审核结论": row["审核结论"],
                "风险标签": json.loads(row["风险标签"]),
                "审核意见": row["审核意见"],
                "是否需要二审": bool(row["是否需要二审"]),
                "审核人": row["审核人"],
            }
            for row in rows
        ]

    def _确认套装存在(self, 套装编号: str) -> None:
        if not self.数据库.查询一条("SELECT 1 FROM sticker_sets WHERE 套装编号 = ?", (套装编号,)):
            raise 业务异常("表情套装不存在", "套装不存在", 404)

    def _套装状态(self, 套装编号: str) -> str:
        row = self.数据库.查询一条("SELECT 状态 FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        return row["状态"]

    def _最新校验通过(self, 套装编号: str) -> bool:
        row = self.数据库.查询一条(
            "SELECT 是否通过 FROM validation_reports WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        return bool(row and row["是否通过"])

    def _写审核记录(
        self,
        审核人: str,
        套装编号: str,
        审核阶段: str,
        审核结论: str,
        风险标签: list[str],
        审核意见: str,
        是否需要二审: bool,
        状态: str,
    ) -> dict[str, object]:
        审核编号 = f"REV-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO review_records
            (审核编号, 套装编号, 审核阶段, 审核结论, 风险标签, 审核意见, 是否需要二审, 审核人)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                审核编号,
                套装编号,
                审核阶段,
                审核结论,
                json.dumps(风险标签, ensure_ascii=False),
                审核意见,
                int(是否需要二审),
                审核人,
            ),
        )
        self.数据库.执行("UPDATE sticker_sets SET 状态 = ? WHERE 套装编号 = ?", (状态, 套装编号))
        return {
            "审核编号": 审核编号,
            "套装编号": 套装编号,
            "审核阶段": 审核阶段,
            "审核结论": 审核结论,
            "风险标签": 风险标签,
            "审核意见": 审核意见,
            "是否需要二审": 是否需要二审,
            "状态": 状态,
        }
