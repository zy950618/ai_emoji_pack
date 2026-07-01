import json
import uuid
from typing import Any

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常


允许执行周期 = {"每小时", "每天", "每周", "手动"}


class 定时任务服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 创建(self, 操作人编号: str, 请求数据: dict[str, Any]) -> dict[str, Any]:
        if 请求数据["执行周期"] not in 允许执行周期:
            raise 业务异常("执行周期不合法", "参数错误", 422)
        if 请求数据["是否自动发布"]:
            raise 业务异常("第一阶段定时任务不能自动发布", "发布拦截", 409)

        目标锁 = self._目标锁(请求数据)
        exists = self.数据库.查询一条("SELECT 定时任务编号 FROM scheduled_tasks WHERE 目标锁 = ?", (目标锁,))
        if exists:
            raise 业务异常("同一目标的定时任务已存在", "任务锁冲突", 409)

        定时任务编号 = f"SCH-{uuid.uuid4().hex[:12]}"
        配置 = json.dumps(请求数据, ensure_ascii=False)
        self.数据库.执行(
            """
            INSERT INTO scheduled_tasks (定时任务编号, 任务名称, 任务类型, 执行周期, 状态, 目标锁, 配置)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                定时任务编号,
                请求数据["任务名称"],
                请求数据["任务类型"],
                请求数据["执行周期"],
                "已创建",
                目标锁,
                配置,
            ),
        )
        self.审计.记录(
            操作人编号,
            "创建定时任务",
            "定时任务",
            定时任务编号,
            {"执行周期": 请求数据["执行周期"], "状态": "已创建", "目标锁": 目标锁},
        )
        return {
            "定时任务编号": 定时任务编号,
            "任务名称": 请求数据["任务名称"],
            "任务类型": 请求数据["任务类型"],
            "执行周期": 请求数据["执行周期"],
            "目标锁": 目标锁,
            "状态": "已创建",
        }

    def 列表(self) -> list[dict[str, Any]]:
        rows = self.数据库.查询全部("SELECT * FROM scheduled_tasks ORDER BY 创建时间 DESC")
        return [self._转字典(row) for row in rows]

    def 执行待运行(self, 操作人编号: str, 定时任务编号: str | None = None) -> dict[str, Any]:
        if 定时任务编号:
            rows = self.数据库.查询全部("SELECT * FROM scheduled_tasks WHERE 定时任务编号 = ?", (定时任务编号,))
        else:
            rows = self.数据库.查询全部("SELECT * FROM scheduled_tasks WHERE 状态 IN (?, ?) ORDER BY 创建时间 ASC", ("已创建", "上次执行完成"))
        if 定时任务编号 and not rows:
            raise 业务异常("定时任务不存在", "定时任务不存在", 404)

        executed = []
        for row in rows:
            result = self._执行单个任务(操作人编号, row)
            executed.append(result)
        return {"执行数量": len(executed), "执行记录": executed}

    def 执行记录列表(self) -> list[dict[str, Any]]:
        rows = self.数据库.查询全部("SELECT * FROM scheduled_task_runs ORDER BY 创建时间 DESC")
        return [
            {
                "执行编号": row["执行编号"],
                "定时任务编号": row["定时任务编号"],
                "执行状态": row["执行状态"],
                "执行结果": json.loads(row["执行结果"]),
                "执行人": row["执行人"],
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    def _执行单个任务(self, 操作人编号: str, row) -> dict[str, Any]:
        task = self._转字典(row)
        if task["配置"]["是否自动发布"]:
            raise 业务异常("定时任务不能绕过审核自动发布", "发布拦截", 409)
        执行编号 = f"SCHRUN-{uuid.uuid4().hex[:12]}"
        派生任务编号 = f"TASK-{uuid.uuid4().hex[:12]}"
        幂等键 = f"schedule:{task['定时任务编号']}:{执行编号}"
        result = {
            "定时任务编号": task["定时任务编号"],
            "派生任务编号": 派生任务编号,
            "任务名称": task["任务名称"],
            "任务类型": task["任务类型"],
            "执行周期": task["执行周期"],
            "目标平台": task["配置"]["目标平台"],
            "目标受众": task["配置"]["目标受众"],
            "目标风格": task["配置"]["目标风格"],
            "是否自动进入审核": task["配置"]["是否自动进入审核"],
        }
        self.数据库.执行("UPDATE scheduled_tasks SET 状态 = ? WHERE 定时任务编号 = ?", ("执行中", task["定时任务编号"]))
        self.数据库.执行(
            """
            INSERT INTO tasks (任务编号, 任务名称, 任务类型, 状态, 幂等键)
            VALUES (?, ?, ?, ?, ?)
            """,
            (派生任务编号, f"{task['任务名称']} / 调度执行", task["任务类型"], "待创建", 幂等键),
        )
        self.数据库.执行(
            "INSERT INTO scheduled_task_runs (执行编号, 定时任务编号, 执行状态, 执行结果, 执行人) VALUES (?, ?, ?, ?, ?)",
            (执行编号, task["定时任务编号"], "执行成功", json.dumps(result, ensure_ascii=False), 操作人编号),
        )
        self.数据库.执行("UPDATE scheduled_tasks SET 状态 = ? WHERE 定时任务编号 = ?", ("上次执行完成", task["定时任务编号"]))
        self.审计.记录(
            操作人编号,
            "执行定时任务",
            "定时任务",
            task["定时任务编号"],
            {"执行编号": 执行编号, "派生任务编号": 派生任务编号, "执行状态": "执行成功"},
        )
        return {"执行编号": 执行编号, "执行状态": "执行成功", "执行结果": result}

    @staticmethod
    def _目标锁(请求数据: dict[str, Any]) -> str:
        lock_data = {
            "任务类型": 请求数据["任务类型"],
            "执行周期": 请求数据["执行周期"],
            "目标平台": sorted(请求数据["目标平台"]),
            "目标受众": sorted(请求数据["目标受众"]),
            "目标风格": sorted(请求数据["目标风格"]),
        }
        return json.dumps(lock_data, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _转字典(row) -> dict[str, Any]:
        return {
            "定时任务编号": row["定时任务编号"],
            "任务名称": row["任务名称"],
            "任务类型": row["任务类型"],
            "执行周期": row["执行周期"],
            "状态": row["状态"],
            "目标锁": row["目标锁"],
            "配置": json.loads(row["配置"]),
            "创建时间": row["创建时间"],
        }
