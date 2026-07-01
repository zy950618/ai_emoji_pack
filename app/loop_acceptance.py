import hashlib
import json
import os
import uuid
from pathlib import Path

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常


class LOOP验收服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 执行(self, 操作人编号: str, 验收范围: str) -> dict[str, object]:
        checks = {
            "输入可追溯": self._存在("performance_records"),
            "处理过程可追溯": self._存在("audit_logs"),
            "输出可复核": self._存在("optimization_reports") and self._存在("next_round_strategy_drafts"),
            "失败可重试": self._存在("publish_tasks"),
            "结果可评分": self._存在评分数据(),
            "数据可回流": self._存在状态({"数据回流", "策略优化完成"}),
            "下一轮策略有变化": self._存在已转正式策略(),
        }
        failures = [{"验收项": name, "原因": "未满足"} for name, passed in checks.items() if not passed]
        passed = not failures
        report_id = f"LOOP-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO loop_acceptance_reports (报告编号, 验收范围, 是否通过, 验收项, 失败项)
            VALUES (?, ?, ?, ?, ?)
            """,
            (report_id, 验收范围, int(passed), json.dumps(checks, ensure_ascii=False), json.dumps(failures, ensure_ascii=False)),
        )
        self.审计.记录(操作人编号, "执行LOOP验收", "LOOP验收", report_id, {"验收范围": 验收范围, "是否通过": passed})
        return {"报告编号": report_id, "验收范围": 验收范围, "是否通过": passed, "验收项": checks, "失败项": failures}

    def 报告列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM loop_acceptance_reports ORDER BY 创建时间 ASC")
        return [
            {
                "报告编号": row["报告编号"],
                "验收范围": row["验收范围"],
                "是否通过": bool(row["是否通过"]),
                "验收项": json.loads(row["验收项"]),
                "失败项": json.loads(row["失败项"]),
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    def 第一阶段总门禁(self, 操作人编号: str, LOOP报告编号: str) -> dict[str, object]:
        existing = self.数据库.查询一条("SELECT * FROM first_stage_gate_reports WHERE LOOP报告编号 = ?", (LOOP报告编号,))
        if existing:
            return self._门禁报告字典(existing)

        report = self.数据库.查询一条("SELECT * FROM loop_acceptance_reports WHERE 报告编号 = ?", (LOOP报告编号,))
        if not report:
            raise 业务异常("LOOP验收报告不存在", "LOOP报告不存在", 404)

        checks = json.loads(report["验收项"])
        failures = json.loads(report["失败项"])
        checklist = [{"验收项": name, "是否通过": bool(passed)} for name, passed in checks.items()]
        queue_items = [self._写再执行队列(LOOP报告编号, item["验收项"], item["原因"]) for item in failures]
        gate_id = f"GATE-{uuid.uuid4().hex[:12]}"
        passed = bool(report["是否通过"])
        self.数据库.执行(
            """
            INSERT INTO first_stage_gate_reports (门禁编号, LOOP报告编号, 是否通过, 验收清单, 失败项, 再执行队列)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                gate_id,
                LOOP报告编号,
                int(passed),
                json.dumps(checklist, ensure_ascii=False),
                json.dumps(failures, ensure_ascii=False),
                json.dumps(queue_items, ensure_ascii=False),
            ),
        )
        self.审计.记录(操作人编号, "执行第一阶段总门禁", "第一阶段总门禁", gate_id, {"LOOP报告编号": LOOP报告编号, "是否通过": passed})
        return self._门禁报告字典(self.数据库.查询一条("SELECT * FROM first_stage_gate_reports WHERE 门禁编号 = ?", (gate_id,)))

    def 第一阶段总门禁报告列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM first_stage_gate_reports ORDER BY 创建时间 ASC")
        return [self._门禁报告字典(row) for row in rows]

    def 再执行队列列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM reexecution_queue ORDER BY 创建时间 ASC")
        return [self._队列字典(row) for row in rows]

    def 创建交付包索引(self, 操作人编号: str, 门禁编号: str) -> dict[str, object]:
        existing = self.数据库.查询一条("SELECT * FROM delivery_package_indexes WHERE 门禁编号 = ?", (门禁编号,))
        if existing:
            if not existing["文件路径"] or not Path(existing["文件路径"]).is_file():
                self._重建交付包文件(existing)
                existing = self.数据库.查询一条("SELECT * FROM delivery_package_indexes WHERE 门禁编号 = ?", (门禁编号,))
            return self._交付包字典(existing)

        gate_row = self.数据库.查询一条("SELECT * FROM first_stage_gate_reports WHERE 门禁编号 = ?", (门禁编号,))
        if not gate_row:
            raise 业务异常("第一阶段总门禁报告不存在", "门禁不存在", 404)
        gate = self._门禁报告字典(gate_row)
        loop_row = self.数据库.查询一条("SELECT * FROM loop_acceptance_reports WHERE 报告编号 = ?", (gate["LOOP报告编号"],))
        loop_report = self._LOOP报告字典(loop_row)
        original_loop_id = self._原始LOOP报告编号(loop_report["验收范围"])
        queue_loop_id = original_loop_id or gate["LOOP报告编号"]
        queues = [
            self._队列字典(row)
            for row in self.数据库.查询全部("SELECT * FROM reexecution_queue WHERE LOOP报告编号 = ? ORDER BY 创建时间 ASC", (queue_loop_id,))
        ]
        content = {
            "门禁报告": gate,
            "LOOP报告": loop_report,
            "复验报告": loop_report if original_loop_id else None,
            "原始LOOP报告编号": original_loop_id,
            "再执行记录": queues,
            "审计摘要": self._审计摘要(gate["门禁编号"], gate["LOOP报告编号"], original_loop_id, [item["队列编号"] for item in queues]),
        }
        package_id = f"PKG-{uuid.uuid4().hex[:12]}"
        file_path, file_size, content_hash = self._写交付包文件(package_id, content)
        self.数据库.执行(
            "INSERT INTO delivery_package_indexes (包编号, 门禁编号, 索引内容, 文件路径, 文件大小B, 内容哈希) VALUES (?, ?, ?, ?, ?, ?)",
            (package_id, 门禁编号, json.dumps(content, ensure_ascii=False), file_path, file_size, content_hash),
        )
        self.审计.记录(操作人编号, "创建交付包索引", "交付包索引", package_id, {"门禁编号": 门禁编号})
        return self._交付包字典(self.数据库.查询一条("SELECT * FROM delivery_package_indexes WHERE 包编号 = ?", (package_id,)))

    def 交付包索引列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM delivery_package_indexes ORDER BY 创建时间 ASC")
        return [self._交付包字典(row) for row in rows]

    def 读取交付包文件(self, 包编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM delivery_package_indexes WHERE 包编号 = ?", (包编号,))
        if not row:
            raise 业务异常("交付包不存在", "交付包不存在", 404)
        package = self._交付包字典(row)
        file_path = Path(str(package["文件路径"]))
        if not file_path.is_file():
            raise 业务异常("交付包文件不存在", "交付包文件缺失", 409)
        text = file_path.read_text(encoding="utf-8")
        self._校验无密钥泄露(text, str(file_path))
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if content_hash != package["内容哈希"]:
            raise 业务异常("交付包文件内容与索引不一致", "交付包内容不一致", 409)
        return package | {"文件内容": json.loads(text)}

    def 领取再执行项(self, 操作人编号: str, 队列编号: str) -> dict[str, object]:
        row = self._获取队列行(队列编号)
        if row["状态"] == "已完成":
            raise 业务异常("已完成的再执行项不能领取", "状态不允许", 409)
        if row["状态"] == "执行中":
            if row["领取人"] == 操作人编号:
                return self._队列字典(row)
            raise 业务异常("再执行项已被其他人领取", "领取冲突", 409)

        self.数据库.执行(
            "UPDATE reexecution_queue SET 状态 = ?, 领取人 = ?, 更新时间 = CURRENT_TIMESTAMP WHERE 队列编号 = ?",
            ("执行中", 操作人编号, 队列编号),
        )
        self.审计.记录(操作人编号, "领取再执行项", "再执行队列", 队列编号, {"验收项": row["验收项"]})
        return self._队列字典(self._获取队列行(队列编号))

    def 记录再执行(self, 操作人编号: str, 队列编号: str, 执行记录: str) -> dict[str, object]:
        row = self._获取队列行(队列编号)
        self._确认可操作队列(row, 操作人编号)
        records = json.loads(row["执行记录"])
        records.append({"操作人": 操作人编号, "执行记录": 执行记录})
        self.数据库.执行(
            "UPDATE reexecution_queue SET 执行记录 = ?, 更新时间 = CURRENT_TIMESTAMP WHERE 队列编号 = ?",
            (json.dumps(records, ensure_ascii=False), 队列编号),
        )
        self.审计.记录(操作人编号, "记录再执行过程", "再执行队列", 队列编号, {"执行记录": 执行记录})
        return self._队列字典(self._获取队列行(队列编号))

    def 完成再执行项(self, 操作人编号: str, 队列编号: str, 完成说明: str) -> dict[str, object]:
        row = self._获取队列行(队列编号)
        if row["状态"] == "已完成":
            return self._队列字典(row)
        self._确认可操作队列(row, 操作人编号)
        if not json.loads(row["执行记录"]):
            raise 业务异常("完成前必须先写入执行记录", "执行记录缺失", 409)
        self.数据库.执行(
            """
            UPDATE reexecution_queue
            SET 状态 = ?, 完成说明 = ?, 更新时间 = CURRENT_TIMESTAMP
            WHERE 队列编号 = ?
            """,
            ("已完成", 完成说明, 队列编号),
        )
        self.审计.记录(操作人编号, "完成再执行项", "再执行队列", 队列编号, {"完成说明": 完成说明})
        updated = self._队列字典(self._获取队列行(队列编号))
        updated["自动复验"] = self._完成后自动复验(操作人编号, row["LOOP报告编号"])
        return updated

    def _写再执行队列(self, LOOP报告编号: str, 验收项: str, 失败原因: str) -> dict[str, object]:
        existing = self.数据库.查询一条("SELECT * FROM reexecution_queue WHERE LOOP报告编号 = ? AND 验收项 = ?", (LOOP报告编号, 验收项))
        if existing:
            return self._队列字典(existing)
        queue_id = f"REQ-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO reexecution_queue (队列编号, LOOP报告编号, 验收项, 失败原因, 状态)
            VALUES (?, ?, ?, ?, ?)
            """,
            (queue_id, LOOP报告编号, 验收项, 失败原因, "待再执行"),
        )
        return self._队列字典(self.数据库.查询一条("SELECT * FROM reexecution_queue WHERE 队列编号 = ?", (queue_id,)))

    def _完成后自动复验(self, 操作人编号: str, LOOP报告编号: str) -> dict[str, object] | None:
        unfinished = self.数据库.查询一条(
            "SELECT 1 FROM reexecution_queue WHERE LOOP报告编号 = ? AND 状态 != ? LIMIT 1",
            (LOOP报告编号, "已完成"),
        )
        if unfinished:
            return None
        recheck = self.执行(操作人编号, f"复验:{LOOP报告编号}")
        gate = self.第一阶段总门禁(操作人编号, recheck["报告编号"])
        self.审计.记录(操作人编号, "完成后自动复验", "LOOP验收", recheck["报告编号"], {"原LOOP报告编号": LOOP报告编号, "门禁编号": gate["门禁编号"]})
        return {"LOOP验收": recheck, "第一阶段总门禁": gate}

    def _获取队列行(self, 队列编号: str):
        row = self.数据库.查询一条("SELECT * FROM reexecution_queue WHERE 队列编号 = ?", (队列编号,))
        if not row:
            raise 业务异常("再执行队列项不存在", "队列项不存在", 404)
        return row

    @staticmethod
    def _确认可操作队列(row, 操作人编号: str) -> None:
        if row["状态"] != "执行中":
            raise 业务异常("只有执行中的再执行项可以记录或完成", "状态不允许", 409)
        if row["领取人"] != 操作人编号:
            raise 业务异常("只能由领取人操作再执行项", "领取人不匹配", 409)

    @staticmethod
    def _队列字典(row) -> dict[str, object]:
        return {
            "队列编号": row["队列编号"],
            "LOOP报告编号": row["LOOP报告编号"],
            "验收项": row["验收项"],
            "失败原因": row["失败原因"],
            "状态": row["状态"],
            "领取人": row["领取人"],
            "执行记录": json.loads(row["执行记录"]),
            "完成说明": row["完成说明"],
            "创建时间": row["创建时间"],
            "更新时间": row["更新时间"],
        }

    @staticmethod
    def _门禁报告字典(row) -> dict[str, object]:
        return {
            "门禁编号": row["门禁编号"],
            "LOOP报告编号": row["LOOP报告编号"],
            "是否通过": bool(row["是否通过"]),
            "验收清单": json.loads(row["验收清单"]),
            "失败项": json.loads(row["失败项"]),
            "再执行队列": json.loads(row["再执行队列"]),
            "创建时间": row["创建时间"],
        }

    @staticmethod
    def _交付包字典(row) -> dict[str, object]:
        return {
            "包编号": row["包编号"],
            "门禁编号": row["门禁编号"],
            "索引内容": json.loads(row["索引内容"]),
            "文件路径": row["文件路径"],
            "文件大小B": row["文件大小B"],
            "内容哈希": row["内容哈希"],
            "创建时间": row["创建时间"],
        }

    def _重建交付包文件(self, row) -> None:
        file_path, file_size, content_hash = self._写交付包文件(row["包编号"], json.loads(row["索引内容"]))
        self.数据库.执行(
            "UPDATE delivery_package_indexes SET 文件路径 = ?, 文件大小B = ?, 内容哈希 = ? WHERE 包编号 = ?",
            (file_path, file_size, content_hash, row["包编号"]),
        )

    def _写交付包文件(self, 包编号: str, 内容: dict[str, object]) -> tuple[str, int, str]:
        directory = self.数据库.数据库路径.parent / "delivery_packages"
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{包编号}.json"
        text = json.dumps(内容, ensure_ascii=False, indent=2, sort_keys=True)
        self._校验无密钥泄露(text, str(file_path))
        file_path.write_text(text, encoding="utf-8")
        encoded = text.encode("utf-8")
        return str(file_path), len(encoded), hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _校验无密钥泄露(内容文本: str, 文件路径: str) -> None:
        candidates = {
            value
            for key, value in os.environ.items()
            if value and len(value) >= 8 and any(marker in key.upper() for marker in ("KEY", "SECRET", "TOKEN", "PASSWORD"))
        }
        scanned = f"{文件路径}\n{内容文本}"
        if any(secret in scanned for secret in candidates):
            raise 业务异常("交付包包含密钥风险", "密钥泄露风险", 409)

    @staticmethod
    def _原始LOOP报告编号(scope: str) -> str | None:
        prefix = "复验:"
        return scope[len(prefix) :] if scope.startswith(prefix) else None

    @staticmethod
    def _LOOP报告字典(row) -> dict[str, object]:
        return {
            "报告编号": row["报告编号"],
            "验收范围": row["验收范围"],
            "是否通过": bool(row["是否通过"]),
            "验收项": json.loads(row["验收项"]),
            "失败项": json.loads(row["失败项"]),
            "创建时间": row["创建时间"],
        }

    def _审计摘要(self, 门禁编号: str, LOOP报告编号: str, 原始LOOP报告编号: str | None, 队列编号列表: list[str]) -> list[dict[str, object]]:
        target_ids = {门禁编号, LOOP报告编号, *队列编号列表}
        if 原始LOOP报告编号:
            target_ids.add(原始LOOP报告编号)
        rows = self.数据库.查询全部("SELECT * FROM audit_logs ORDER BY id ASC")
        return [
            {
                "操作人": row["操作人"],
                "动作": row["动作"],
                "目标类型": row["目标类型"],
                "目标编号": row["目标编号"],
                "创建时间": row["创建时间"],
            }
            for row in rows
            if row["目标编号"] in target_ids
            or row["动作"] in {"完成后自动复验", "执行第一阶段总门禁", "执行LOOP验收", "领取再执行项", "记录再执行过程", "完成再执行项"}
        ]

    def _存在(self, table_name: str) -> bool:
        row = self.数据库.查询一条(f"SELECT 1 FROM {table_name} LIMIT 1")
        return bool(row)

    def _存在评分数据(self) -> bool:
        row = self.数据库.查询一条("SELECT 标签表现, 受众表现 FROM performance_records LIMIT 1")
        return bool(row and json.loads(row["标签表现"]) and json.loads(row["受众表现"]))

    def _存在状态(self, statuses: set[str]) -> bool:
        rows = self.数据库.查询全部("SELECT 状态 FROM sticker_sets")
        return any(row["状态"] in statuses for row in rows)

    def _存在已转正式策略(self) -> bool:
        row = self.数据库.查询一条("SELECT 1 FROM next_round_strategy_drafts WHERE 状态 = ? LIMIT 1", ("已转正式策略",))
        return bool(row)
