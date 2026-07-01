import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class 数据库:
    def __init__(self, 数据库路径: Path) -> None:
        self.数据库路径 = 数据库路径
        self.数据库路径.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def 连接(self) -> Iterator[sqlite3.Connection]:
        连接 = sqlite3.connect(self.数据库路径)
        连接.row_factory = sqlite3.Row
        try:
            yield 连接
            连接.commit()
        except Exception:
            连接.rollback()
            raise
        finally:
            连接.close()

    def 初始化(self) -> None:
        with self.连接() as 连接:
            连接.executescript(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    操作人 TEXT NOT NULL,
                    动作 TEXT NOT NULL,
                    目标类型 TEXT NOT NULL,
                    目标编号 TEXT NOT NULL,
                    详情 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    任务编号 TEXT PRIMARY KEY,
                    任务名称 TEXT NOT NULL,
                    任务类型 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    幂等键 TEXT UNIQUE,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    定时任务编号 TEXT PRIMARY KEY,
                    任务名称 TEXT NOT NULL,
                    任务类型 TEXT NOT NULL,
                    执行周期 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    目标锁 TEXT UNIQUE,
                    配置 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scheduled_task_runs (
                    执行编号 TEXT PRIMARY KEY,
                    定时任务编号 TEXT NOT NULL,
                    执行状态 TEXT NOT NULL,
                    执行结果 TEXT NOT NULL,
                    执行人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS validation_reports (
                    报告编号 TEXT PRIMARY KEY,
                    平台名称 TEXT NOT NULL,
                    套装编号 TEXT NOT NULL,
                    是否通过 INTEGER NOT NULL,
                    错误列表 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS asset_validation_reports (
                    报告编号 TEXT PRIMARY KEY,
                    平台名称 TEXT NOT NULL,
                    套装编号 TEXT NOT NULL,
                    是否通过 INTEGER NOT NULL,
                    文件结果 TEXT NOT NULL,
                    错误列表 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sticker_acceptance_reports (
                    验收编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    是否通过 INTEGER NOT NULL,
                    验收项 TEXT NOT NULL,
                    失败项 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS platform_rule_versions (
                    版本编号 TEXT PRIMARY KEY,
                    平台名称 TEXT NOT NULL,
                    规则版本 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    规则数据 TEXT NOT NULL,
                    创建人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (平台名称, 规则版本)
                );

                CREATE TABLE IF NOT EXISTS platform_rule_change_logs (
                    变更编号 TEXT PRIMARY KEY,
                    平台名称 TEXT NOT NULL,
                    原版本 TEXT,
                    新版本 TEXT NOT NULL,
                    动作 TEXT NOT NULL,
                    原因 TEXT NOT NULL,
                    操作人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audience_profiles (
                    画像编号 TEXT PRIMARY KEY,
                    画像名称 TEXT NOT NULL UNIQUE,
                    年龄段 TEXT NOT NULL,
                    兴趣标签 TEXT NOT NULL,
                    使用场景 TEXT NOT NULL,
                    风格偏好 TEXT NOT NULL,
                    禁用内容 TEXT NOT NULL,
                    风险等级 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS hot_topics (
                    热点编号 TEXT PRIMARY KEY,
                    热点名称 TEXT NOT NULL,
                    热点来源 TEXT NOT NULL,
                    热度分 INTEGER NOT NULL,
                    生命周期 TEXT NOT NULL,
                    风险分 INTEGER NOT NULL,
                    受众匹配 TEXT NOT NULL,
                    是否允许生成 INTEGER NOT NULL,
                    风险原因 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS original_roles (
                    角色编号 TEXT PRIMARY KEY,
                    角色名称 TEXT NOT NULL UNIQUE,
                    人设 TEXT NOT NULL,
                    动作库 TEXT NOT NULL,
                    口头禅 TEXT NOT NULL,
                    风格关键词 TEXT NOT NULL,
                    可复用 INTEGER NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS generation_strategies (
                    策略编号 TEXT PRIMARY KEY,
                    策略版本 TEXT NOT NULL,
                    目标平台 TEXT NOT NULL,
                    目标受众 TEXT NOT NULL,
                    生成类型 TEXT NOT NULL,
                    表情数量 INTEGER NOT NULL,
                    策略内容 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sticker_sets (
                    套装编号 TEXT PRIMARY KEY,
                    策略编号 TEXT NOT NULL,
                    标题 TEXT NOT NULL,
                    描述 TEXT NOT NULL,
                    标签 TEXT NOT NULL,
                    目标受众 TEXT NOT NULL,
                    使用场景 TEXT NOT NULL,
                    平台适配版本 TEXT NOT NULL DEFAULT '',
                    封面图 TEXT NOT NULL DEFAULT '{}',
                    缩略图 TEXT NOT NULL DEFAULT '{}',
                    风格体系 TEXT NOT NULL DEFAULT '{}',
                    质量报告 TEXT NOT NULL DEFAULT '{}',
                    状态 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sticker_items (
                    表情编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    序号 INTEGER NOT NULL,
                    情绪标签 TEXT NOT NULL,
                    场景标签 TEXT NOT NULL,
                    文案 TEXT NOT NULL,
                    生成参数 TEXT NOT NULL,
                    文件路径 TEXT NOT NULL DEFAULT '',
                    文件大小B INTEGER NOT NULL DEFAULT 0,
                    文件指纹 TEXT NOT NULL,
                    候选数量 INTEGER NOT NULL DEFAULT 0,
                    重试次数 INTEGER NOT NULL DEFAULT 0,
                    质量报告 TEXT NOT NULL DEFAULT '{}',
                    失败原因 TEXT NOT NULL DEFAULT '[]',
                    状态 TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preview_packages (
                    预览包编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    清单 TEXT NOT NULL,
                    文件路径 TEXT NOT NULL DEFAULT '',
                    文件大小B INTEGER NOT NULL DEFAULT 0,
                    内容哈希 TEXT NOT NULL DEFAULT '',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS review_records (
                    审核编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    审核阶段 TEXT NOT NULL DEFAULT '人工审核',
                    审核结论 TEXT NOT NULL,
                    风险标签 TEXT NOT NULL,
                    审核意见 TEXT NOT NULL,
                    是否需要二审 INTEGER NOT NULL,
                    审核人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS regenerate_requests (
                    退回编号 TEXT PRIMARY KEY,
                    原套装编号 TEXT NOT NULL,
                    新策略编号 TEXT NOT NULL,
                    新套装编号 TEXT NOT NULL,
                    退回原因 TEXT NOT NULL,
                    操作人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS publish_tasks (
                    发布任务编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    发布平台 TEXT NOT NULL,
                    发布账号 TEXT NOT NULL,
                    发布方式 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    重试次数 INTEGER NOT NULL DEFAULT 0,
                    失败原因 TEXT,
                    外部发布编号 TEXT NOT NULL DEFAULT '',
                    发布回执 TEXT NOT NULL DEFAULT '{}',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS publish_prechecks (
                    复核编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    复核结论 TEXT NOT NULL,
                    复核意见 TEXT NOT NULL,
                    复核人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS publish_retry_records (
                    记录编号 TEXT PRIMARY KEY,
                    发布任务编号 TEXT NOT NULL,
                    重试序号 INTEGER NOT NULL,
                    失败原因 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS submit_packages (
                    提交包编号 TEXT PRIMARY KEY,
                    发布任务编号 TEXT NOT NULL,
                    套装编号 TEXT NOT NULL,
                    清单 TEXT NOT NULL,
                    文件路径 TEXT NOT NULL DEFAULT '',
                    文件大小B INTEGER NOT NULL DEFAULT 0,
                    内容哈希 TEXT NOT NULL DEFAULT '',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS performance_records (
                    表现编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    下载量 INTEGER NOT NULL,
                    发送量 INTEGER NOT NULL,
                    收藏量 INTEGER NOT NULL,
                    分享量 INTEGER NOT NULL,
                    收益 REAL NOT NULL,
                    标签表现 TEXT NOT NULL,
                    受众表现 TEXT NOT NULL,
                    拒审原因 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS optimization_reports (
                    报告编号 TEXT PRIMARY KEY,
                    周期 TEXT NOT NULL,
                    高表现标签 TEXT NOT NULL,
                    低表现策略 TEXT NOT NULL,
                    拒审原因回写 TEXT NOT NULL,
                    下一轮策略 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS platform_rule_feedbacks (
                    反馈编号 TEXT PRIMARY KEY,
                    报告编号 TEXT NOT NULL,
                    拒审原因 TEXT NOT NULL,
                    来源 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    处理意见 TEXT NOT NULL DEFAULT '',
                    处理人 TEXT NOT NULL DEFAULT '',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (拒审原因)
                );

                CREATE TABLE IF NOT EXISTS next_round_strategy_drafts (
                    草案编号 TEXT PRIMARY KEY,
                    报告编号 TEXT NOT NULL,
                    目标平台 TEXT NOT NULL,
                    目标受众 TEXT NOT NULL,
                    表情数量 INTEGER NOT NULL,
                    策略内容 TEXT NOT NULL,
                    状态 TEXT NOT NULL DEFAULT '草案待转正式',
                    正式策略编号 TEXT NOT NULL DEFAULT '',
                    正式套装编号 TEXT NOT NULL DEFAULT '',
                    创建人 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS loop_acceptance_reports (
                    报告编号 TEXT PRIMARY KEY,
                    验收范围 TEXT NOT NULL,
                    是否通过 INTEGER NOT NULL,
                    验收项 TEXT NOT NULL,
                    失败项 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS first_stage_gate_reports (
                    门禁编号 TEXT PRIMARY KEY,
                    LOOP报告编号 TEXT NOT NULL UNIQUE,
                    是否通过 INTEGER NOT NULL,
                    验收清单 TEXT NOT NULL,
                    失败项 TEXT NOT NULL,
                    再执行队列 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS reexecution_queue (
                    队列编号 TEXT PRIMARY KEY,
                    LOOP报告编号 TEXT NOT NULL,
                    验收项 TEXT NOT NULL,
                    失败原因 TEXT NOT NULL,
                    状态 TEXT NOT NULL,
                    领取人 TEXT NOT NULL DEFAULT '',
                    执行记录 TEXT NOT NULL DEFAULT '[]',
                    完成说明 TEXT NOT NULL DEFAULT '',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (LOOP报告编号, 验收项)
                );

                CREATE TABLE IF NOT EXISTS delivery_package_indexes (
                    包编号 TEXT PRIMARY KEY,
                    门禁编号 TEXT NOT NULL UNIQUE,
                    索引内容 TEXT NOT NULL,
                    文件路径 TEXT NOT NULL DEFAULT '',
                    文件大小B INTEGER NOT NULL DEFAULT 0,
                    内容哈希 TEXT NOT NULL DEFAULT '',
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS platform_packages (
                    包编号 TEXT PRIMARY KEY,
                    套装编号 TEXT NOT NULL,
                    平台名称 TEXT NOT NULL,
                    包类型 TEXT NOT NULL,
                    规则版本 TEXT NOT NULL,
                    文件路径 TEXT NOT NULL,
                    文件大小B INTEGER NOT NULL,
                    内容哈希 TEXT NOT NULL,
                    manifest TEXT NOT NULL,
                    下载前检查 TEXT NOT NULL,
                    创建时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            columns = [row["name"] for row in 连接.execute("PRAGMA table_info(scheduled_tasks)").fetchall()]
            if "目标锁" not in columns:
                连接.execute("ALTER TABLE scheduled_tasks ADD COLUMN 目标锁 TEXT")
            review_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(review_records)").fetchall()]
            if "审核阶段" not in review_columns:
                连接.execute("ALTER TABLE review_records ADD COLUMN 审核阶段 TEXT NOT NULL DEFAULT '人工审核'")
            feedback_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(platform_rule_feedbacks)").fetchall()]
            if "处理意见" not in feedback_columns:
                连接.execute("ALTER TABLE platform_rule_feedbacks ADD COLUMN 处理意见 TEXT NOT NULL DEFAULT ''")
            if "处理人" not in feedback_columns:
                连接.execute("ALTER TABLE platform_rule_feedbacks ADD COLUMN 处理人 TEXT NOT NULL DEFAULT ''")
            if "更新时间" not in feedback_columns:
                连接.execute("ALTER TABLE platform_rule_feedbacks ADD COLUMN 更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
            draft_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(next_round_strategy_drafts)").fetchall()]
            if "状态" not in draft_columns:
                连接.execute("ALTER TABLE next_round_strategy_drafts ADD COLUMN 状态 TEXT NOT NULL DEFAULT '草案待转正式'")
            if "正式策略编号" not in draft_columns:
                连接.execute("ALTER TABLE next_round_strategy_drafts ADD COLUMN 正式策略编号 TEXT NOT NULL DEFAULT ''")
            if "正式套装编号" not in draft_columns:
                连接.execute("ALTER TABLE next_round_strategy_drafts ADD COLUMN 正式套装编号 TEXT NOT NULL DEFAULT ''")
            if "更新时间" not in draft_columns:
                连接.execute("ALTER TABLE next_round_strategy_drafts ADD COLUMN 更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
            queue_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(reexecution_queue)").fetchall()]
            if "领取人" not in queue_columns:
                连接.execute("ALTER TABLE reexecution_queue ADD COLUMN 领取人 TEXT NOT NULL DEFAULT ''")
            if "执行记录" not in queue_columns:
                连接.execute("ALTER TABLE reexecution_queue ADD COLUMN 执行记录 TEXT NOT NULL DEFAULT '[]'")
            if "完成说明" not in queue_columns:
                连接.execute("ALTER TABLE reexecution_queue ADD COLUMN 完成说明 TEXT NOT NULL DEFAULT ''")
            if "更新时间" not in queue_columns:
                连接.execute("ALTER TABLE reexecution_queue ADD COLUMN 更新时间 TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
            package_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(delivery_package_indexes)").fetchall()]
            if "文件路径" not in package_columns:
                连接.execute("ALTER TABLE delivery_package_indexes ADD COLUMN 文件路径 TEXT NOT NULL DEFAULT ''")
            if "文件大小B" not in package_columns:
                连接.execute("ALTER TABLE delivery_package_indexes ADD COLUMN 文件大小B INTEGER NOT NULL DEFAULT 0")
            if "内容哈希" not in package_columns:
                连接.execute("ALTER TABLE delivery_package_indexes ADD COLUMN 内容哈希 TEXT NOT NULL DEFAULT ''")
            submit_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(submit_packages)").fetchall()]
            if "文件路径" not in submit_columns:
                连接.execute("ALTER TABLE submit_packages ADD COLUMN 文件路径 TEXT NOT NULL DEFAULT ''")
            if "文件大小B" not in submit_columns:
                连接.execute("ALTER TABLE submit_packages ADD COLUMN 文件大小B INTEGER NOT NULL DEFAULT 0")
            if "内容哈希" not in submit_columns:
                连接.execute("ALTER TABLE submit_packages ADD COLUMN 内容哈希 TEXT NOT NULL DEFAULT ''")
            preview_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(preview_packages)").fetchall()]
            if "文件路径" not in preview_columns:
                连接.execute("ALTER TABLE preview_packages ADD COLUMN 文件路径 TEXT NOT NULL DEFAULT ''")
            if "文件大小B" not in preview_columns:
                连接.execute("ALTER TABLE preview_packages ADD COLUMN 文件大小B INTEGER NOT NULL DEFAULT 0")
            if "内容哈希" not in preview_columns:
                连接.execute("ALTER TABLE preview_packages ADD COLUMN 内容哈希 TEXT NOT NULL DEFAULT ''")
            set_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(sticker_sets)").fetchall()]
            if "封面图" not in set_columns:
                连接.execute("ALTER TABLE sticker_sets ADD COLUMN 封面图 TEXT NOT NULL DEFAULT '{}'")
            if "缩略图" not in set_columns:
                连接.execute("ALTER TABLE sticker_sets ADD COLUMN 缩略图 TEXT NOT NULL DEFAULT '{}'")
            if "平台适配版本" not in set_columns:
                连接.execute("ALTER TABLE sticker_sets ADD COLUMN 平台适配版本 TEXT NOT NULL DEFAULT ''")
            if "风格体系" not in set_columns:
                连接.execute("ALTER TABLE sticker_sets ADD COLUMN 风格体系 TEXT NOT NULL DEFAULT '{}'")
            if "质量报告" not in set_columns:
                连接.execute("ALTER TABLE sticker_sets ADD COLUMN 质量报告 TEXT NOT NULL DEFAULT '{}'")
            item_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(sticker_items)").fetchall()]
            if "文件路径" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 文件路径 TEXT NOT NULL DEFAULT ''")
            if "文件大小B" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 文件大小B INTEGER NOT NULL DEFAULT 0")
            if "候选数量" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 候选数量 INTEGER NOT NULL DEFAULT 0")
            if "重试次数" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 重试次数 INTEGER NOT NULL DEFAULT 0")
            if "质量报告" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 质量报告 TEXT NOT NULL DEFAULT '{}'")
            if "失败原因" not in item_columns:
                连接.execute("ALTER TABLE sticker_items ADD COLUMN 失败原因 TEXT NOT NULL DEFAULT '[]'")
            publish_columns = [row["name"] for row in 连接.execute("PRAGMA table_info(publish_tasks)").fetchall()]
            if "外部发布编号" not in publish_columns:
                连接.execute("ALTER TABLE publish_tasks ADD COLUMN 外部发布编号 TEXT NOT NULL DEFAULT ''")
            if "发布回执" not in publish_columns:
                连接.execute("ALTER TABLE publish_tasks ADD COLUMN 发布回执 TEXT NOT NULL DEFAULT '{}'")

    def 执行(self, sql: str, 参数: tuple[Any, ...] = ()) -> None:
        with self.连接() as 连接:
            连接.execute(sql, 参数)

    def 查询一条(self, sql: str, 参数: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self.连接() as 连接:
            return 连接.execute(sql, 参数).fetchone()

    def 查询全部(self, sql: str, 参数: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.连接() as 连接:
            return list(连接.execute(sql, 参数).fetchall())
