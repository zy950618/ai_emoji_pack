import hashlib
import json
import math
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.audit import 审计服务
from app.database import 数据库
from app.rule_governance import 平台规则治理服务


class 资产校验服务:
    def __init__(self, 数据库实例: 数据库, 审计: 审计服务, 规则治理: 平台规则治理服务) -> None:
        self.数据库 = 数据库实例
        self.审计 = 审计
        self.规则治理 = 规则治理

    def 校验(self, 操作人编号: str, 平台名称: str, 套装编号: str, 文件路径: list[str]) -> dict[str, object]:
        规则 = self.规则治理.获取当前规则(平台名称)
        文件结果: list[dict[str, object]] = []
        错误列表: list[dict[str, object]] = []

        数量 = len(文件路径)
        if 数量 < 规则.最少数量 or 数量 > 规则.最多数量:
            错误列表.append(
                {
                    "文件名": "套装",
                    "规则": "套装数量",
                    "错误": f"当前数量{数量}不在{规则.最少数量}-{规则.最多数量}范围内",
                    "修复建议": "调整资产数量后重新校验",
                }
            )

        for raw_path in 文件路径:
            result = self._校验单文件(raw_path, 规则, 错误列表)
            文件结果.append(result)

        报告编号 = f"ASSET-{uuid.uuid4().hex[:12]}"
        是否通过 = not 错误列表
        self.数据库.执行(
            """
            INSERT INTO asset_validation_reports (报告编号, 平台名称, 套装编号, 是否通过, 文件结果, 错误列表)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                报告编号,
                平台名称,
                套装编号,
                int(是否通过),
                json.dumps(文件结果, ensure_ascii=False),
                json.dumps(错误列表, ensure_ascii=False),
            ),
        )
        self.审计.记录(
            操作人编号,
            "资产文件校验",
            "套装",
            套装编号,
            {"平台名称": 平台名称, "报告编号": 报告编号, "是否通过": 是否通过},
        )
        return {
            "报告编号": 报告编号,
            "平台名称": 平台名称,
            "套装编号": 套装编号,
            "规则版本": 规则.规则版本,
            "是否通过": 是否通过,
            "文件结果": 文件结果,
            "错误列表": 错误列表,
        }

    def 报告列表(self) -> list[dict[str, object]]:
        rows = self.数据库.查询全部("SELECT * FROM asset_validation_reports ORDER BY 创建时间 ASC")
        return [
            {
                "报告编号": row["报告编号"],
                "平台名称": row["平台名称"],
                "套装编号": row["套装编号"],
                "是否通过": bool(row["是否通过"]),
                "文件结果": json.loads(row["文件结果"]),
                "错误列表": json.loads(row["错误列表"]),
                "创建时间": row["创建时间"],
            }
            for row in rows
        ]

    def _校验单文件(self, raw_path: str, 规则, 错误列表: list[dict[str, object]]) -> dict[str, object]:
        path = Path(raw_path)
        文件名 = path.name or raw_path
        if not path.exists():
            self._添加错误(错误列表, 文件名, "文件存在", "文件不存在", "确认生成文件路径并重新校验")
            return {"文件名": 文件名, "文件路径": raw_path, "可打开": False, "文件指纹": None}
        if not path.is_file():
            self._添加错误(错误列表, 文件名, "文件存在", "路径不是文件", "传入具体图片文件路径")
            return {"文件名": 文件名, "文件路径": raw_path, "可打开": False, "文件指纹": None}

        content = path.read_bytes()
        fingerprint = hashlib.sha256(content).hexdigest()
        size_kb = math.ceil(len(content) / 1024)

        try:
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                fmt = (image.format or "").upper()
                has_transparency = self._有透明背景(image)
        except (OSError, UnidentifiedImageError):
            self._添加错误(错误列表, 文件名, "文件可打开", "图片文件无法打开", "重新导出未损坏的图片文件")
            return {
                "文件名": 文件名,
                "文件路径": raw_path,
                "可打开": False,
                "文件大小KB": size_kb,
                "文件指纹": fingerprint,
            }

        if width != 规则.宽度 or height != 规则.高度:
            self._添加错误(错误列表, 文件名, "尺寸", f"当前尺寸{width}x{height}，要求{规则.宽度}x{规则.高度}", "按目标平台尺寸重新导出")
        if fmt not in 规则.允许格式:
            self._添加错误(错误列表, 文件名, "格式", f"当前格式{fmt}不在允许格式内", f"转换为{','.join(规则.允许格式)}")
        if size_kb > 规则.最大文件大小KB:
            self._添加错误(错误列表, 文件名, "文件大小", f"当前{size_kb}KB超过{规则.最大文件大小KB}KB", "压缩文件后重新校验")
        if 规则.要求透明背景 and not has_transparency:
            self._添加错误(错误列表, 文件名, "透明背景", "目标平台要求透明背景", "导出透明背景版本")

        return {
            "文件名": 文件名,
            "文件路径": raw_path,
            "可打开": True,
            "宽度": width,
            "高度": height,
            "格式": fmt,
            "文件大小KB": size_kb,
            "透明背景": has_transparency,
            "文件指纹": fingerprint,
        }

    @staticmethod
    def _有透明背景(image: Image.Image) -> bool:
        if image.mode in {"RGBA", "LA"}:
            alpha = image.getchannel("A")
            return alpha.getextrema()[0] < 255
        if image.mode == "P" and "transparency" in image.info:
            return True
        return False

    @staticmethod
    def _添加错误(错误列表: list[dict[str, object]], 文件名: str, 规则: str, 错误: str, 修复建议: str) -> None:
        错误列表.append({"文件名": 文件名, "规则": 规则, "错误": 错误, "修复建议": 修复建议})
