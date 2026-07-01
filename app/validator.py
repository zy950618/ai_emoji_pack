import json
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.rule_governance import 平台规则治理服务
from app.schemas import 表情文件描述


class 规格校验器:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务, 规则治理: 平台规则治理服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计
        self.规则治理 = 规则治理

    def 校验(
        self,
        操作人编号: str,
        平台名称: str,
        套装编号: str,
        表情文件: list[表情文件描述],
    ) -> dict[str, object]:
        规则 = self.规则治理.获取当前规则(平台名称)
        错误列表: list[dict[str, object]] = []

        数量 = len(表情文件)
        if 数量 < 规则.最少数量 or 数量 > 规则.最多数量:
            错误列表.append(
                {
                    "文件名": "套装",
                    "规则": "套装数量",
                    "错误": f"当前数量{数量}不在{规则.最少数量}-{规则.最多数量}范围内",
                    "修复建议": "调整表情数量后重新校验",
                }
            )

        for 文件 in 表情文件:
            self._校验单文件(规则, 文件, 错误列表)

        报告编号 = f"VAL-{uuid.uuid4().hex[:12]}"
        是否通过 = not 错误列表
        self.数据库.执行(
            """
            INSERT INTO validation_reports (报告编号, 平台名称, 套装编号, 是否通过, 错误列表)
            VALUES (?, ?, ?, ?, ?)
            """,
            (报告编号, 平台名称, 套装编号, int(是否通过), json.dumps(错误列表, ensure_ascii=False)),
        )
        self.审计.记录(
            操作人编号,
            "平台规则校验",
            "套装",
            套装编号,
            {"平台名称": 平台名称, "报告编号": 报告编号, "是否通过": 是否通过},
        )
        return {
            "报告编号": 报告编号,
            "平台名称": 平台名称,
            "套装编号": 套装编号,
            "规则版本": 规则.规则版本,
            "是否通过": 是否通过,
            "错误列表": 错误列表,
            "需要人工复核": 规则.需要人工复核,
        }

    def 报告列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM validation_reports ORDER BY 创建时间 ASC")
        return [
            {
                "报告编号": row["报告编号"],
                "平台名称": row["平台名称"],
                "套装编号": row["套装编号"],
                "是否通过": bool(row["是否通过"]),
                "错误列表": json.loads(row["错误列表"]),
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    @staticmethod
    def _校验单文件(规则, 文件: 表情文件描述, 错误列表: list[dict[str, object]]) -> None:
        if 文件.宽度 != 规则.宽度 or 文件.高度 != 规则.高度:
            错误列表.append(
                {
                    "文件名": 文件.文件名,
                    "规则": "尺寸",
                    "错误": f"当前尺寸{文件.宽度}x{文件.高度}，要求{规则.宽度}x{规则.高度}",
                    "修复建议": "按目标平台尺寸重新导出",
                }
            )
        if 文件.格式.upper() not in 规则.允许格式:
            错误列表.append(
                {
                    "文件名": 文件.文件名,
                    "规则": "格式",
                    "错误": f"当前格式{文件.格式}不在允许格式内",
                    "修复建议": f"转换为{','.join(规则.允许格式)}",
                }
            )
        if 文件.文件大小KB > 规则.最大文件大小KB:
            错误列表.append(
                {
                    "文件名": 文件.文件名,
                    "规则": "文件大小",
                    "错误": f"当前{文件.文件大小KB}KB超过{规则.最大文件大小KB}KB",
                    "修复建议": "压缩文件后重新校验",
                }
            )
        if 规则.要求透明背景 and not 文件.是否透明背景:
            错误列表.append(
                {
                    "文件名": 文件.文件名,
                    "规则": "透明背景",
                    "错误": "目标平台要求透明背景",
                    "修复建议": "导出透明背景版本",
                }
            )
