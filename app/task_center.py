import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常


允许流转: dict[str, set[str]] = {
    "待创建": {"策略已生成"},
    "策略已生成": {"生成中"},
    "生成中": {"生成完成"},
    "生成完成": {"校验中"},
    "校验中": {"校验通过"},
    "校验通过": {"待审核"},
    "待审核": {"审核通过"},
    "审核通过": {"待发布"},
    "待发布": {"dry-run 通过"},
    "dry-run 通过": {"发布中"},
    "发布中": {"发布成功"},
    "发布成功": {"数据回流"},
    "数据回流": {"策略优化完成"},
    "策略优化完成": set(),
}


class 任务中心:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 创建任务(self, 操作人编号: str, 任务名称: str, 任务类型: str, 幂等键: str | None) -> dict[str, str]:
        if 幂等键:
            existing = self.数据库.查询一条("SELECT * FROM tasks WHERE 幂等键 = ?", (幂等键,))
            if existing:
                return self._转字典(existing)

        任务编号 = f"TASK-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO tasks (任务编号, 任务名称, 任务类型, 状态, 幂等键)
            VALUES (?, ?, ?, ?, ?)
            """,
            (任务编号, 任务名称, 任务类型, "待创建", 幂等键),
        )
        self.审计.记录(
            操作人编号,
            "创建任务",
            "任务",
            任务编号,
            {"任务名称": 任务名称, "任务类型": 任务类型, "状态": "待创建"},
        )
        return self.获取任务(任务编号)

    def 获取任务(self, 任务编号: str) -> dict[str, str]:
        row = self.数据库.查询一条("SELECT * FROM tasks WHERE 任务编号 = ?", (任务编号,))
        if not row:
            raise 业务异常("任务不存在", "任务不存在", 404)
        return self._转字典(row)

    def 流转任务(self, 操作人编号: str, 任务编号: str, 目标状态: str) -> dict[str, str]:
        当前任务 = self.获取任务(任务编号)
        当前状态 = 当前任务["状态"]
        if 目标状态 == 当前状态:
            return 当前任务
        if 目标状态 not in 允许流转.get(当前状态, set()):
            raise 业务异常(f"禁止从{当前状态}流转到{目标状态}", "非法状态流转", 409)

        self.数据库.执行(
            "UPDATE tasks SET 状态 = ?, 更新时间 = CURRENT_TIMESTAMP WHERE 任务编号 = ?",
            (目标状态, 任务编号),
        )
        self.审计.记录(
            操作人编号,
            "任务状态流转",
            "任务",
            任务编号,
            {"原状态": 当前状态, "目标状态": 目标状态},
        )
        return self.获取任务(任务编号)

    @staticmethod
    def _转字典(row) -> dict[str, str]:
        return {
            "任务编号": row["任务编号"],
            "任务名称": row["任务名称"],
            "任务类型": row["任务类型"],
            "状态": row["状态"],
            "幂等键": row["幂等键"],
        }
