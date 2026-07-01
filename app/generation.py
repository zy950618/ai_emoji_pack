import hashlib
import json
import os
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.audit import 审计服务
from app.config import 获取配置
from app.database import 数据库
from app.exceptions import 业务异常
from app.quality import 表情质量评分器, 视觉评分客户端
from app.rule_governance import 平台规则治理服务
from app.schemas import 创建生成策略请求


class 生成策略服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务, 规则治理: 平台规则治理服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计
        self.规则治理 = 规则治理
        self.质量评分器 = 表情质量评分器()
        配置 = 获取配置()
        self.视觉评分 = 视觉评分客户端(配置.视觉评分端点, 配置.视觉评分超时秒, 配置.视觉评分密钥)

    def 创建(self, 操作人编号: str, 请求: 创建生成策略请求) -> dict[str, object]:
        规则 = self.规则治理.获取当前规则(请求.目标平台)
        if 请求.表情数量 < 规则.最少数量 or 请求.表情数量 > 规则.最多数量:
            raise 业务异常("表情数量不符合平台规则", "平台规则失败", 409)
        if len(请求.情绪标签) < 请求.表情数量 or len(请求.场景标签) < 请求.表情数量:
            raise 业务异常("情绪标签和场景标签数量必须覆盖每张表情", "策略不完整", 422)
        self._确认受众存在(请求.目标受众)
        if 请求.关联热点:
            self._确认热点允许生成(请求.关联热点)
        if 请求.关联角色:
            self._确认角色可复用(请求.关联角色)

        策略编号 = f"STR-{uuid.uuid4().hex[:12]}"
        策略版本 = self._版本(请求)
        套装编号 = f"SET-{uuid.uuid4().hex[:12]}"
        预览包编号 = f"PRE-{uuid.uuid4().hex[:12]}"
        策略内容 = 请求.model_dump()
        封面图 = self._媒体占位("封面图", 套装编号, 请求.目标平台)
        缩略图 = self._媒体占位("缩略图", 套装编号, 请求.目标平台)

        self.数据库.执行(
            """
            INSERT INTO generation_strategies
            (策略编号, 策略版本, 目标平台, 目标受众, 生成类型, 表情数量, 策略内容)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (策略编号, 策略版本, 请求.目标平台, 请求.目标受众, 请求.生成类型, 请求.表情数量, json.dumps(策略内容, ensure_ascii=False)),
        )
        self.数据库.执行(
            """
            INSERT INTO sticker_sets
            (套装编号, 策略编号, 标题, 描述, 标签, 目标受众, 使用场景, 平台适配版本, 封面图, 缩略图, 状态)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                套装编号,
                策略编号,
                请求.生成类型,
                f"{请求.目标受众}适用的{请求.生成类型}表情套装",
                json.dumps(请求.风格标签 + 请求.情绪标签, ensure_ascii=False),
                请求.目标受众,
                json.dumps(请求.场景标签, ensure_ascii=False),
                规则.规则版本,
                json.dumps(封面图, ensure_ascii=False),
                json.dumps(缩略图, ensure_ascii=False),
                "策略已生成",
            ),
        )

        表情列表 = []
        for index in range(请求.表情数量):
            表情列表.append(self._创建表情占位(套装编号, index + 1, 请求))

        清单 = {"套装编号": 套装编号, "策略编号": 策略编号, "表情编号": [item["表情编号"] for item in 表情列表]}
        file_path, file_size, content_hash = self._写预览包文件(预览包编号, 清单)
        self.数据库.执行(
            "INSERT INTO preview_packages (预览包编号, 套装编号, 清单, 文件路径, 文件大小B, 内容哈希) VALUES (?, ?, ?, ?, ?, ?)",
            (预览包编号, 套装编号, json.dumps(清单, ensure_ascii=False), file_path, file_size, content_hash),
        )
        self.审计.记录(操作人编号, "创建生成策略", "生成策略", 策略编号, {"套装编号": 套装编号, "策略版本": 策略版本})

        return {
            "策略编号": 策略编号,
            "策略版本": 策略版本,
            "套装": self.获取套装(套装编号),
            "预览包": {"预览包编号": 预览包编号, "清单": 清单, "文件路径": file_path, "文件大小B": file_size, "内容哈希": content_hash},
        }

    def 策略列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM generation_strategies ORDER BY 创建时间 ASC")
        return [
            {
                "策略编号": row["策略编号"],
                "策略版本": row["策略版本"],
                "目标平台": row["目标平台"],
                "目标受众": row["目标受众"],
                "生成类型": row["生成类型"],
                "表情数量": row["表情数量"],
                "策略内容": json.loads(row["策略内容"]),
            }
            for row in rows
        ]

    def 预览包列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM preview_packages ORDER BY 创建时间 ASC")
        return [self._预览包字典(row) for row in rows]

    def 读取预览包文件(self, 预览包编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM preview_packages WHERE 预览包编号 = ?", (预览包编号,))
        if not row:
            raise 业务异常("预览包不存在", "预览包不存在", 404)
        package = self._预览包字典(row)
        file_path = Path(str(package["文件路径"]))
        if not file_path.is_file():
            raise 业务异常("预览包文件不存在", "预览包文件缺失", 409)
        text = file_path.read_text(encoding="utf-8")
        self._校验无密钥泄露(text, str(file_path))
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != package["内容哈希"]:
            raise 业务异常("预览包文件内容与索引不一致", "预览包内容不一致", 409)
        return package | {"文件内容": json.loads(text)}

    def 获取套装(self, 套装编号: str) -> dict[str, object]:
        set_row = self.数据库.查询一条("SELECT * FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        item_rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))
        return {
            "套装编号": set_row["套装编号"],
            "策略编号": set_row["策略编号"],
            "标题": set_row["标题"],
            "描述": set_row["描述"],
            "标签": json.loads(set_row["标签"]),
            "目标受众": set_row["目标受众"],
            "使用场景": json.loads(set_row["使用场景"]),
            "平台适配版本": set_row["平台适配版本"],
            "封面图": json.loads(set_row["封面图"]),
            "缩略图": json.loads(set_row["缩略图"]),
            "风格体系": json.loads(set_row["风格体系"]),
            "质量报告": json.loads(set_row["质量报告"]),
            "状态": set_row["状态"],
            "表情列表": [
                {
                    "表情编号": row["表情编号"],
                    "序号": row["序号"],
                    "情绪标签": row["情绪标签"],
                    "场景标签": row["场景标签"],
                    "文案": row["文案"],
                    "生成参数": json.loads(row["生成参数"]),
                    "文件路径": row["文件路径"],
                    "文件大小B": row["文件大小B"],
                    "文件指纹": row["文件指纹"],
                    "候选数量": row["候选数量"],
                    "重试次数": row["重试次数"],
                    "质量报告": json.loads(row["质量报告"]),
                    "失败原因": json.loads(row["失败原因"]),
                    "状态": row["状态"],
                }
                for row in item_rows
            ],
        }

    def 生成资产(self, 操作人编号: str, 套装编号: str) -> dict[str, object]:
        set_row = self.数据库.查询一条("SELECT * FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        strategy_row = self.数据库.查询一条("SELECT * FROM generation_strategies WHERE 策略编号 = ?", (set_row["策略编号"],))
        if not strategy_row:
            raise 业务异常("生成策略不存在", "策略不存在", 404)
        strategy = json.loads(strategy_row["策略内容"])
        规则 = self.规则治理.获取当前规则(strategy["目标平台"])
        calibration = self._质量校准上下文(套装编号, strategy)

        generated = []
        item_rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))
        for row in item_rows:
            generated.append(self._生成单张质量资产(套装编号, row, 规则.宽度, 规则.高度, len(item_rows), calibration=calibration))

        cover = self._写媒体图片("封面图", 套装编号, strategy["目标平台"], 规则.宽度, 规则.高度)
        thumbnail = self._写媒体图片("缩略图", 套装编号, strategy["目标平台"], 128, 128)
        set_report = self.质量评分器.套装门禁([item["质量报告"] for item in generated], strategy)
        set_report["校准依据"] = calibration
        set_status = "生成完成" if set_report["是否通过"] and all(item["质量报告"]["是否通过"] for item in generated) else "质量待重生成"
        self.数据库.执行(
            "UPDATE sticker_sets SET 封面图 = ?, 缩略图 = ?, 风格体系 = ?, 质量报告 = ?, 状态 = ? WHERE 套装编号 = ?",
            (
                json.dumps(cover, ensure_ascii=False),
                json.dumps(thumbnail, ensure_ascii=False),
                json.dumps(set_report["风格体系"], ensure_ascii=False),
                json.dumps(set_report, ensure_ascii=False),
                set_status,
                套装编号,
            ),
        )
        self.审计.记录(
            操作人编号,
            "生成表情资产",
            "套装",
            套装编号,
            {"生成数量": len(generated), "封面图": cover["文件路径"], "缩略图": thumbnail["文件路径"], "质量状态": set_status},
        )
        return {"套装编号": 套装编号, "生成数量": len(generated), "表情文件": generated, "封面图": cover, "缩略图": thumbnail, "质量报告": set_report, "状态": set_status}

    def 重生成低分项(self, 操作人编号: str, 套装编号: str) -> dict[str, object]:
        set_row = self.数据库.查询一条("SELECT * FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        strategy_row = self.数据库.查询一条("SELECT * FROM generation_strategies WHERE 策略编号 = ?", (set_row["策略编号"],))
        if not strategy_row:
            raise 业务异常("生成策略不存在", "策略不存在", 404)
        strategy = json.loads(strategy_row["策略内容"])
        规则 = self.规则治理.获取当前规则(strategy["目标平台"])
        calibration = self._质量校准上下文(套装编号, strategy)
        item_rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))
        set_report = json.loads(set_row["质量报告"] or "{}")
        set_failed = bool(set_report) and not bool(set_report.get("是否通过", True))
        target_rows = []
        for row in item_rows:
            report = json.loads(row["质量报告"] or "{}")
            failures = json.loads(row["失败原因"] or "[]")
            if set_failed or failures or (report and not bool(report.get("是否通过", True))):
                target_rows.append(row)
        regenerated = [
            self._生成单张质量资产(套装编号, row, 规则.宽度, 规则.高度, len(item_rows), max_retries=3, calibration=calibration)
            for row in target_rows
        ]
        refreshed_rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))
        item_reports = [json.loads(row["质量报告"] or "{}") for row in refreshed_rows if row["质量报告"]]
        refreshed_report = self.质量评分器.套装门禁(item_reports, strategy)
        refreshed_report["校准依据"] = calibration
        set_status = "生成完成" if refreshed_report["是否通过"] and all(report.get("是否通过") for report in item_reports) else "质量待重生成"
        self.数据库.执行(
            "UPDATE sticker_sets SET 风格体系 = ?, 质量报告 = ?, 状态 = ? WHERE 套装编号 = ?",
            (json.dumps(refreshed_report["风格体系"], ensure_ascii=False), json.dumps(refreshed_report, ensure_ascii=False), set_status, 套装编号),
        )
        self.审计.记录(操作人编号, "重生成低分项", "套装", 套装编号, {"重生成数量": len(regenerated), "质量状态": set_status})
        return {"套装编号": 套装编号, "重生成数量": len(regenerated), "表情文件": regenerated, "质量报告": refreshed_report, "状态": set_status}

    def _质量校准上下文(self, 套装编号: str, strategy: dict[str, object]) -> dict[str, object]:
        review_rows = self.数据库.查询全部("SELECT 审核结论, 审核意见, 风险标签 FROM review_records WHERE 套装编号 = ? ORDER BY 创建时间 DESC LIMIT 3", (套装编号,))
        performance_rows = self.数据库.查询全部("SELECT 标签表现, 受众表现, 拒审原因 FROM performance_records ORDER BY 创建时间 DESC LIMIT 5")
        review_feedback = "暂无人工审核样本"
        if review_rows:
            review_feedback = "；".join(f"{row['审核结论']}:{row['审核意见']}" for row in review_rows)
        style_tags = {str(tag) for tag in strategy.get("风格标签", [])}
        matched_tags: list[str] = []
        reject_reasons: list[str] = []
        for row in performance_rows:
            tag_scores = json.loads(row["标签表现"])
            reject_reasons.extend(json.loads(row["拒审原因"]))
            for tag, score in tag_scores.items():
                if tag in style_tags and int(score) >= 80 and tag not in matched_tags:
                    matched_tags.append(tag)
        performance_feedback = "暂无发布后表现数据"
        if performance_rows:
            parts = []
            if matched_tags:
                parts.append("高表现风格:" + "/".join(matched_tags))
            if reject_reasons:
                parts.append("拒审回写:" + "/".join(sorted(set(reject_reasons))))
            performance_feedback = "；".join(parts) if parts else "已有表现数据，但未命中当前风格"
        return {
            "人工审核回流": review_feedback,
            "表现数据校准": performance_feedback,
            "禁止进入主菜单": True,
        }

    def _生成单张质量资产(self, 套装编号: str, row, width: int, height: int, total_items: int, max_retries: int = 2, calibration: dict[str, object] | None = None) -> dict[str, object]:
        item = {
            "表情编号": row["表情编号"],
            "序号": row["序号"],
            "情绪标签": row["情绪标签"],
            "场景标签": row["场景标签"],
            "文案": row["文案"],
        }
        def visual_score(candidate_no: int, retry_no: int) -> dict[str, object]:
            candidate_path = self._资产目录(套装编号) / ".candidates" / f"{row['序号']:02d}-{row['表情编号']}-r{retry_no}-c{candidate_no}.png"
            self._写表情图片(candidate_path, width, height, row, candidate_no)
            return self.视觉评分.评分(candidate_path, item, candidate_no, retry_no)

        selection = self.质量评分器.候选筛选(item, total_items, max_retries=max_retries, visual_score_provider=visual_score)
        report = selection.report
        selected_visual = {}
        for candidate in report["候选评分"]:
            if candidate["候选编号"] == report["选中候选"] and candidate["重试轮次"] == report["实际重试次数"]:
                selected_visual = candidate.get("视觉评分", {})
                break
        report["评分依据"] = self.质量评分器.评分依据(report["评分"], calibration, selected_visual)
        report["生成修正策略"] = self.质量评分器.修正策略(report["失败原因"], report["评分"])
        status = "生成完成" if selection.passed else "质量待重生成"
        path = self._资产目录(套装编号) / f"{row['序号']:02d}-{row['表情编号']}.png"
        file_path, file_size, fingerprint = self._写表情图片(path, width, height, row, int(report["选中候选"]))
        self.数据库.执行(
            """
            UPDATE sticker_items
            SET 文件路径 = ?, 文件大小B = ?, 文件指纹 = ?, 候选数量 = ?, 重试次数 = ?, 质量报告 = ?, 失败原因 = ?, 状态 = ?
            WHERE 表情编号 = ?
            """,
            (
                file_path,
                file_size,
                fingerprint,
                int(report["候选数量"]),
                int(report["实际重试次数"]),
                json.dumps(report, ensure_ascii=False),
                json.dumps(report["失败原因"], ensure_ascii=False),
                status,
                row["表情编号"],
            ),
        )
        return {
            "表情编号": row["表情编号"],
            "序号": row["序号"],
            "文件路径": file_path,
            "文件大小B": file_size,
            "文件指纹": fingerprint,
            "候选数量": int(report["候选数量"]),
            "重试次数": int(report["实际重试次数"]),
            "质量报告": report,
            "失败原因": report["失败原因"],
            "状态": status,
        }

    def 读取表情资产(self, 表情编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM sticker_items WHERE 表情编号 = ?", (表情编号,))
        if not row:
            raise 业务异常("表情资产不存在", "表情资产不存在", 404)
        if not row["文件路径"]:
            raise 业务异常("表情资产尚未生成", "表情资产未生成", 409)
        path = Path(row["文件路径"])
        if not path.is_file():
            raise 业务异常("表情资产文件不存在", "表情资产文件缺失", 409)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != row["文件指纹"]:
            raise 业务异常("表情资产文件与指纹不一致", "表情资产内容不一致", 409)
        return {"表情编号": 表情编号, "文件路径": str(path), "文件大小B": len(content), "文件指纹": row["文件指纹"]}

    def _创建表情占位(self, 套装编号: str, 序号: int, 请求: 创建生成策略请求) -> dict[str, object]:
        情绪 = 请求.情绪标签[序号 - 1]
        场景 = 请求.场景标签[序号 - 1]
        生成参数 = {
            "目标平台": 请求.目标平台,
            "目标受众": 请求.目标受众,
            "风格标签": 请求.风格标签,
            "视觉风格分类": self._视觉风格分类(请求.风格标签),
            "情绪标签": 情绪,
            "场景标签": 场景,
            "关联角色": 请求.关联角色,
        }
        文件指纹 = hashlib.sha256(json.dumps(生成参数, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        表情编号 = f"ITEM-{uuid.uuid4().hex[:12]}"
        self.数据库.执行(
            """
            INSERT INTO sticker_items
            (表情编号, 套装编号, 序号, 情绪标签, 场景标签, 文案, 生成参数, 文件指纹, 状态)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                表情编号,
                套装编号,
                序号,
                情绪,
                场景,
                self._职场文案(情绪, 场景),
                json.dumps(生成参数, ensure_ascii=False),
                文件指纹,
                "待生成",
            ),
        )
        return {"表情编号": 表情编号, "文件指纹": 文件指纹}

    def _确认受众存在(self, 画像名称: str) -> None:
        if not self.数据库.查询一条("SELECT 1 FROM audience_profiles WHERE 画像名称 = ?", (画像名称,)):
            raise 业务异常("受众画像不存在", "画像不存在", 404)

    def _确认热点允许生成(self, 热点名称: str) -> None:
        row = self.数据库.查询一条("SELECT 是否允许生成, 风险原因 FROM hot_topics WHERE 热点名称 = ?", (热点名称,))
        if not row:
            raise 业务异常("关联热点不存在", "热点不存在", 404)
        if not bool(row["是否允许生成"]):
            raise 业务异常("关联热点风险过高，禁止生成策略", "热点风险拦截", 409)

    def _确认角色可复用(self, 角色名称: str) -> None:
        row = self.数据库.查询一条("SELECT 可复用 FROM original_roles WHERE 角色名称 = ?", (角色名称,))
        if not row:
            raise 业务异常("关联原创角色不存在", "角色不存在", 404)
        if not bool(row["可复用"]):
            raise 业务异常("关联原创角色不可复用", "角色不可复用", 409)

    @staticmethod
    def _媒体占位(媒体类型: str, 套装编号: str, 目标平台: str) -> dict[str, object]:
        return {
            "媒体类型": 媒体类型,
            "套装编号": 套装编号,
            "目标平台": 目标平台,
            "状态": "待生成",
            "文件路径": "",
            "文件指纹": "",
        }

    def _写表情图片(self, path: Path, width: int, height: int, row, 候选编号: int = 1) -> tuple[str, int, str]:
        path.parent.mkdir(parents=True, exist_ok=True)
        scale = 2
        image = Image.new("RGBA", (width * scale, height * scale), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        params = json.loads(row["生成参数"])
        风格标签 = [str(item) for item in params.get("风格标签", [])]
        风格分类 = str(params.get("视觉风格分类") or self._视觉风格分类(风格标签))
        config = self._贴纸配置(str(row["情绪标签"]), str(row["场景标签"]), 风格标签)
        outline = config["轮廓色"]
        white = (255, 255, 255, 255)
        blush = (255, 132, 150, 120)

        self._画分类背景(draw, 风格分类, config["强调色"], outline, scale)
        self._画动势背景(draw, config["强调色"], outline, scale)
        self._画候选动势强化(draw, 候选编号, config["强调色"], outline, scale)
        self._画手势(draw, str(row["情绪标签"]), outline, config["主体色"], scale)
        self._画角色主体(draw, config, outline, white, blush, scale, 风格分类)
        self._画风格配件(draw, 风格分类, str(row["情绪标签"]), str(row["场景标签"]), outline, config["强调色"], config["主体色"], scale)
        self._画五官(draw, str(row["情绪标签"]), outline, scale, 风格分类)
        self._画情绪符号(draw, str(row["情绪标签"]), str(row["场景标签"]), outline, config["强调色"], scale, 风格分类)
        self._画文案条(draw, width * scale, height * scale, str(row["文案"]), outline, config["强调色"], scale, 风格分类)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        image.save(path, format="PNG", optimize=True)
        content = path.read_bytes()
        return str(path), len(content), hashlib.sha256(content).hexdigest()

    def _写媒体图片(self, 媒体类型: str, 套装编号: str, 目标平台: str, width: int, height: int) -> dict[str, object]:
        file_name = "cover.png" if 媒体类型 == "封面图" else "thumbnail.png"
        path = self._资产目录(套装编号) / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file():
            image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((10, 12, width - 10, height - 12), radius=max(18, width // 10), fill=(255, 255, 255, 255), outline=(32, 39, 52, 255), width=max(4, width // 42))
            draw.rounded_rectangle((25, 26, width - 25, height - 26), radius=max(14, width // 12), fill=(109, 93, 252, 255))
            draw.ellipse((width * 0.14, height * 0.12, width * 0.46, height * 0.44), fill=(255, 232, 126, 255), outline=(32, 39, 52, 255), width=max(3, width // 58))
            draw.ellipse((width * 0.23, height * 0.23, width * 0.29, height * 0.29), fill=(32, 39, 52, 255))
            draw.ellipse((width * 0.34, height * 0.23, width * 0.40, height * 0.29), fill=(32, 39, 52, 255))
            font = self._字体(max(18, width // 8), bold=True)
            title = "表情套装" if 媒体类型 == "封面图" else "套装"
            text_box = draw.textbbox((0, 0), title, font=font)
            draw.text(((width - (text_box[2] - text_box[0])) / 2, (height - (text_box[3] - text_box[1])) / 2), title, fill=(255, 255, 255, 255), font=font)
            image.save(path, format="PNG", optimize=True)
        content = path.read_bytes()
        return {
            "媒体类型": 媒体类型,
            "套装编号": 套装编号,
            "目标平台": 目标平台,
            "状态": "已生成",
            "文件路径": str(path),
            "文件大小B": len(content),
            "文件指纹": hashlib.sha256(content).hexdigest(),
        }

    def _资产目录(self, 套装编号: str) -> Path:
        return self.数据库.数据库路径.parent / "generated_assets" / 套装编号

    @staticmethod
    def _颜色(seed: str) -> tuple[int, int, int, int]:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        return 80 + digest[0] % 120, 80 + digest[1] % 120, 80 + digest[2] % 120, 235

    @staticmethod
    def _视觉风格分类(风格标签: list[str]) -> str:
        joined = " ".join(风格标签)
        if "游戏开黑" in joined:
            return "霓虹游戏反应"
        if "二次元Q版" in joined:
            return "二次元Q版闪光"
        if "家庭大字" in joined:
            return "家庭大字高可读"
        if "节日祝福" in joined:
            return "节日礼花祝福"
        if "品牌吉祥物" in joined:
            return "品牌吉祥物徽章"
        if "治愈陪伴" in joined:
            return "治愈陪伴软萌"
        if "搞笑夸张" in joined:
            return "搞笑反应梗"
        return "圆润职场贴纸"

    @classmethod
    def _贴纸配置(cls, 情绪: str, 场景: str, 风格标签: list[str]) -> dict[str, tuple[int, int, int, int] | str]:
        palette = {
            "开心": ((255, 218, 97, 255), (255, 242, 176, 255), (255, 141, 73, 255)),
            "无语": ((156, 178, 229, 255), (210, 221, 248, 255), (89, 113, 178, 255)),
            "加油": ((116, 211, 143, 255), (199, 244, 205, 255), (31, 153, 105, 255)),
            "震惊": ((255, 176, 108, 255), (255, 226, 184, 255), (235, 91, 86, 255)),
            "感谢": ((245, 140, 190, 255), (255, 210, 232, 255), (202, 65, 145, 255)),
            "困惑": ((134, 211, 198, 255), (204, 242, 236, 255), (46, 145, 143, 255)),
        }
        主体色, 高光色, 强调色 = palette.get(情绪, palette.get(场景, ((160, 190, 220, 255), (216, 230, 244, 255), (62, 128, 172, 255))))
        风格分类 = cls._视觉风格分类(风格标签)
        style_palette = {
            "霓虹游戏反应": ((74, 222, 128, 255), (186, 230, 253, 255), (99, 102, 241, 255), (15, 23, 42, 255)),
            "二次元Q版闪光": ((255, 170, 224, 255), (255, 226, 247, 255), (124, 58, 237, 255), (66, 43, 106, 255)),
            "家庭大字高可读": ((255, 204, 112, 255), (255, 241, 199, 255), (239, 68, 68, 255), (36, 36, 45, 255)),
            "节日礼花祝福": ((255, 110, 90, 255), (255, 218, 150, 255), (245, 158, 11, 255), (97, 35, 35, 255)),
            "品牌吉祥物徽章": ((96, 165, 250, 255), (219, 234, 254, 255), (37, 99, 235, 255), (30, 64, 175, 255)),
            "治愈陪伴软萌": ((160, 230, 210, 255), (230, 255, 246, 255), (236, 72, 153, 255), (45, 85, 95, 255)),
            "搞笑反应梗": ((255, 235, 108, 255), (255, 248, 188, 255), (249, 115, 22, 255), (25, 35, 48, 255)),
        }
        if 风格分类 in style_palette:
            主体色, 高光色, 强调色, 轮廓色 = style_palette[风格分类]
        else:
            轮廓色 = (32, 39, 52, 255)
        return {"主体色": 主体色, "高光色": 高光色, "强调色": 强调色, "轮廓色": 轮廓色, "风格分类": 风格分类}

    @staticmethod
    def _框(box: tuple[int, int, int, int], scale: int) -> tuple[int, int, int, int]:
        return tuple(value * scale for value in box)

    @staticmethod
    def _点(points: list[tuple[int, int]], scale: int) -> list[tuple[int, int]]:
        return [(x * scale, y * scale) for x, y in points]

    @classmethod
    def _画角色主体(
        cls,
        draw: ImageDraw.ImageDraw,
        config: dict[str, tuple[int, int, int, int]],
        outline: tuple[int, int, int, int],
        white: tuple[int, int, int, int],
        blush: tuple[int, int, int, int],
        scale: int,
        风格分类: str,
    ) -> None:
        draw.ellipse(cls._框((102, 338, 410, 388), scale), fill=(25, 35, 48, 46))
        draw.rounded_rectangle(cls._框((70, 34, 442, 386), scale), radius=176 * scale, fill=white)
        body_box = (91, 54, 421, 362)
        inner_box = (104, 68, 408, 346)
        if 风格分类 == "搞笑反应梗":
            body_box = (84, 42, 430, 368)
            inner_box = (100, 56, 414, 352)
        elif 风格分类 == "二次元Q版闪光":
            draw.polygon(cls._点([(154, 70), (190, 18), (226, 84)], scale), fill=white, outline=outline)
            draw.polygon(cls._点([(286, 84), (322, 18), (358, 70)], scale), fill=white, outline=outline)
            draw.polygon(cls._点([(168, 70), (191, 36), (213, 84)], scale), fill=config["高光色"])
            draw.polygon(cls._点([(299, 84), (322, 36), (344, 70)], scale), fill=config["高光色"])
        elif 风格分类 == "霓虹游戏反应":
            draw.arc(cls._框((106, 70, 406, 324), scale), 192, 348, fill=outline, width=22 * scale)
            draw.rounded_rectangle(cls._框((70, 190, 110, 270), scale), radius=15 * scale, fill=config["强调色"], outline=outline, width=5 * scale)
            draw.rounded_rectangle(cls._框((402, 190, 442, 270), scale), radius=15 * scale, fill=config["强调色"], outline=outline, width=5 * scale)
        draw.rounded_rectangle(cls._框(body_box, scale), radius=155 * scale, fill=outline)
        draw.rounded_rectangle(cls._框(inner_box, scale), radius=140 * scale, fill=config["主体色"])
        for index in range(4):
            inset = 116 + index * 14
            draw.rounded_rectangle(
                cls._框((inset, 82 + index * 12, 408 - index * 9, 340 - index * 12), scale),
                radius=(126 - index * 12) * scale,
                fill=(*config["高光色"][:3], 255),
            )
        draw.ellipse(cls._框((122, 88, 198, 164), scale), fill=config["高光色"])
        draw.arc(cls._框((130, 82, 376, 304), scale), 205, 268, fill=(255, 255, 255, 190), width=8 * scale)
        draw.ellipse(cls._框((136, 226, 196, 262), scale), fill=blush)
        draw.ellipse(cls._框((316, 226, 376, 262), scale), fill=blush)
        draw.ellipse(cls._框((158, 330, 230, 378), scale), fill=white)
        draw.ellipse(cls._框((282, 330, 354, 378), scale), fill=white)
        draw.ellipse(cls._框((168, 338, 224, 374), scale), fill=config["强调色"], outline=outline, width=5 * scale)
        draw.ellipse(cls._框((288, 338, 344, 374), scale), fill=config["强调色"], outline=outline, width=5 * scale)
        if 风格分类 == "品牌吉祥物徽章":
            draw.rounded_rectangle(cls._框((174, 54, 338, 94), scale), radius=18 * scale, fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.text((210 * scale, 60 * scale), "IP", fill=config["强调色"], font=ImageFont.load_default(size=25 * scale))
        for x, y in ((150, 112), (360, 126), (132, 292), (386, 286)):
            draw.ellipse(cls._框((x, y, x + 8, y + 8), scale), fill=(255, 255, 255, 135))

    @classmethod
    def _画分类背景(cls, draw: ImageDraw.ImageDraw, 风格分类: str, accent: tuple[int, int, int, int], outline: tuple[int, int, int, int], scale: int) -> None:
        if 风格分类 == "霓虹游戏反应":
            for y in (92, 132, 172):
                draw.line(cls._点([(54, y), (142, y - 30)], scale), fill=(*accent[:3], 220), width=6 * scale)
                draw.line(cls._点([(370, y - 24), (470, y + 10)], scale), fill=(34, 211, 238, 220), width=6 * scale)
        elif 风格分类 == "二次元Q版闪光":
            for points in [[(70, 82), (80, 108), (108, 116), (82, 126), (72, 152), (62, 126), (36, 116), (62, 106)], [(420, 74), (432, 104), (462, 112), (434, 124), (426, 154), (414, 124), (386, 112), (414, 102)]]:
                draw.polygon(cls._点(points, scale), fill=(255, 255, 255, 255))
                draw.line(cls._点(points + [points[0]], scale), fill=accent, width=4 * scale)
        elif 风格分类 == "节日礼花祝福":
            for x, y, color in ((72, 82, accent), (438, 92, (255, 214, 10, 255)), (84, 284, (16, 185, 129, 255)), (436, 288, accent)):
                draw.ellipse(cls._框((x, y, x + 24, y + 24), scale), fill=color, outline=outline, width=3 * scale)
                draw.line(cls._点([(x + 12, y + 12), (x + 4, y + 40)], scale), fill=color, width=4 * scale)
        elif 风格分类 == "搞笑反应梗":
            burst = [(256, 28), (286, 82), (348, 50), (336, 112), (408, 112), (354, 154), (418, 206), (336, 200), (348, 276), (288, 232), (256, 308), (224, 232), (164, 276), (176, 200), (94, 206), (158, 154), (104, 112), (176, 112), (164, 50), (226, 82)]
            draw.polygon(cls._点(burst, scale), fill=(255, 255, 255, 255))
            draw.line(cls._点(burst + [burst[0]], scale), fill=accent, width=4 * scale)
        elif 风格分类 == "治愈陪伴软萌":
            for box in ((56, 84, 140, 134), (380, 74, 470, 130), (64, 278, 132, 324)):
                draw.rounded_rectangle(cls._框(box, scale), radius=24 * scale, fill=(255, 255, 255, 220), outline=outline, width=2 * scale)

    @classmethod
    def _画动势背景(cls, draw: ImageDraw.ImageDraw, accent: tuple[int, int, int, int], outline: tuple[int, int, int, int], scale: int) -> None:
        for start, end in [((66, 180), (34, 158)), ((72, 214), (34, 218)), ((436, 176), (472, 150)), ((434, 214), (482, 216))]:
            draw.line(cls._点([start, end], scale), fill=(255, 255, 255, 230), width=13 * scale)
            draw.line(cls._点([start, end], scale), fill=(*accent[:3], 220), width=6 * scale)
        for box in ((62, 62, 84, 84), (430, 58, 452, 80), (54, 258, 70, 274)):
            draw.ellipse(cls._框(box, scale), fill=(255, 255, 255, 235), outline=outline, width=3 * scale)

    @classmethod
    def _画候选动势强化(cls, draw: ImageDraw.ImageDraw, 候选编号: int, accent: tuple[int, int, int, int], outline: tuple[int, int, int, int], scale: int) -> None:
        intensity = max(1, min(候选编号, 4))
        for offset in range(intensity):
            y = 126 + offset * 34
            draw.line(cls._点([(28, y), (110, y - 28)], scale), fill=(255, 255, 255, 225), width=(10 - offset) * scale)
            draw.line(cls._点([(30, y), (112, y - 28)], scale), fill=(*accent[:3], 230), width=(5 + offset) * scale)
            draw.line(cls._点([(400, y + 22), (486, y - 6)], scale), fill=(255, 255, 255, 225), width=(10 - offset) * scale)
            draw.line(cls._点([(398, y + 22), (486, y - 6)], scale), fill=(*accent[:3], 230), width=(5 + offset) * scale)
        if intensity >= 3:
            burst = [(254, 42), (272, 82), (316, 72), (292, 108), (330, 136), (282, 132), (256, 176), (230, 132), (182, 136), (220, 108), (196, 72), (240, 82)]
            draw.polygon(cls._点(burst, scale), fill=(255, 255, 255, 235))
            draw.line(cls._点(burst + [burst[0]], scale), fill=outline, width=4 * scale)

    @classmethod
    def _画风格配件(
        cls,
        draw: ImageDraw.ImageDraw,
        风格分类: str,
        情绪: str,
        场景: str,
        outline: tuple[int, int, int, int],
        accent: tuple[int, int, int, int],
        body: tuple[int, int, int, int],
        scale: int,
    ) -> None:
        if 风格分类 == "霓虹游戏反应":
            draw.rounded_rectangle(cls._框((180, 116, 332, 148), scale), radius=16 * scale, fill=(15, 23, 42, 235), outline=accent, width=4 * scale)
            draw.line(cls._点([(208, 132), (238, 132), (252, 122), (282, 142), (306, 126)], scale), fill=(34, 211, 238, 255), width=5 * scale)
            bolt = [(394, 78), (430, 78), (406, 120), (440, 120), (382, 184), (402, 136), (374, 136)]
            draw.polygon(cls._点(bolt, scale), fill=(250, 204, 21, 255), outline=outline)
        elif 风格分类 == "二次元Q版闪光":
            draw.line(cls._点([(132, 236), (172, 246)], scale), fill=(255, 255, 255, 200), width=5 * scale)
            draw.line(cls._点([(340, 246), (380, 236)], scale), fill=(255, 255, 255, 200), width=5 * scale)
            draw.ellipse(cls._框((394, 82, 430, 118), scale), fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.text((403 * scale, 79 * scale), "☆", fill=accent, font=ImageFont.load_default(size=32 * scale))
        elif 风格分类 == "家庭大字高可读":
            draw.rounded_rectangle(cls._框((360, 88, 460, 148), scale), radius=18 * scale, fill=(255, 255, 255, 255), outline=outline, width=5 * scale)
            draw.text((382 * scale, 101 * scale), "大字", fill=accent, font=cls._字体(24 * scale, bold=True))
        elif 风格分类 == "节日礼花祝福":
            draw.pieslice(cls._框((196, 34, 316, 128), scale), 205, 335, fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.arc(cls._框((206, 42, 306, 118), scale), 205, 335, fill=accent, width=9 * scale)
            draw.ellipse(cls._框((244, 46, 268, 70), scale), fill=(255, 214, 10, 255), outline=outline, width=3 * scale)
        elif 风格分类 == "品牌吉祥物徽章":
            draw.polygon(cls._点([(72, 118), (114, 96), (156, 118), (146, 178), (82, 178)], scale), fill=(255, 255, 255, 245), outline=outline)
            draw.text((98 * scale, 124 * scale), "✓", fill=accent, font=ImageFont.load_default(size=42 * scale))
        elif 风格分类 == "治愈陪伴软萌":
            draw.ellipse(cls._框((390, 88, 424, 122), scale), fill=accent)
            draw.ellipse(cls._框((420, 88, 454, 122), scale), fill=accent)
            draw.polygon(cls._点([(390, 106), (454, 106), (422, 154)], scale), fill=accent)

    @classmethod
    def _画五官(cls, draw: ImageDraw.ImageDraw, 情绪: str, outline: tuple[int, int, int, int], scale: int, 风格分类: str) -> None:
        if 风格分类 == "搞笑反应梗" and 情绪 in {"震惊", "困惑"}:
            draw.ellipse(cls._框((138, 156, 220, 238), scale), fill=(255, 255, 255, 245), outline=outline, width=8 * scale)
            draw.ellipse(cls._框((292, 156, 374, 238), scale), fill=(255, 255, 255, 245), outline=outline, width=8 * scale)
            draw.ellipse(cls._框((168, 188, 194, 214), scale), fill=outline)
            draw.ellipse(cls._框((322, 188, 348, 214), scale), fill=outline)
            draw.ellipse(cls._框((224, 246, 288, 320), scale), fill=(255, 255, 255, 245), outline=outline, width=8 * scale)
            return
        if 风格分类 == "二次元Q版闪光" and 情绪 in {"开心", "感谢"}:
            for x in (158, 310):
                star = [(x + 18, 166), (x + 26, 188), (x + 50, 190), (x + 30, 204), (x + 38, 228), (x + 18, 214), (x - 2, 228), (x + 6, 204), (x - 14, 190), (x + 10, 188)]
                draw.polygon(cls._点(star, scale), fill=(255, 255, 255, 245), outline=outline)
            draw.arc(cls._框((198, 232, 314, 306), scale), 20, 160, fill=outline, width=11 * scale)
            return
        if 情绪 == "开心":
            draw.ellipse(cls._框((154, 166, 206, 218), scale), fill=outline)
            draw.ellipse(cls._框((306, 166, 358, 218), scale), fill=outline)
            draw.ellipse(cls._框((170, 176, 188, 194), scale), fill=(255, 255, 255, 230))
            draw.ellipse(cls._框((322, 176, 340, 194), scale), fill=(255, 255, 255, 230))
            draw.arc(cls._框((196, 220, 316, 306), scale), 18, 162, fill=outline, width=12 * scale)
        elif 情绪 == "无语":
            draw.rounded_rectangle(cls._框((150, 184, 216, 202), scale), radius=8 * scale, fill=outline)
            draw.rounded_rectangle(cls._框((296, 184, 362, 202), scale), radius=8 * scale, fill=outline)
            draw.line(cls._点([(204, 268), (308, 268)], scale), fill=outline, width=10 * scale)
        elif 情绪 == "加油":
            draw.line(cls._点([(146, 168), (210, 188)], scale), fill=outline, width=9 * scale)
            draw.line(cls._点([(302, 188), (366, 168)], scale), fill=outline, width=9 * scale)
            draw.ellipse(cls._框((166, 196, 204, 234), scale), fill=outline)
            draw.ellipse(cls._框((308, 196, 346, 234), scale), fill=outline)
            draw.arc(cls._框((198, 240, 314, 312), scale), 20, 160, fill=outline, width=11 * scale)
        elif 情绪 == "震惊":
            draw.ellipse(cls._框((148, 166, 210, 230), scale), fill=(255, 255, 255, 235), outline=outline, width=8 * scale)
            draw.ellipse(cls._框((302, 166, 364, 230), scale), fill=(255, 255, 255, 235), outline=outline, width=8 * scale)
            draw.ellipse(cls._框((226, 246, 286, 320), scale), fill=(255, 255, 255, 235), outline=outline, width=8 * scale)
        elif 情绪 == "感谢":
            draw.arc(cls._框((150, 168, 212, 230), scale), 205, 335, fill=outline, width=9 * scale)
            draw.arc(cls._框((300, 168, 362, 230), scale), 205, 335, fill=outline, width=9 * scale)
            draw.arc(cls._框((202, 234, 310, 304), scale), 18, 162, fill=outline, width=10 * scale)
        elif 情绪 == "困惑":
            draw.line(cls._点([(150, 174), (212, 158)], scale), fill=outline, width=9 * scale)
            draw.ellipse(cls._框((166, 198, 204, 236), scale), fill=outline)
            draw.ellipse(cls._框((314, 190, 352, 228), scale), fill=outline)
            draw.arc(cls._框((214, 248, 306, 308), scale), 205, 335, fill=outline, width=10 * scale)
        else:
            draw.ellipse(cls._框((170, 190, 202, 222), scale), fill=outline)
            draw.ellipse(cls._框((310, 190, 342, 222), scale), fill=outline)
            draw.arc(cls._框((206, 234, 306, 300), scale), 20, 160, fill=outline, width=9 * scale)

    @classmethod
    def _画手势(cls, draw: ImageDraw.ImageDraw, 情绪: str, outline: tuple[int, int, int, int], body: tuple[int, int, int, int], scale: int) -> None:
        if 情绪 == "加油":
            draw.line(cls._点([(386, 234), (450, 128)], scale), fill=(255, 255, 255, 255), width=34 * scale)
            draw.line(cls._点([(386, 234), (450, 128)], scale), fill=outline, width=13 * scale)
            draw.ellipse(cls._框((424, 92, 480, 148), scale), fill=body, outline=outline, width=8 * scale)
            draw.line(cls._点([(116, 280), (76, 318)], scale), fill=(255, 255, 255, 255), width=30 * scale)
            draw.line(cls._点([(116, 280), (76, 318)], scale), fill=outline, width=12 * scale)
            draw.ellipse(cls._框((52, 300, 100, 348), scale), fill=body, outline=outline, width=7 * scale)
        else:
            draw.line(cls._点([(112, 274), (58, 318)], scale), fill=(255, 255, 255, 255), width=30 * scale)
            draw.line(cls._点([(398, 274), (454, 318)], scale), fill=(255, 255, 255, 255), width=30 * scale)
            draw.line(cls._点([(112, 274), (58, 318)], scale), fill=outline, width=12 * scale)
            draw.line(cls._点([(398, 274), (454, 318)], scale), fill=outline, width=12 * scale)
            draw.ellipse(cls._框((38, 300, 92, 354), scale), fill=body, outline=outline, width=7 * scale)
            draw.ellipse(cls._框((420, 300, 474, 354), scale), fill=body, outline=outline, width=7 * scale)

    @classmethod
    def _画情绪符号(cls, draw: ImageDraw.ImageDraw, 情绪: str, 场景: str, outline: tuple[int, int, int, int], accent: tuple[int, int, int, int], scale: int, 风格分类: str) -> None:
        if 情绪 == "开心":
            points = [(392, 82), (406, 116), (444, 120), (414, 144), (424, 180), (392, 160), (360, 180), (370, 144), (340, 120), (378, 116)]
            draw.polygon(cls._点(points, scale), fill=(255, 255, 255, 255))
            draw.line(cls._点(points + [points[0]], scale), fill=accent, width=5 * scale)
        elif 情绪 == "无语":
            draw.rounded_rectangle(cls._框((366, 96, 448, 154), scale), radius=16 * scale, fill=(255, 255, 255, 255), outline=outline, width=5 * scale)
            draw.text((388 * scale, 104 * scale), "...", fill=accent, font=ImageFont.load_default(size=28 * scale))
        elif 情绪 == "震惊":
            draw.line(cls._点([(390, 84), (404, 146)], scale), fill=accent, width=10 * scale)
            draw.ellipse(cls._框((392, 160, 408, 176), scale), fill=accent)
        elif 情绪 == "感谢":
            draw.ellipse(cls._框((382, 92, 414, 124), scale), fill=accent)
            draw.ellipse(cls._框((414, 92, 446, 124), scale), fill=accent)
            draw.polygon(cls._点([(380, 110), (448, 110), (414, 160)], scale), fill=accent)
            draw.line(cls._点([(380, 110), (448, 110), (414, 160), (380, 110)], scale), fill=outline, width=4 * scale)
        elif 情绪 == "困惑":
            font = ImageFont.load_default(size=48 * scale)
            draw.text((392 * scale, 76 * scale), "?", fill=accent, font=font)
        if 场景 == "开会":
            draw.rounded_rectangle(cls._框((62, 86, 136, 132), scale), radius=12 * scale, fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.line(cls._点([(76, 104), (120, 104)], scale), fill=accent, width=5 * scale)
        elif 场景 == "确认":
            draw.rounded_rectangle(cls._框((58, 92, 132, 150), scale), radius=12 * scale, fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.line(cls._点([(76, 124), (94, 140), (118, 104)], scale), fill=accent, width=6 * scale)
        elif 场景 == "催办":
            draw.rounded_rectangle(cls._框((56, 92, 136, 146), scale), radius=12 * scale, fill=(255, 255, 255, 255), outline=outline, width=4 * scale)
            draw.line(cls._点([(76, 120), (118, 120)], scale), fill=accent, width=5 * scale)
            draw.line(cls._点([(104, 106), (120, 120), (104, 134)], scale), fill=accent, width=5 * scale)
        if 风格分类 == "霓虹游戏反应":
            draw.rounded_rectangle(cls._框((58, 86, 140, 138), scale), radius=14 * scale, fill=(15, 23, 42, 235), outline=accent, width=4 * scale)
            draw.ellipse(cls._框((78, 104, 96, 122), scale), fill=(34, 211, 238, 255))
            draw.line(cls._点([(108, 113), (128, 113)], scale), fill=(34, 211, 238, 255), width=4 * scale)

    @classmethod
    def _画文案条(cls, draw: ImageDraw.ImageDraw, width: int, height: int, 文案: str, outline: tuple[int, int, int, int], accent: tuple[int, int, int, int], scale: int, 风格分类: str) -> None:
        box = (52 * scale, height - 116 * scale, width - 52 * scale, height - 32 * scale)
        if 风格分类 == "家庭大字高可读":
            box = (34 * scale, height - 140 * scale, width - 34 * scale, height - 24 * scale)
        draw.rounded_rectangle((box[0] + 6 * scale, box[1] + 9 * scale, box[2] + 6 * scale, box[3] + 9 * scale), radius=32 * scale, fill=(25, 35, 48, 50))
        fill = (255, 255, 255, 255)
        if 风格分类 == "霓虹游戏反应":
            fill = (17, 24, 39, 255)
        draw.rounded_rectangle(box, radius=32 * scale, fill=fill, outline=outline, width=7 * scale)
        draw.rounded_rectangle((box[0] + 9 * scale, box[1] + 9 * scale, box[0] + 31 * scale, box[3] - 9 * scale), radius=11 * scale, fill=accent)
        font_size = 50 if 风格分类 == "家庭大字高可读" else 42
        font = cls._字体(font_size * scale, bold=True)
        text_box = draw.textbbox((0, 0), 文案, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        text_fill = (255, 255, 255, 255) if 风格分类 == "霓虹游戏反应" else outline
        draw.text(((width - text_width) / 2 + 12 * scale, box[1] + (box[3] - box[1] - text_height) / 2 - 5 * scale), 文案, fill=text_fill, font=font)

    @staticmethod
    def _职场文案(情绪: str, 场景: str) -> str:
        copies = {
            ("开心", "沟通"): "收到啦",
            ("无语", "开会"): "先别卷",
            ("加油", "催办"): "马上冲",
            ("震惊", "确认"): "这也改",
            ("感谢", "复盘"): "辛苦啦",
            ("困惑", "交付"): "我捋下",
        }
        return copies.get((情绪, 场景), f"{情绪}一下")

    @staticmethod
    def _字体(size: int, bold: bool = False) -> ImageFont.ImageFont:
        candidates = [
            Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        ]
        for font_path in candidates:
            if font_path.is_file():
                return ImageFont.truetype(str(font_path), size)
        return ImageFont.load_default()

    def _写预览包文件(self, 预览包编号: str, 清单: dict[str, object]) -> tuple[str, int, str]:
        directory = self.数据库.数据库路径.parent / "preview_packages"
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{预览包编号}.json"
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
            raise 业务异常("预览包包含密钥风险", "密钥泄露风险", 409)

    @staticmethod
    def _预览包字典(row) -> dict[str, object]:
        return {
            "预览包编号": row["预览包编号"],
            "套装编号": row["套装编号"],
            "清单": json.loads(row["清单"]),
            "文件路径": row["文件路径"],
            "文件大小B": row["文件大小B"],
            "内容哈希": row["内容哈希"],
            "创建时间": row["创建时间"],
        }

    @staticmethod
    def _版本(请求: 创建生成策略请求) -> str:
        raw = json.dumps(请求.model_dump(), ensure_ascii=False, sort_keys=True)
        return f"strategy-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10]}"
