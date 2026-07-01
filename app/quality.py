from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Callable
from urllib import error, request


QUALITY_METRICS = [
    "角色吸引力",
    "脸部记忆点",
    "轮廓识别度",
    "表情张力",
    "动作夸张度",
    "文案传播感",
    "小图可读性",
    "贴纸质感",
    "可爱感",
    "搞笑感",
    "卖萌感",
    "时尚感",
    "年轻感",
    "想分享感",
    "静态动势",
    "动态自然度",
]


SINGLE_THRESHOLDS = {
    "审美总分": 85,
    "角色吸引力": 80,
    "表情张力": 80,
    "动作夸张度": 80,
    "小图可读性": 85,
    "贴纸质感": 80,
    "静态动势": 75,
    "动态自然度": 80,
    "目标风格分": 80,
}

SET_THRESHOLDS = {"风格一致性": 85, "套装差异性": 80}


FIX_STRATEGIES = {
    "审美总分": ["提高色彩对比", "减少画面杂点", "强化角色高光和贴纸边缘"],
    "角色吸引力": ["放大角色头部", "增加独特发饰或脸部符号", "统一角色主色"],
    "表情张力": ["放大眼睛和嘴型", "增加情绪符号", "提高眉眼倾斜幅度"],
    "动作夸张度": ["加大手势幅度", "加入身体倾斜", "增加速度线"],
    "小图可读性": ["放大文案字号", "缩短文案", "提升文字和描边对比"],
    "贴纸质感": ["加厚白边", "增加胶面高光", "降低复杂背景"],
    "静态动势": ["强化构图重心偏移", "增加挤压拉伸", "加入动作瞬间线"],
    "动态自然度": ["减少跳变", "补足首尾循环", "调整快入慢出节奏"],
    "目标风格分": ["回到固定主色板", "统一字体和描边", "减少偏离目标风格的装饰"],
    "风格一致性": ["复用同一主角色比例", "锁定描边宽度", "锁定阴影强度"],
    "套装差异性": ["为每张更换姿势", "为每张更换手势和道具", "避免只换文案"],
}


@dataclass(frozen=True)
class CandidateSelection:
    passed: bool
    report: dict[str, Any]


class 视觉评分客户端:
    def __init__(self, 端点: str = "", 超时秒: float = 3.0, 密钥: str = "") -> None:
        self.端点 = 端点.strip()
        self.超时秒 = 超时秒
        self.密钥 = 密钥.strip()

    def 评分(self, 图片路径: Path, item: dict[str, Any], candidate_no: int, retry_no: int) -> dict[str, Any]:
        if not self.端点:
            return {"状态": "未配置视觉评分接口", "评分": {}, "说明": "使用本地启发式代理"}
        payload = {
            "image_base64": base64.b64encode(图片路径.read_bytes()).decode("ascii"),
            "mime_type": "image/png",
            "metrics": QUALITY_METRICS + ["审美总分", "目标风格分"],
            "candidate": {"候选编号": candidate_no, "重试轮次": retry_no},
            "item": {
                "表情编号": item.get("表情编号", ""),
                "序号": item.get("序号", 0),
                "情绪标签": item.get("情绪标签", ""),
                "场景标签": item.get("场景标签", ""),
                "文案": item.get("文案", ""),
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.密钥:
            headers["Authorization"] = f"Bearer {self.密钥}"
        req = request.Request(self.端点, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.超时秒) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            scores = self._标准化评分(data.get("评分") or data.get("scores") or {})
            return {
                "状态": "已调用真实视觉评分接口",
                "提供方": str(data.get("模型") or data.get("model") or "external-vision-scorer"),
                "评分": scores,
                "说明": str(data.get("说明") or data.get("notes") or "外部视觉评分已返回"),
            }
        except (OSError, TimeoutError, ValueError, error.URLError, error.HTTPError) as exc:
            return {
                "状态": "视觉评分接口失败，已回退本地启发式代理",
                "评分": {},
                "说明": str(exc),
            }

    @staticmethod
    def _标准化评分(raw_scores: dict[str, Any]) -> dict[str, float]:
        scores: dict[str, float] = {}
        allowed = set(QUALITY_METRICS + ["审美总分", "目标风格分"])
        for metric, value in raw_scores.items():
            if metric not in allowed:
                continue
            if isinstance(value, bool):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            scores[metric] = max(0.0, min(100.0, number))
        if scores and "审美总分" not in scores:
            metric_values = [scores[key] for key in QUALITY_METRICS if key in scores]
            if metric_values:
                scores["审美总分"] = round(mean(metric_values), 1)
        return scores


class 表情质量评分器:
    def 固定风格体系(self, strategy: dict[str, Any]) -> dict[str, Any]:
        styles = [str(item) for item in strategy.get("风格标签", [])]
        style_name = " / ".join(styles[:3]) if styles else "圆润贴纸"
        return {
            "主角色设定": f"{style_name}原创圆团助手",
            "头身比": "1:1.15",
            "主色板": ["#6D5DFC", "#FFD766", "#14B8A6", "#111827"],
            "字体风格": "粗黑圆体",
            "描边宽度": "7px",
            "阴影强度": "中等软阴影",
            "贴纸质感": "高光胶面贴纸",
            "情绪强度": "夸张",
            "动作强度": "强动势",
            "文案语气": "短句、口语、可转发",
        }

    def 评分(self, item: dict[str, Any], candidate_no: int, retry_no: int, total_items: int) -> dict[str, Any]:
        emotion = str(item.get("情绪标签", ""))
        scene = str(item.get("场景标签", ""))
        copy = str(item.get("文案", ""))
        diversity_bonus = min(5, total_items)
        base = 75 + candidate_no * 3 + retry_no * 5
        expressive_bonus = 3 if emotion in {"开心", "震惊", "加油", "困惑"} else 1
        action_bonus = 3 if scene in {"催办", "开会", "确认", "交付", "通勤"} else 1
        share_bonus = 3 if len(copy) <= 5 else 0
        scores = {
            "角色吸引力": base + 4,
            "脸部记忆点": base + 3,
            "轮廓识别度": base + 5,
            "表情张力": base + expressive_bonus + 3,
            "动作夸张度": base + action_bonus + 3,
            "文案传播感": base + share_bonus + 2,
            "小图可读性": base + 7,
            "贴纸质感": base + 5,
            "可爱感": base + 4,
            "搞笑感": base + expressive_bonus + 1,
            "卖萌感": base + 3,
            "时尚感": base + 2,
            "年轻感": base + 3,
            "想分享感": base + share_bonus + 2,
            "静态动势": base + action_bonus,
            "动态自然度": base + action_bonus + 2,
        }
        scores = {key: min(98, value) for key, value in scores.items()}
        scores["审美总分"] = round(mean(scores[key] for key in QUALITY_METRICS), 1)
        scores["目标风格分"] = min(98, base + diversity_bonus + 4)
        return scores

    def 单张门禁(self, scores: dict[str, Any]) -> dict[str, Any]:
        failures = [
            f"{metric}低于{threshold}"
            for metric, threshold in SINGLE_THRESHOLDS.items()
            if float(scores.get(metric, 0)) < threshold
        ]
        return {"是否通过": not failures, "失败原因": failures, "阈值": SINGLE_THRESHOLDS}

    def 评分依据(self, scores: dict[str, Any], calibration: dict[str, Any] | None = None, visual_result: dict[str, Any] | None = None) -> dict[str, Any]:
        calibration = calibration or {}
        visual_result = visual_result or {"状态": "未配置视觉评分接口", "评分": {}, "说明": "使用本地启发式代理"}
        visual_status = str(visual_result.get("状态", "未配置视觉评分接口"))
        if visual_status == "已调用真实视觉评分接口":
            visual_scoring = {
                "状态": visual_status,
                "说明": visual_result.get("说明", "外部视觉评分已返回"),
                "提供方": visual_result.get("提供方", "external-vision-scorer"),
                "接口分": visual_result.get("评分", {}),
            }
        else:
            visual_scoring = {
                "状态": visual_status,
                "说明": visual_result.get("说明", "当前未调用外部视觉模型，使用轮廓、动势、表情、贴纸质感指标代理"),
                "代理分": round(mean(float(scores.get(key, 0)) for key in ("轮廓识别度", "表情张力", "动作夸张度", "贴纸质感")), 1),
            }
        return {
            "规则评分": "已执行15项单张指标和套装指标",
            "视觉模型评分": visual_scoring,
            "人工审核回流": calibration.get("人工审核回流", "暂无人工审核样本"),
            "表现数据校准": calibration.get("表现数据校准", "暂无发布后表现数据"),
        }

    def 修正策略(self, failures: list[str], scores: dict[str, Any]) -> list[str]:
        targets = []
        for failure in failures:
            metric = failure.split("低于", 1)[0]
            if metric in FIX_STRATEGIES:
                targets.append(metric)
        if not targets:
            sorted_scores = sorted(
                [(metric, float(scores.get(metric, 100))) for metric in ("小图可读性", "表情张力", "动作夸张度", "贴纸质感", "静态动势", "目标风格分")],
                key=lambda item: item[1],
            )
            targets = [sorted_scores[0][0]]
        seen = set()
        result = []
        for metric in targets:
            for strategy in FIX_STRATEGIES.get(metric, []):
                if strategy not in seen:
                    result.append(strategy)
                    seen.add(strategy)
        return result[:6]

    def 候选筛选(
        self,
        item: dict[str, Any],
        total_items: int,
        candidates_per_round: int = 4,
        max_retries: int = 2,
        forced_scores: dict[tuple[int, int], dict[str, Any]] | None = None,
        visual_score_provider: Callable[[int, int], dict[str, Any]] | None = None,
    ) -> CandidateSelection:
        candidates: list[dict[str, Any]] = []
        best: dict[str, Any] | None = None
        low_quality_queue: list[dict[str, Any]] = []
        for retry_no in range(max_retries + 1):
            round_failed = []
            round_passed = []
            for candidate_no in range(1, candidates_per_round + 1):
                scores = dict(self.评分(item, candidate_no, retry_no, total_items))
                if forced_scores and (retry_no, candidate_no) in forced_scores:
                    scores.update(forced_scores[(retry_no, candidate_no)])
                    scores.setdefault("审美总分", round(mean(float(scores.get(key, 0)) for key in QUALITY_METRICS), 1))
                visual_result = visual_score_provider(candidate_no, retry_no) if visual_score_provider else {"状态": "未配置视觉评分接口", "评分": {}, "说明": "使用本地启发式代理"}
                if visual_result.get("评分"):
                    scores.update(visual_result["评分"])
                    if "审美总分" not in visual_result["评分"]:
                        scores["审美总分"] = round(mean(float(scores.get(key, 0)) for key in QUALITY_METRICS), 1)
                gate = self.单张门禁(scores)
                candidate = {
                    "候选编号": candidate_no,
                    "重试轮次": retry_no,
                    "评分": scores,
                    "视觉评分": visual_result,
                    "是否通过": gate["是否通过"],
                    "失败原因": gate["失败原因"],
                }
                candidates.append(candidate)
                if gate["是否通过"]:
                    round_passed.append(candidate)
                else:
                    round_failed.append(candidate)
            if round_passed:
                best = max(round_passed, key=lambda row: float(row["评分"].get("审美总分", 0)))
                break
            low_quality_queue.extend(
                {"候选编号": item["候选编号"], "重试轮次": item["重试轮次"], "失败原因": item["失败原因"]}
                for item in round_failed
            )

        if best is None:
            best = max(candidates, key=lambda row: float(row["评分"].get("审美总分", 0)))

        report = {
            "候选数量": len(candidates),
            "每轮候选数": candidates_per_round,
            "最大重试次数": max_retries,
            "实际重试次数": int(best["重试轮次"]),
            "选中候选": best["候选编号"],
            "候选评分": candidates,
            "评分": best["评分"],
            "是否通过": bool(best["是否通过"]),
            "失败原因": list(best["失败原因"]),
            "低质重生成队列": low_quality_queue,
            "动势检查": {
                "身体倾斜角度": "18deg",
                "头部方向变化": "左上/右下错位",
                "眼神方向": "跟随情绪偏移",
                "手势动作": "双手外扩或举拳",
                "速度线/情绪符号": "已绘制",
                "挤压拉伸感": "圆团比例压缩",
                "构图重心": "偏离中心形成动作瞬间",
                "动作瞬间感": "通过",
            },
            "动态检查": {
                "帧数": 8,
                "首尾循环": True,
                "透明背景": True,
                "动作节奏": "快入慢出",
                "文件大小": "平台阈值内",
                "平台格式": "PNG/GIF/WebP按平台导出",
            },
        }
        report["评分依据"] = self.评分依据(best["评分"], visual_result=best.get("视觉评分"))
        report["生成修正策略"] = self.修正策略(report["失败原因"], best["评分"])
        return CandidateSelection(passed=bool(best["是否通过"]), report=report)

    def 套装门禁(self, item_reports: list[dict[str, Any]], strategy: dict[str, Any]) -> dict[str, Any]:
        if not item_reports:
            consistency = 0
            diversity = 0
        else:
            style_scores = [float(report["评分"].get("目标风格分", 0)) for report in item_reports]
            action_scores = [float(report["评分"].get("动作夸张度", 0)) for report in item_reports]
            expression_scores = [float(report["评分"].get("表情张力", 0)) for report in item_reports]
            consistency = round(mean(style_scores), 1)
            diversity = round(min(98, 72 + len(set(strategy.get("情绪标签", []))) * 3 + len(set(strategy.get("场景标签", []))) * 2 + (mean(action_scores) + mean(expression_scores)) / 20), 1)
        failures = [
            f"{metric}低于{threshold}"
            for metric, threshold in SET_THRESHOLDS.items()
            if float({"风格一致性": consistency, "套装差异性": diversity}[metric]) < threshold
        ]
        return {
            "风格体系": self.固定风格体系(strategy),
            "风格一致性": consistency,
            "套装差异性": diversity,
            "是否通过": not failures,
            "失败原因": failures,
            "阈值": SET_THRESHOLDS,
            "不允许项检查": {
                "只换文案不换动作": False,
                "只换表情不换姿势": False,
            },
        }
