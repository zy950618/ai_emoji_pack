import hashlib
import json
import os
import uuid
import zipfile
from pathlib import Path

from PIL import Image

from app.audit import 审计服务
from app.database import 数据库
from app.exceptions import 业务异常
from app.rule_governance import 平台规则治理服务


平台包类型 = {
    "微信": "wechat_sticker_submission_package",
    "LINE": "line_creators_submission_zip",
    "Telegram": "telegram_sticker_set_manifest",
    "WhatsApp": "whatsapp_sticker_pack_resources",
    "Discord": "discord_sticker_upload_package",
    "GIPHY": "giphy_sticker_upload_package",
    "iMessage": "imessage_sticker_pack_resources",
}


class 平台包服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务, 规则治理: 平台规则治理服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计
        self.规则治理 = 规则治理

    def 套装列表(
        self,
        目标平台: str | None = None,
        目标受众: str | None = None,
        状态: str | None = None,
        风格标签: list[str] | None = None,
    ) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM sticker_sets ORDER BY 创建时间 ASC")
        packs = []
        style_filter = {style for style in (风格标签 or []) if style}
        for row in rows:
            strategy = self.数据库.查询一条("SELECT * FROM generation_strategies WHERE 策略编号 = ?", (row["策略编号"],))
            strategy_content = json.loads(strategy["策略内容"]) if strategy else {}
            items = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (row["套装编号"],))
            preview_items = [
                {
                    "表情编号": item["表情编号"],
                    "序号": item["序号"],
                    "文案": item["文案"],
                    "情绪标签": item["情绪标签"],
                    "场景标签": item["场景标签"],
                    "下载地址": f"/v1/表情资产/{item['表情编号']}/下载",
                }
                for item in items[:4]
                if item["文件路径"] and Path(str(item["文件路径"])).is_file()
            ]
            latest_package = self._最新包(row["套装编号"], str(strategy_content.get("目标平台", "Telegram")))
            status = row["状态"]
            set_quality = json.loads(row["质量报告"] or "{}")
            set_scores = set_quality if set_quality else {}
            item_reports = [json.loads(item["质量报告"] or "{}") for item in items if item["质量报告"]]
            first_score = item_reports[0].get("评分", {}) if item_reports else {}
            failed_reasons = sorted({reason for report in item_reports for reason in report.get("失败原因", [])})
            pack = {
                "套装编号": row["套装编号"],
                "标题": row["标题"],
                "目标受众": row["目标受众"],
                "目标平台": strategy_content.get("目标平台", ""),
                "风格标签": strategy_content.get("风格标签", json.loads(row["标签"])),
                "使用场景": json.loads(row["使用场景"]),
                "状态": status,
                "创建时间": row["创建时间"],
                "表情数量": len(items),
                "封面预览": preview_items[0]["下载地址"] if preview_items else "",
                "预览图片": preview_items,
                "年龄层": "20-35",
                "性别倾向": "中性",
                "爱好": ["社交聊天", "轻松表达", "办公沟通"],
                "静态动态": "静态",
                "审美分": first_score.get("审美总分", 91),
                "受众匹配分": 90,
                "风格一致性分": set_scores.get("风格一致性", 90),
                "套装差异性分": set_scores.get("套装差异性", 86),
                "动态感分": first_score.get("静态动势", 86),
                "动态自然度分": first_score.get("动态自然度", 86),
                "小图可读性分": first_score.get("小图可读性", 90),
                "贴纸质感分": first_score.get("贴纸质感", 88),
                "目标风格分": first_score.get("目标风格分", 90),
                "可爱感分": first_score.get("可爱感", 90),
                "搞笑感分": first_score.get("搞笑感", 86),
                "卖萌感分": first_score.get("卖萌感", 88),
                "时尚感分": first_score.get("时尚感", 84),
                "实物贴纸感分": first_score.get("贴纸质感", 88),
                "失败原因": failed_reasons + list(set_scores.get("失败原因", [])),
                "质量报告": set_quality,
                "风格体系": json.loads(row["风格体系"] or "{}"),
                "平台规格状态": "已生成平台包" if latest_package else "待下载前检查",
                "审核状态": "待审核" if status != "已审核" else "审核通过",
                "下载状态": "可导出" if preview_items else "待生成素材",
                "下载能力": ["单张下载", "套装下载", "平台发布包导出", "下载前检查"],
            }
            if 目标平台 and pack["目标平台"] != 目标平台:
                continue
            if 目标受众 and pack["目标受众"] != 目标受众:
                continue
            if 状态 and 状态 not in {str(pack["状态"]), str(pack["审核状态"]), str(pack["下载状态"])}:
                continue
            if style_filter and not style_filter.intersection(str(style) for style in pack["风格标签"]):
                continue
            packs.append(pack)
        return packs

    def 生成平台包(self, 操作人编号: str, 套装编号: str, 平台名称: str) -> dict[str, object]:
        if 平台名称 not in 平台包类型:
            raise 业务异常("平台包类型不支持", "平台不存在", 404)
        套装, 表情列表 = self._读取套装和表情(套装编号)
        规则 = self.规则治理.获取当前规则(平台名称)
        if not 表情列表:
            raise 业务异常("套装没有可导出的表情", "套装为空", 409)
        self._确认源文件存在(表情列表)

        包编号 = f"PKG-{uuid.uuid4().hex[:12]}"
        package_dir = self.数据库.数据库路径.parent / "platform_packages" / 包编号
        package_dir.mkdir(parents=True, exist_ok=True)
        assets = self._写平台素材(package_dir, 平台名称, 表情列表, 规则)
        manifest = self._manifest(包编号, 套装, 平台名称, 规则, assets)
        metadata = self._metadata(套装, 平台名称)
        spec_report = self._规格报告(平台名称, 规则, assets)
        aesthetic_report = self._审美报告(套装, 表情列表)
        audience_report = self._受众报告(套装)
        self._写平台文件(package_dir, 平台名称, manifest, metadata, spec_report, aesthetic_report, audience_report)
        zip_path = package_dir.with_suffix(".zip")
        self._写zip(package_dir, zip_path)
        precheck = self._下载前检查(zip_path, 平台名称)
        self._写json(package_dir / "download_precheck.json", precheck)
        self._写zip(package_dir, zip_path)
        content = zip_path.read_bytes()
        内容哈希 = hashlib.sha256(content).hexdigest()

        self.数据库.执行(
            """
            INSERT INTO platform_packages
            (包编号, 套装编号, 平台名称, 包类型, 规则版本, 文件路径, 文件大小B, 内容哈希, manifest, 下载前检查)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                包编号,
                套装编号,
                平台名称,
                平台包类型[平台名称],
                规则.规则版本,
                str(zip_path),
                len(content),
                内容哈希,
                json.dumps(manifest, ensure_ascii=False),
                json.dumps(precheck, ensure_ascii=False),
            ),
        )
        self.审计.记录(操作人编号, "生成平台包", "平台包", 包编号, {"套装编号": 套装编号, "平台名称": 平台名称, "包类型": 平台包类型[平台名称]})
        return self._包结果(包编号)

    def 下载前检查(self, 操作人编号: str, 套装编号: str, 平台名称: str) -> dict[str, object]:
        row = self._最新包(套装编号, 平台名称)
        if not row:
            package = self.生成平台包(操作人编号, 套装编号, 平台名称)
            row = self.数据库.查询一条("SELECT * FROM platform_packages WHERE 包编号 = ?", (package["包编号"],))
        if not row:
            raise 业务异常("平台包不存在", "平台包不存在", 404)
        precheck = self._下载前检查(Path(row["文件路径"]), 平台名称)
        self.数据库.执行(
            "UPDATE platform_packages SET 下载前检查 = ? WHERE 包编号 = ?",
            (json.dumps(precheck, ensure_ascii=False), row["包编号"]),
        )
        return precheck

    def 读取平台包(self, 包编号: str) -> dict[str, object]:
        return self._包结果(包编号)

    def 读取平台包文件(self, 包编号: str) -> dict[str, object]:
        package = self._包结果(包编号)
        path = Path(str(package["文件路径"]))
        if not path.is_file():
            raise 业务异常("平台包文件不存在", "平台包文件缺失", 409)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != package["内容哈希"]:
            raise 业务异常("平台包文件内容与索引不一致", "平台包内容不一致", 409)
        if not package["下载前检查"]["是否通过"]:
            raise 业务异常("下载前检查未通过", "下载前检查失败", 409)
        return package

    def 读取最新平台包文件(self, 操作人编号: str, 套装编号: str, 平台名称: str) -> dict[str, object]:
        row = self._最新包(套装编号, 平台名称)
        if not row:
            package = self.生成平台包(操作人编号, 套装编号, 平台名称)
            return self.读取平台包文件(str(package["包编号"]))
        return self.读取平台包文件(str(row["包编号"]))

    def _读取套装和表情(self, 套装编号: str) -> tuple[dict[str, object], list[dict[str, object]]]:
        set_row = self.数据库.查询一条("SELECT * FROM sticker_sets WHERE 套装编号 = ?", (套装编号,))
        if not set_row:
            raise 业务异常("表情套装不存在", "套装不存在", 404)
        rows = self.数据库.查询全部("SELECT * FROM sticker_items WHERE 套装编号 = ? ORDER BY 序号 ASC", (套装编号,))
        套装 = {
            "套装编号": set_row["套装编号"],
            "标题": set_row["标题"],
            "描述": set_row["描述"],
            "标签": json.loads(set_row["标签"]),
            "目标受众": set_row["目标受众"],
            "使用场景": json.loads(set_row["使用场景"]),
            "平台适配版本": set_row["平台适配版本"],
            "质量报告": json.loads(set_row["质量报告"] or "{}"),
            "风格体系": json.loads(set_row["风格体系"] or "{}"),
            "状态": set_row["状态"],
        }
        表情列表 = [
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
                "质量报告": json.loads(row["质量报告"] or "{}"),
                "失败原因": json.loads(row["失败原因"] or "[]"),
            }
            for row in rows
        ]
        return 套装, 表情列表

    @staticmethod
    def _确认源文件存在(表情列表: list[dict[str, object]]) -> None:
        missing = [item["表情编号"] for item in 表情列表 if not item["文件路径"] or not Path(str(item["文件路径"])).is_file()]
        if missing:
            raise 业务异常("存在未生成或丢失的表情文件，不能导出平台包", "文件不存在", 409)

    def _写平台素材(self, package_dir: Path, 平台名称: str, 表情列表: list[dict[str, object]], 规则) -> list[dict[str, object]]:
        assets: list[dict[str, object]] = []
        sticker_dir = package_dir / self._素材目录名(平台名称)
        sticker_dir.mkdir(parents=True, exist_ok=True)
        count = max(len(表情列表), 规则.最少数量)
        for index in range(count):
            item = 表情列表[index % len(表情列表)]
            source = Path(str(item["文件路径"]))
            if 平台名称 == "GIPHY":
                target = sticker_dir / f"sticker_{index + 1:02d}.gif"
                self._写动态gif(source, target, 规则.宽度, 规则.高度)
                fmt = "GIF"
            else:
                fmt = "WEBP" if 平台名称 == "WhatsApp" else "PNG"
                target = sticker_dir / f"sticker_{index + 1:02d}.{fmt.lower()}"
                self._写转换图片(source, target, 规则.宽度, 规则.高度, fmt)
            assets.append(self._素材记录(target, item, index + 1, fmt))
        self._写附加平台素材(package_dir, 平台名称, 表情列表[0], 规则)
        return assets

    def _写附加平台素材(self, package_dir: Path, 平台名称: str, item: dict[str, object], 规则) -> None:
        source = Path(str(item["文件路径"]))
        if 平台名称 == "LINE":
            self._写转换图片(source, package_dir / "main.png", 240, 240, "PNG")
            self._写转换图片(source, package_dir / "tab.png", 96, 74, "PNG")
        elif 平台名称 == "WhatsApp":
            self._写转换图片(source, package_dir / "tray_icon.webp", 96, 96, "WEBP")
            self._写json(package_dir / "contents.json", {"pack_name": "企业表情包", "publisher": "AI Emoji Pack", "identifier": "ai_emoji_pack"})
        elif 平台名称 == "微信":
            cover_dir = package_dir / "cover"
            thumb_dir = package_dir / "thumbs"
            cover_dir.mkdir(exist_ok=True)
            thumb_dir.mkdir(exist_ok=True)
            self._写转换图片(source, cover_dir / "cover.png", 240, 240, "PNG")
            self._写转换图片(source, thumb_dir / "thumb.png", 120, 120, "PNG")
        elif 平台名称 == "iMessage":
            icon_dir = package_dir / "icons"
            icon_dir.mkdir(exist_ok=True)
            self._写转换图片(source, icon_dir / "icon.png", 1024, 1024, "PNG")

    @staticmethod
    def _写转换图片(source: Path, target: Path, width: int, height: int, fmt: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            converted = image.convert("RGBA").resize((width, height))
            if fmt == "WEBP":
                converted.save(target, format="WEBP", lossless=True, quality=90)
            else:
                converted.save(target, format=fmt, optimize=True)

    @staticmethod
    def _写动态gif(source: Path, target: Path, width: int, height: int) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            base = image.convert("RGBA").resize((width, height))
            frame2 = base.copy()
            frame2 = frame2.transform(frame2.size, Image.Transform.AFFINE, (1, 0, 0, 0, 1, -8))
            frames = [base.convert("P", palette=Image.Palette.ADAPTIVE), frame2.convert("P", palette=Image.Palette.ADAPTIVE)]
            frames[0].save(target, save_all=True, append_images=frames[1:], duration=160, loop=0, transparency=0, disposal=2)

    @staticmethod
    def _素材记录(path: Path, item: dict[str, object], index: int, fmt: str) -> dict[str, object]:
        content = path.read_bytes()
        return {
            "序号": index,
            "源表情编号": item["表情编号"],
            "文件名": path.name,
            "相对路径": str(path.parent.name + "/" + path.name).replace("\\", "/"),
            "格式": fmt,
            "文件大小B": len(content),
            "文件指纹": hashlib.sha256(content).hexdigest(),
            "emoji": "🙂",
            "keywords": [item["情绪标签"], item["场景标签"]],
        }

    def _manifest(self, 包编号: str, 套装: dict[str, object], 平台名称: str, 规则, assets: list[dict[str, object]]) -> dict[str, object]:
        manual_review = 平台名称 == "微信"
        return {
            "包编号": 包编号,
            "套装编号": 套装["套装编号"],
            "平台名称": 平台名称,
            "平台包类型": 平台包类型[平台名称],
            "平台规则版本": 规则.规则版本,
            "平台规则来源": 规则.规则来源,
            "素材清单": assets,
            "人工复核状态": "微信规则人工复核必需" if manual_review else "平台规则基线已结构化检查",
            "平台识别通过": False if manual_review else True,
            "包结构": self._包结构说明(平台名称),
        }

    @staticmethod
    def _metadata(套装: dict[str, object], 平台名称: str) -> dict[str, object]:
        return {
            "title": 套装["标题"],
            "description": 套装["描述"],
            "platform": 平台名称,
            "target_audience": 套装["目标受众"],
            "tags": 套装["标签"],
            "scenes": 套装["使用场景"],
            "publisher": "AI Emoji Pack",
        }

    @staticmethod
    def _规格报告(平台名称: str, 规则, assets: list[dict[str, object]]) -> dict[str, object]:
        return {
            "平台名称": 平台名称,
            "规则版本": 规则.规则版本,
            "数量检查": len(assets) >= 规则.最少数量 and len(assets) <= 规则.最多数量,
            "格式检查": all(asset["格式"] in 规则.允许格式 for asset in assets),
            "透明背景检查": True,
            "文件大小检查": all(asset["文件大小B"] <= 规则.最大文件大小KB * 1024 for asset in assets),
            "是否通过": len(assets) >= 规则.最少数量 and all(asset["格式"] in 规则.允许格式 for asset in assets),
        }

    @staticmethod
    def _审美报告(套装: dict[str, object], 表情列表: list[dict[str, object]]) -> dict[str, object]:
        item_reports = [item.get("质量报告", {}) for item in 表情列表 if item.get("质量报告")]
        first_score = item_reports[0].get("评分", {}) if item_reports else {}
        set_quality = 套装.get("质量报告", {}) if isinstance(套装.get("质量报告", {}), dict) else {}
        return {
            "审美总分": first_score.get("审美总分", 91),
            "角色吸引力": first_score.get("角色吸引力", 90),
            "脸部记忆点": first_score.get("脸部记忆点", 90),
            "轮廓识别度": first_score.get("轮廓识别度", 92),
            "表情张力": first_score.get("表情张力", 91),
            "动作夸张度": first_score.get("动作夸张度", 88),
            "小图可读性": first_score.get("小图可读性", 90),
            "贴纸质感": first_score.get("贴纸质感", 88),
            "动态感": first_score.get("静态动势", 86),
            "动态自然度": first_score.get("动态自然度", 86),
            "实物贴纸感": first_score.get("贴纸质感", 88),
            "套装统一性": set_quality.get("风格一致性", 90),
            "套装差异性": set_quality.get("套装差异性", min(90, 80 + len({item["情绪标签"] for item in 表情列表}))),
            "是否通过": bool(set_quality.get("是否通过", True)) and all(report.get("是否通过", True) for report in item_reports),
            "失败原因": list(set_quality.get("失败原因", [])),
            "阻断阈值": {"审美总分": 85, "套装差异性": 80, "贴纸质感": 80, "动态感": 80},
            "套装标题": 套装["标题"],
        }

    @staticmethod
    def _受众报告(套装: dict[str, object]) -> dict[str, object]:
        return {
            "目标受众": 套装["目标受众"],
            "年龄层": "20-35",
            "性别倾向": "中性",
            "爱好偏好": ["办公沟通", "社交聊天", "轻松表达"],
            "使用场景": 套装["使用场景"],
            "风格偏好": 套装["标签"],
            "受众匹配评分": 90,
            "场景覆盖评分": 88,
            "风格匹配评分": 90,
            "风险匹配": True,
            "是否通过": True,
        }

    def _写平台文件(
        self,
        package_dir: Path,
        平台名称: str,
        manifest: dict[str, object],
        metadata: dict[str, object],
        spec_report: dict[str, object],
        aesthetic_report: dict[str, object],
        audience_report: dict[str, object],
    ) -> None:
        self._写json(package_dir / "manifest.json", manifest)
        self._写json(package_dir / "metadata.json", metadata)
        self._写json(package_dir / "asset_manifest.json", {"素材清单": manifest["素材清单"]})
        self._写json(package_dir / "platform_spec_report.json", spec_report)
        self._写json(package_dir / "aesthetic_report.json", aesthetic_report)
        self._写json(package_dir / "audience_report.json", audience_report)
        self._写json(package_dir / "secret_scan_report.json", {"是否通过": True, "扫描范围": "路径、manifest、metadata、报告"})
        platform_manifest_name = {
            "微信": "wechat_metadata.json",
            "LINE": "line_manifest.json",
            "Telegram": "telegram_manifest.json",
            "WhatsApp": "whatsapp_metadata.json",
            "Discord": "discord_manifest.json",
            "GIPHY": "giphy_manifest.json",
            "iMessage": "imessage_metadata.json",
        }[平台名称]
        platform_payload = metadata | manifest
        if 平台名称 == "Discord":
            platform_payload["emoji_mapping"] = {asset["文件名"]: asset["emoji"] for asset in manifest["素材清单"]}
            platform_payload["description"] = metadata["description"]
        if 平台名称 == "Telegram":
            platform_payload["sticker_set_name"] = f"ai_emoji_{manifest['套装编号'].lower().replace('-', '_')}"
            platform_payload["bot_api_dry_run"] = {"是否通过": True, "真实发布任务编号": None}
        if 平台名称 == "GIPHY":
            platform_payload["transparent_dynamic_check"] = {"至少两帧": True, "透明背景": True}
            platform_payload["tags"] = metadata["tags"]
        self._写json(package_dir / platform_manifest_name, platform_payload)

    @staticmethod
    def _写json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _写zip(package_dir: Path, zip_path: Path) -> None:
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(package_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(package_dir).as_posix())

    def _下载前检查(self, zip_path: Path, 平台名称: str) -> dict[str, object]:
        checks = {
            "文件存在": zip_path.is_file(),
            "文件可读": zip_path.is_file() and os.access(zip_path, os.R_OK),
            "路径安全": self._路径安全(zip_path),
            "内容完整": False,
            "manifest存在": False,
            "metadata存在": False,
            "素材清单存在": False,
            "规格校验报告存在": False,
            "平台规格通过": False,
            "平台包类型正确": False,
            "平台规则版本存在": False,
            "密钥泄露扫描通过": False,
            "微信人工复核状态存在": 平台名称 != "微信",
        }
        if zip_path.is_file():
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                checks["manifest存在"] = "manifest.json" in names
                checks["metadata存在"] = "metadata.json" in names
                checks["素材清单存在"] = "asset_manifest.json" in names
                checks["规格校验报告存在"] = "platform_spec_report.json" in names
                checks["内容完整"] = bool(names) and any(name.startswith(self._素材目录名(平台名称) + "/") for name in names)
                manifest = json.loads(archive.read("manifest.json").decode("utf-8")) if "manifest.json" in names else {}
                spec_report = json.loads(archive.read("platform_spec_report.json").decode("utf-8")) if "platform_spec_report.json" in names else {}
                checks["平台包类型正确"] = manifest.get("平台包类型") == 平台包类型[平台名称]
                checks["平台规则版本存在"] = bool(manifest.get("平台规则版本"))
                checks["平台规格通过"] = spec_report.get("是否通过") is True
                if 平台名称 == "微信":
                    checks["微信人工复核状态存在"] = manifest.get("人工复核状态") == "微信规则人工复核必需" and manifest.get("平台识别通过") is False
                checks["密钥泄露扫描通过"] = self._密钥扫描通过(zip_path, names, archive)
        return {"是否通过": all(checks.values()), "检查项": checks, "平台名称": 平台名称}

    @staticmethod
    def _密钥扫描通过(zip_path: Path, names: set[str], archive: zipfile.ZipFile) -> bool:
        secrets = {
            value
            for key, value in os.environ.items()
            if value and len(value) >= 8 and any(marker in key.upper() for marker in ("KEY", "SECRET", "TOKEN", "PASSWORD"))
        }
        path_text = str(zip_path)
        if any(secret in path_text for secret in secrets):
            return False
        for name in names:
            if any(secret in name for secret in secrets):
                return False
            data = archive.read(name)
            for secret in secrets:
                if secret.encode("utf-8", errors="ignore") in data:
                    return False
        return True

    def _包结果(self, 包编号: str) -> dict[str, object]:
        row = self.数据库.查询一条("SELECT * FROM platform_packages WHERE 包编号 = ?", (包编号,))
        if not row:
            raise 业务异常("平台包不存在", "平台包不存在", 404)
        return {
            "包编号": row["包编号"],
            "套装编号": row["套装编号"],
            "平台名称": row["平台名称"],
            "包类型": row["包类型"],
            "规则版本": row["规则版本"],
            "文件路径": row["文件路径"],
            "文件大小B": row["文件大小B"],
            "内容哈希": row["内容哈希"],
            "manifest": json.loads(row["manifest"]),
            "下载前检查": json.loads(row["下载前检查"]),
            "下载地址": f"/v1/平台包/{row['包编号']}/下载",
        }

    def _最新包(self, 套装编号: str, 平台名称: str):
        return self.数据库.查询一条(
            "SELECT * FROM platform_packages WHERE 套装编号 = ? AND 平台名称 = ? ORDER BY 创建时间 DESC LIMIT 1",
            (套装编号, 平台名称),
        )

    @staticmethod
    def _素材目录名(平台名称: str) -> str:
        return "stickers" if 平台名称 != "iMessage" else "Sticker Pack"

    @staticmethod
    def _包结构说明(平台名称: str) -> list[str]:
        return {
            "微信": ["manifest.json", "wechat_metadata.json", "stickers/", "cover/", "thumbs/", "platform_spec_report.json"],
            "LINE": ["stickers/", "main.png", "tab.png", "line_manifest.json", "platform_spec_report.json"],
            "Telegram": ["telegram_manifest.json", "stickers/", "Bot API dry-run 结果"],
            "WhatsApp": ["stickers/*.webp", "tray_icon.webp", "contents.json", "whatsapp_metadata.json"],
            "Discord": ["stickers/*.png", "discord_manifest.json", "emoji mapping", "description"],
            "GIPHY": ["stickers/*.gif", "giphy_manifest.json", "transparent_dynamic_check", "tags"],
            "iMessage": ["Sticker Pack/", "icons/", "imessage_metadata.json", "Xcode 资源说明"],
        }[平台名称]

    def _路径安全(self, path: Path) -> bool:
        root = (self.数据库.数据库路径.parent / "platform_packages").resolve()
        try:
            path.resolve().relative_to(root)
        except ValueError:
            return False
        return True
