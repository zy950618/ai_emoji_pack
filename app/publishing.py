import hashlib
import json
import os
import uuid
from pathlib import Path

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.platform_publishers import 开放发布适配器
from app.schemas import 创建发布任务请求


最大重试次数 = 3


class 发布服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计
        self.开放发布 = 开放发布适配器()

    def 创建任务(self, 操作人编号: str, 请求: 创建发布任务请求) -> dict[str, object]:
        if 请求.是否真实发布:
            raise 业务异常("创建发布任务阶段只能创建 dry-run 任务", "真实发布拦截", 409)
        self._确认可发布(请求.套装编号)
        if not self._最新发布前复核通过(请求.套装编号):
            raise 业务异常("发布前复核未通过，不能创建发布任务", "发布前复核未通过", 409)
        发布任务编号 = f"PUB-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO publish_tasks
            (发布任务编号, 套装编号, 发布平台, 发布账号, 发布方式, 状态)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (发布任务编号, 请求.套装编号, 请求.发布平台, 请求.发布账号, 请求.发布方式, "待发布"),
        )
        self.审计.记录(操作人编号, "创建发布任务", "发布任务", 发布任务编号, {"套装编号": 请求.套装编号, "发布平台": 请求.发布平台})
        return self._获取任务(发布任务编号)

    def 发布前复核(self, 操作人编号: str, 套装编号: str, 复核结论: str, 复核意见: str) -> dict[str, object]:
        self._确认可发布(套装编号)
        复核编号 = f"PRECHK-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO publish_prechecks (复核编号, 套装编号, 复核结论, 复核意见, 复核人)
            VALUES (?, ?, ?, ?, ?)
            """,
            (复核编号, 套装编号, 复核结论, 复核意见, 操作人编号),
        )
        self.审计.记录(操作人编号, "发布前复核", "套装", 套装编号, {"复核编号": 复核编号, "复核结论": 复核结论})
        return {
            "复核编号": 复核编号,
            "套装编号": 套装编号,
            "复核结论": 复核结论,
            "复核意见": 复核意见,
            "是否通过": 复核结论 == "通过",
        }

    def 执行(self, 操作人编号: str, 发布任务编号: str, 确认真实发布: bool) -> dict[str, object]:
        任务 = self._获取任务(发布任务编号)
        if 任务["状态"] == "发布成功":
            return 任务
        self._确认可发布(任务["套装编号"])
        if not 确认真实发布:
            return self._执行dry_run(操作人编号, 任务)
        if 任务["状态"] not in {"dry-run 通过", "发布失败"}:
            raise 业务异常("真实发布前必须先通过 dry-run", "dry-run未通过", 409)
        if int(任务["重试次数"]) >= 最大重试次数:
            raise 业务异常("发布失败重试次数已达上限", "重试次数超限", 409)
        key = os.getenv("AI_EMOJI_OPEN_PUBLISH_KEY")
        self.审计.记录(操作人编号, "读取发布密钥", "发布任务", 发布任务编号, {"发布平台": 任务["发布平台"], "密钥用途": "开放发布回执"})
        if not key:
            self._标记失败(发布任务编号, "缺少开放发布密钥")
            raise 业务异常("真实发布缺少开放发布密钥", "密钥缺失", 409)

        submit_package = self._获取提交包(发布任务编号)
        try:
            receipt = self.开放发布.发布(str(任务["发布平台"]), str(任务["发布账号"]), submit_package)
        except 业务异常 as exc:
            self._标记失败(发布任务编号, exc.消息)
            raise

        self.数据库.执行(
            "UPDATE publish_tasks SET 状态 = ?, 外部发布编号 = ?, 发布回执 = ?, 更新时间 = CURRENT_TIMESTAMP WHERE 发布任务编号 = ?",
            ("发布成功", receipt["外部发布编号"], json.dumps(receipt, ensure_ascii=False), 发布任务编号),
        )
        self.数据库.执行("UPDATE sticker_sets SET 状态 = ? WHERE 套装编号 = ?", ("发布成功", 任务["套装编号"]))
        self.审计.记录(操作人编号, "真实发布成功", "发布任务", 发布任务编号, {"发布平台": 任务["发布平台"], "外部发布编号": receipt["外部发布编号"], "是否访问外网": False})
        return self._获取任务(发布任务编号)

    def 列表(self) -> list[dict[str, object]]:
        return [self._转任务(row) for row in self.数据库.查询全部("SELECT * FROM publish_tasks ORDER BY 创建时间 ASC")]

    def 复核列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM publish_prechecks ORDER BY 创建时间 ASC")
        return [
            {
                "复核编号": row["复核编号"],
                "套装编号": row["套装编号"],
                "复核结论": row["复核结论"],
                "复核意见": row["复核意见"],
                "复核人": row["复核人"],
            }
            for row in rows
        ]

    def 提交包列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM submit_packages ORDER BY 创建时间 ASC")
        return [self._提交包字典(row) for row in rows]

    def 重试记录列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM publish_retry_records ORDER BY 创建时间 ASC")
        return [
            {
                "记录编号": row["记录编号"],
                "发布任务编号": row["发布任务编号"],
                "重试序号": row["重试序号"],
                "失败原因": row["失败原因"],
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    def 读取提交包文件(self, 提交包编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM submit_packages WHERE 提交包编号 = ?", (提交包编号,))
        if not row:
            raise 业务异常("提交包不存在", "提交包不存在", 404)
        package = self._提交包字典(row)
        file_path = Path(str(package["文件路径"]))
        if not file_path.is_file():
            raise 业务异常("提交包文件不存在", "提交包文件缺失", 409)
        text = file_path.read_text(encoding="utf-8")
        self._校验无密钥泄露(text, str(file_path))
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != package["内容哈希"]:
            raise 业务异常("提交包文件内容与索引不一致", "提交包内容不一致", 409)
        return package | {"文件内容": json.loads(text)}

    def _执行dry_run(self, 操作人编号: str, 任务: dict[str, object]) -> dict[str, object]:
        发布任务编号 = str(任务["发布任务编号"])
        套装编号 = str(任务["套装编号"])
        existing = self.数据库.查询一条("SELECT * FROM submit_packages WHERE 发布任务编号 = ? ORDER BY 创建时间 ASC LIMIT 1", (发布任务编号,))
        if existing:
            if not existing["文件路径"] or not Path(existing["文件路径"]).is_file():
                self._重建提交包文件(existing)
                existing = self.数据库.查询一条("SELECT * FROM submit_packages WHERE 提交包编号 = ?", (existing["提交包编号"],))
            result = self._获取任务(发布任务编号)
            result["提交包编号"] = existing["提交包编号"]
            result["提交包文件路径"] = existing["文件路径"]
            result["提交包内容哈希"] = existing["内容哈希"]
            return result
        提交包编号 = f"SUB-{uuid.uuid4().hex[:12]}"
        清单 = {"套装编号": 套装编号, "发布任务编号": 发布任务编号, "发布平台": 任务["发布平台"]}
        file_path, file_size, content_hash = self._写提交包文件(提交包编号, 清单)
        self.数据库.执行(
            "INSERT INTO submit_packages (提交包编号, 发布任务编号, 套装编号, 清单, 文件路径, 文件大小B, 内容哈希) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (提交包编号, 发布任务编号, 套装编号, json.dumps(清单, ensure_ascii=False), file_path, file_size, content_hash),
        )
        self.数据库.执行("UPDATE publish_tasks SET 状态 = ?, 更新时间 = CURRENT_TIMESTAMP WHERE 发布任务编号 = ?", ("dry-run 通过", 发布任务编号))
        self.审计.记录(操作人编号, "发布dry-run通过", "发布任务", 发布任务编号, {"提交包编号": 提交包编号})
        result = self._获取任务(发布任务编号)
        result["提交包编号"] = 提交包编号
        result["提交包文件路径"] = file_path
        result["提交包内容哈希"] = content_hash
        return result

    def _确认可发布(self, 套装编号: str) -> None:
        set_row = self.数据库.查询一条("SELECT 状态 FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        if not self._最新校验通过(套装编号):
            raise 业务异常("平台规则未通过，不能发布", "校验未通过", 409)
        if set_row["状态"] not in {"审核通过", "发布成功"}:
            raise 业务异常("审核未通过，不能发布", "审核未通过", 409)

    def _最新校验通过(self, 套装编号: str) -> bool:
        row = self.数据库.查询一条(
            "SELECT 是否通过 FROM validation_reports WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        return bool(row and row["是否通过"])

    def _最新发布前复核通过(self, 套装编号: str) -> bool:
        row = self.数据库.查询一条(
            "SELECT 复核结论 FROM publish_prechecks WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号,),
        )
        return bool(row and row["复核结论"] == "通过")

    def _获取任务(self, 发布任务编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM publish_tasks WHERE 发布任务编号 = ?", (发布任务编号,))
        if not row:
            raise 业务异常("发布任务不存在", "发布任务不存在", 404)
        return self._转任务(row)

    def _获取提交包(self, 发布任务编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM submit_packages WHERE 发布任务编号 = ? ORDER BY 创建时间 ASC LIMIT 1", (发布任务编号,))
        if not row:
            raise 业务异常("真实发布缺少 dry-run 提交包", "提交包缺失", 409)
        return self._提交包字典(row)

    def _标记失败(self, 发布任务编号: str, 失败原因: str) -> None:
        任务 = self._获取任务(发布任务编号)
        重试序号 = int(任务["重试次数"]) + 1
        self.数据库.执行(
            """
            UPDATE publish_tasks
            SET 状态 = ?, 失败原因 = ?, 重试次数 = 重试次数 + 1, 更新时间 = CURRENT_TIMESTAMP
            WHERE 发布任务编号 = ?
            """,
            ("发布失败", 失败原因, 发布任务编号),
        )
        self.数据库.执行(
            "INSERT INTO publish_retry_records (记录编号, 发布任务编号, 重试序号, 失败原因) VALUES (?, ?, ?, ?)",
            (f"RETRY-{uuid.uuid4().hex[:12]}", 发布任务编号, 重试序号, 失败原因),
        )

    def _重建提交包文件(self, row) -> None:
        file_path, file_size, content_hash = self._写提交包文件(row["提交包编号"], json.loads(row["清单"]))
        self.数据库.执行(
            "UPDATE submit_packages SET 文件路径 = ?, 文件大小B = ?, 内容哈希 = ? WHERE 提交包编号 = ?",
            (file_path, file_size, content_hash, row["提交包编号"]),
        )

    def _写提交包文件(self, 提交包编号: str, 清单: dict[str, object]) -> tuple[str, int, str]:
        directory = self.数据库.数据库路径.parent / "submit_packages"
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{提交包编号}.json"
        text = json.dumps(清单, ensure_ascii=False, indent=2, sort_keys=True)
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
            raise 业务异常("提交包包含密钥风险", "密钥泄露风险", 409)

    @staticmethod
    def _转任务(row) -> dict[str, object]:
        return {
            "发布任务编号": row["发布任务编号"],
            "套装编号": row["套装编号"],
            "发布平台": row["发布平台"],
            "发布账号": row["发布账号"],
            "发布方式": row["发布方式"],
            "状态": row["状态"],
            "重试次数": row["重试次数"],
            "失败原因": row["失败原因"],
            "外部发布编号": row["外部发布编号"],
            "发布回执": json.loads(row["发布回执"]),
        }

    @staticmethod
    def _提交包字典(row) -> dict[str, object]:
        return {
            "提交包编号": row["提交包编号"],
            "发布任务编号": row["发布任务编号"],
            "套装编号": row["套装编号"],
            "清单": json.loads(row["清单"]),
            "文件路径": row["文件路径"],
            "文件大小B": row["文件大小B"],
            "内容哈希": row["内容哈希"],
            "创建时间": row["创建时间"],
        }
