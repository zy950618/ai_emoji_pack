import json
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.schemas import 创建生成策略请求, 创建下一轮策略请求, 创建优化周报请求, 处理规则反馈请求, 记录表现请求, 转正式策略请求


允许反馈流转 = {
    "待规则评审": {"评审中", "已关闭"},
    "评审中": {"已采纳", "已关闭"},
}


class 数据回流服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 记录表现(self, 操作人编号: str, 请求: 记录表现请求) -> dict[str, object]:
        self._确认已发布(请求.套装编号)
        表现编号 = f"PERF-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO performance_records
            (表现编号, 套装编号, 下载量, 发送量, 收藏量, 分享量, 收益, 标签表现, 受众表现, 拒审原因)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                表现编号,
                请求.套装编号,
                请求.下载量,
                请求.发送量,
                请求.收藏量,
                请求.分享量,
                请求.收益,
                json.dumps(请求.标签表现, ensure_ascii=False),
                json.dumps(请求.受众表现, ensure_ascii=False),
                json.dumps(请求.拒审原因, ensure_ascii=False),
            ),
        )
        self.审计.记录(操作人编号, "记录表现数据", "套装", 请求.套装编号, {"表现编号": 表现编号})
        self.数据库.执行("UPDATE sticker_sets SET 状态 = ? WHERE 套装编号 = ?", ("数据回流", 请求.套装编号))
        self.审计.记录(操作人编号, "标记数据回流", "套装", 请求.套装编号, {"表现编号": 表现编号})
        return {
            "表现编号": 表现编号,
            "套装编号": 请求.套装编号,
            "下载量": 请求.下载量,
            "发送量": 请求.发送量,
            "收藏量": 请求.收藏量,
            "分享量": 请求.分享量,
            "收益": 请求.收益,
            "标签表现": 请求.标签表现,
            "受众表现": 请求.受众表现,
            "拒审原因": 请求.拒审原因,
        }

    def 创建周报(self, 操作人编号: str, 请求: 创建优化周报请求) -> dict[str, object]:
        records = self._全部表现()
        if not records:
            raise 业务异常("没有表现数据，不能生成周报", "数据不足", 409)

        tag_scores: dict[str, int] = {}
        reject_reasons: list[str] = []
        for record in records:
            for tag, score in record["标签表现"].items():
                tag_scores[tag] = tag_scores.get(tag, 0) + int(score)
            reject_reasons.extend(record["拒审原因"])

        高表现标签 = sorted([tag for tag, score in tag_scores.items() if score >= 80])
        低表现策略 = sorted([tag for tag, score in tag_scores.items() if score < 30])
        拒审原因回写 = sorted(set(reject_reasons))
        下一轮策略 = {
            "加权标签": 高表现标签,
            "降权策略": 低表现策略,
            "规则库回写": 拒审原因回写,
            "历史数据来源": [record["表现编号"] for record in records],
        }
        报告编号 = f"RPT-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO optimization_reports
            (报告编号, 周期, 高表现标签, 低表现策略, 拒审原因回写, 下一轮策略)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                报告编号,
                请求.周期,
                json.dumps(高表现标签, ensure_ascii=False),
                json.dumps(低表现策略, ensure_ascii=False),
                json.dumps(拒审原因回写, ensure_ascii=False),
                json.dumps(下一轮策略, ensure_ascii=False),
            ),
        )
        self._回写规则反馈(报告编号, 拒审原因回写)
        self.审计.记录(操作人编号, "生成优化周报", "优化周报", 报告编号, {"周期": 请求.周期})
        return {
            "报告编号": 报告编号,
            "周期": 请求.周期,
            "高表现标签": 高表现标签,
            "低表现策略": 低表现策略,
            "拒审原因回写": 拒审原因回写,
            "下一轮策略": 下一轮策略,
        }

    def 规则反馈列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM platform_rule_feedbacks ORDER BY 创建时间 ASC")
        return [dict(row) for row in rows]

    def 处理规则反馈(self, 操作人编号: str, 请求: 处理规则反馈请求) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM platform_rule_feedbacks WHERE 反馈编号 = ?", (请求.反馈编号,))
        if not row:
            raise 业务异常("规则反馈不存在", "反馈不存在", 404)
        当前状态 = row["状态"]
        if 请求.目标状态 not in 允许反馈流转.get(当前状态, set()):
            raise 业务异常("规则反馈状态不允许这样流转", "非法反馈流转", 409)

        self.数据库.执行(
            """
            UPDATE platform_rule_feedbacks
            SET 状态 = ?, 处理意见 = ?, 处理人 = ?, 更新时间 = CURRENT_TIMESTAMP
            WHERE 反馈编号 = ?
            """,
            (请求.目标状态, 请求.处理意见, 操作人编号, 请求.反馈编号),
        )
        self.审计.记录(
            操作人编号,
            "处理规则反馈",
            "规则反馈",
            请求.反馈编号,
            {"原状态": 当前状态, "目标状态": 请求.目标状态, "拒审原因": row["拒审原因"]},
        )
        updated = self.数据库.查询一条("SELECT * FROM platform_rule_feedbacks WHERE 反馈编号 = ?", (请求.反馈编号,))
        return dict(updated)

    def 周报列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM optimization_reports ORDER BY 创建时间 ASC")
        return [
            {
                "报告编号": row["报告编号"],
                "周期": row["周期"],
                "高表现标签": json.loads(row["高表现标签"]),
                "低表现策略": json.loads(row["低表现策略"]),
                "拒审原因回写": json.loads(row["拒审原因回写"]),
                "下一轮策略": json.loads(row["下一轮策略"]),
            }
            for row in rows
        ]

    def 创建下一轮策略(self, 操作人编号: str, 请求: 创建下一轮策略请求) -> dict[str, object]:
        report = self.数据库.查询一条("SELECT * FROM optimization_reports WHERE 报告编号 = ?", (请求.报告编号,))
        if not report:
            raise 业务异常("优化周报不存在，不能创建下一轮策略", "周报不存在", 404)

        strategy = json.loads(report["下一轮策略"])
        history_sources = strategy.get("历史数据来源", [])
        if not history_sources:
            raise 业务异常("下一轮策略缺少历史数据来源", "历史数据缺失", 409)

        boosted_tags = set(strategy.get("加权标签", []))
        lowered_tags = set(strategy.get("降权策略", []))
        风格标签 = sorted((set(请求.基础风格标签) - lowered_tags) | boosted_tags)
        策略内容 = {
            "来源报告": 请求.报告编号,
            "历史数据来源": history_sources,
            "目标平台": 请求.目标平台,
            "目标受众": 请求.目标受众,
            "表情数量": 请求.表情数量,
            "风格标签": 风格标签,
            "情绪标签": 请求.情绪标签,
            "场景标签": 请求.场景标签,
            "策略变化": {
                "加权标签": sorted(boosted_tags),
                "降权策略": sorted(lowered_tags),
            },
        }
        existing = self.数据库.查询一条(
            """
            SELECT * FROM next_round_strategy_drafts
            WHERE 报告编号 = ? AND 目标平台 = ? AND 目标受众 = ? AND 表情数量 = ?
            ORDER BY 创建时间 ASC LIMIT 1
            """,
            (请求.报告编号, 请求.目标平台, 请求.目标受众, 请求.表情数量),
        )
        if existing:
            return {"草案编号": existing["草案编号"], **json.loads(existing["策略内容"])}

        草案编号 = f"NRS-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO next_round_strategy_drafts
            (草案编号, 报告编号, 目标平台, 目标受众, 表情数量, 策略内容, 创建人)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (草案编号, 请求.报告编号, 请求.目标平台, 请求.目标受众, 请求.表情数量, json.dumps(策略内容, ensure_ascii=False), 操作人编号),
        )
        self.审计.记录(操作人编号, "创建下一轮策略草案", "下一轮策略", 草案编号, {"报告编号": 请求.报告编号, "历史数据来源": history_sources})
        return {"草案编号": 草案编号, **策略内容}

    def 准备草案转正式(self, 请求: 转正式策略请求) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM next_round_strategy_drafts WHERE 草案编号 = ?", (请求.草案编号,))
        if not row:
            raise 业务异常("下一轮策略草案不存在", "草案不存在", 404)
        strategy = json.loads(row["策略内容"])
        source_set_ids = self._来源套装编号(strategy["历史数据来源"])
        if row["状态"] == "已转正式策略":
            return {
                "是否已转正式": True,
                "草案编号": row["草案编号"],
                "状态": row["状态"],
                "正式策略编号": row["正式策略编号"],
                "正式套装编号": row["正式套装编号"],
                "来源套装编号": source_set_ids,
            }

        return {
            "是否已转正式": False,
            "草案编号": row["草案编号"],
            "来源套装编号": source_set_ids,
            "生成请求": 创建生成策略请求(
                目标平台=strategy["目标平台"],
                目标受众=strategy["目标受众"],
                生成类型=请求.生成类型,
                表情数量=int(strategy["表情数量"]),
                风格标签=strategy["风格标签"],
                情绪标签=strategy["情绪标签"],
                场景标签=strategy["场景标签"],
                风险阈值=请求.风险阈值,
            ),
        }

    def 完成草案转正式(self, 操作人编号: str, 草案编号: str, 策略结果: dict[str, object]) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM next_round_strategy_drafts WHERE 草案编号 = ?", (草案编号,))
        if not row:
            raise 业务异常("下一轮策略草案不存在", "草案不存在", 404)
        strategy = json.loads(row["策略内容"])
        source_set_ids = self._来源套装编号(strategy["历史数据来源"])
        new_set_id = 策略结果["套装"]["套装编号"]
        self.数据库.执行(
            """
            UPDATE next_round_strategy_drafts
            SET 状态 = ?, 正式策略编号 = ?, 正式套装编号 = ?, 更新时间 = CURRENT_TIMESTAMP
            WHERE 草案编号 = ?
            """,
            ("已转正式策略", 策略结果["策略编号"], new_set_id, 草案编号),
        )
        for set_id in source_set_ids:
            self.数据库.执行("UPDATE sticker_sets SET 状态 = ? WHERE 套装编号 = ?", ("策略优化完成", set_id))
            self.审计.记录(操作人编号, "标记策略优化完成", "套装", set_id, {"草案编号": 草案编号, "正式策略编号": 策略结果["策略编号"]})
        self.审计.记录(操作人编号, "转正式生成策略", "下一轮策略", 草案编号, {"正式策略编号": 策略结果["策略编号"], "正式套装编号": new_set_id})
        return {
            "草案编号": 草案编号,
            "状态": "已转正式策略",
            "正式策略编号": 策略结果["策略编号"],
            "正式套装编号": new_set_id,
            "来源套装编号": source_set_ids,
            "正式策略": 策略结果,
        }

    def 下一轮策略列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM next_round_strategy_drafts ORDER BY 创建时间 ASC")
        return [
            {
                "草案编号": row["草案编号"],
                "报告编号": row["报告编号"],
                "目标平台": row["目标平台"],
                "目标受众": row["目标受众"],
                "表情数量": row["表情数量"],
                "策略内容": json.loads(row["策略内容"]),
                "状态": row["状态"],
                "正式策略编号": row["正式策略编号"],
                "正式套装编号": row["正式套装编号"],
                "创建人": row["创建人"],
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    def _回写规则反馈(self, 报告编号: str, 拒审原因列表: list[str]) -> None:
        for reason in 拒审原因列表:
            exists = self.数据库.查询一条("SELECT 1 FROM platform_rule_feedbacks WHERE 拒审原因 = ?", (reason,))
            if exists:
                continue
            self.数据库.执行(
                """
                INSERT INTO platform_rule_feedbacks (反馈编号, 报告编号, 拒审原因, 来源, 状态)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"FBK-{uuid.uuid4().hex[:12]}", 报告编号, reason, "优化周报", "待规则评审"),
            )

    def _确认已发布(self, 套装编号: str) -> None:
        row = self.数据库.查询一条("SELECT 状态 FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        if row["状态"] not in {"发布成功", "数据回流", "策略优化完成"}:
            raise 业务异常("只有发布成功的套装才能写入表现数据", "未发布", 409)

    def _来源套装编号(self, 表现编号列表: list[str]) -> list[str]:
        source_set_ids: list[str] = []
        for performance_id in 表现编号列表:
            row = self.数据库.查询一条("SELECT 套装编号 FROM performance_records WHERE 表现编号 = ?", (performance_id,))
            if row and row["套装编号"] not in source_set_ids:
                source_set_ids.append(row["套装编号"])
        if not source_set_ids:
            raise 业务异常("下一轮策略缺少可追溯的来源套装", "历史数据缺失", 409)
        return source_set_ids

    def _全部表现(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM performance_records ORDER BY 创建时间 ASC")
        return [
            {
                "表现编号": row["表现编号"],
                "套装编号": row["套装编号"],
                "标签表现": json.loads(row["标签表现"]),
                "受众表现": json.loads(row["受众表现"]),
                "拒审原因": json.loads(row["拒审原因"]),
            }
            for row in rows
        ]
