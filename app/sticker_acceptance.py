import json
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常


class 表情套装验收服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 验收(self, 操作人编号: str, 套装编号: str) -> dict[str, object]:
        set_row = self.数据库.查询一条("SELECT * FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        item_rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))

        emotions = {row["情绪标签"] for row in item_rows}
        scenes = {row["场景标签"] for row in item_rows}
        latest_validation = self.数据库.查询一条(
            "SELECT 是否通过 FROM validation_reports WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        latest_asset = self.数据库.查询一条(
            "SELECT 是否通过 FROM asset_validation_reports WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        latest_review = self.数据库.查询一条(
            "SELECT 审核结论 FROM review_records WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        latest_precheck = self.数据库.查询一条(
            "SELECT 复核结论 FROM publish_prechecks WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )

        checks = {
            "套装存在": True,
            "标题存在": bool(set_row["标题"]),
            "描述存在": bool(set_row["描述"]),
            "标签存在": bool(json.loads(set_row["标签"])),
            "目标受众存在": bool(set_row["目标受众"]),
            "平台适配版本存在": bool(set_row["平台适配版本"]),
            "封面图存在": bool(json.loads(set_row["封面图"])),
            "缩略图存在": bool(json.loads(set_row["缩略图"])),
            "使用场景不少于6个": len(scenes) >= 6,
            "情绪标签不少于6个": len(emotions) >= 6,
            "每张表情有指纹": all(bool(row["文件指纹"]) for row in item_rows),
            "每张表情有生成参数": all(bool(row["生成参数"]) for row in item_rows),
            "平台规格校验通过": bool(latest_validation and latest_validation["是否通过"]),
            "资产文件校验通过": bool(latest_asset and latest_asset["是否通过"]),
            "人工审核通过": bool(latest_review and latest_review["审核结论"] == "通过"),
            "发布前复核通过": bool(latest_precheck and latest_precheck["复核结论"] == "通过"),
        }
        failures = [{"验收项": name, "原因": "未满足"} for name, passed in checks.items() if not passed]
        passed = not failures
        验收编号 = f"ACC-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO sticker_acceptance_reports (验收编号, 套装编号, 是否通过, 验收项, 失败项)
            VALUES (?, ?, ?, ?, ?)
            """,
            (验收编号, 套装编号, int(passed), json.dumps(checks, ensure_ascii=False), json.dumps(failures, ensure_ascii=False)),
        )
        self.审计.记录(操作人编号, "表情套装综合验收", "套装", 套装编号, {"验收编号": 验收编号, "是否通过": passed})
        return {
            "验收编号": 验收编号,
            "套装编号": 套装编号,
            "是否通过": passed,
            "验收项": checks,
            "失败项": failures,
        }

    def 报告列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM sticker_acceptance_reports ORDER BY 创建时间 ASC")
        return [
            {
                "验收编号": row["验收编号"],
                "套装编号": row["套装编号"],
                "是否通过": bool(row["是否通过"]),
                "验收项": json.loads(row["验收项"]),
                "失败项": json.loads(row["失败项"]),
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]
