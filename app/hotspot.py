import json
import uuid

from app.audit import 审计服务
from app.database import 数据库
from app.schemas import 创建热点请求


高风险标签 = {"政治", "灾难", "未成年人擦边", "明星肖像", "版权不清晰", "真人肖像"}
过期生命周期 = {"过期", "衰退"}


class 热点服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计

    def 创建(self, 操作人编号: str, 请求: 创建热点请求) -> dict[str, object]:
        风险原因 = self._风险原因(请求)
        是否允许生成 = not 风险原因
        热点编号 = f"HOT-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO hot_topics
            (热点编号, 热点名称, 热点来源, 热度分, 生命周期, 风险分, 受众匹配, 是否允许生成, 风险原因)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                热点编号,
                请求.热点名称,
                请求.热点来源,
                请求.热度分,
                请求.生命周期,
                请求.风险分,
                json.dumps(请求.受众匹配, ensure_ascii=False),
                int(是否允许生成),
                json.dumps(风险原因, ensure_ascii=False),
            ),
        )
        self.审计.记录(操作人编号, "创建热点", "热点", 热点编号, {"热点名称": 请求.热点名称, "是否允许生成": 是否允许生成})
        return self._获取(热点编号)

    def 列表(self) -> list[dict[str, object]]:
        return [self._转字典(row) for row in self.数据库.查询全部("SELECT * FROM hot_topics ORDER BY 创建时间 ASC")]

    def _获取(self, 热点编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM hot_topics WHERE 热点编号 = ?", (热点编号,))
        return self._转字典(row)

    @staticmethod
    def _风险原因(请求: 创建热点请求) -> list[str]:
        原因: list[str] = []
        if 请求.风险分 >= 70:
            原因.append("风险分达到高风险阈值")
        if 请求.生命周期 in 过期生命周期:
            原因.append("热点生命周期不适合生成")
        命中标签 = 高风险标签.intersection(set(请求.风险标签))
        for 标签 in sorted(命中标签):
            原因.append(f"命中高风险标签：{标签}")
        return 原因

    @staticmethod
    def _转字典(row) -> dict[str, object]:
        return {
            "热点编号": row["热点编号"],
            "热点名称": row["热点名称"],
            "热点来源": row["热点来源"],
            "热度分": row["热度分"],
            "生命周期": row["生命周期"],
            "风险分": row["风险分"],
            "受众匹配": json.loads(row["受众匹配"]),
            "是否允许生成": bool(row["是否允许生成"]),
            "风险原因": json.loads(row["风险原因"]),
        }
