from typing import Any

from pydantic import BaseModel, Field


class 标准响应(BaseModel):
    成功: bool
    消息: str
    数据: Any | None = None
    错误码: str | None = None


class 创建任务请求(BaseModel):
    任务名称: str = Field(min_length=1)
    任务类型: str = Field(min_length=1)
    幂等键: str | None = Field(default=None, min_length=1)


class 任务流转请求(BaseModel):
    目标状态: str = Field(min_length=1)


class 创建定时任务请求(BaseModel):
    任务名称: str = Field(min_length=1)
    任务类型: str = Field(min_length=1)
    执行周期: str = Field(min_length=1)
    目标平台: list[str] = Field(min_length=1)
    目标受众: list[str] = Field(min_length=1)
    目标风格: list[str] = Field(min_length=1)
    风险阈值: str = Field(min_length=1)
    是否自动进入审核: bool
    是否自动发布: bool


class 执行定时任务请求(BaseModel):
    定时任务编号: str | None = Field(default=None, min_length=1)


class 表情文件描述(BaseModel):
    文件名: str = Field(min_length=1)
    宽度: int = Field(gt=0)
    高度: int = Field(gt=0)
    格式: str = Field(min_length=1)
    文件大小KB: int = Field(gt=0)
    是否透明背景: bool


class 平台规则校验请求(BaseModel):
    平台名称: str = Field(min_length=1)
    套装编号: str = Field(min_length=1)
    是否只检查: bool = True
    表情文件: list[表情文件描述] = Field(default_factory=list)


class 资产文件校验请求(BaseModel):
    平台名称: str = Field(min_length=1)
    套装编号: str = Field(min_length=1)
    文件路径: list[str] = Field(min_length=1)


class 表情套装验收请求(BaseModel):
    套装编号: str = Field(min_length=1)


class 创建平台规则版本请求(BaseModel):
    平台名称: str = Field(min_length=1)
    规则版本: str = Field(min_length=1)
    规则来源: str = Field(min_length=1)
    最少数量: int = Field(ge=1)
    最多数量: int = Field(ge=1)
    宽度: int = Field(gt=0)
    高度: int = Field(gt=0)
    允许格式: list[str] = Field(min_length=1)
    最大文件大小KB: int = Field(gt=0)
    要求透明背景: bool
    支持自动发布: bool = False
    需要人工复核: bool = True
    合法样例: dict[str, object] = Field(min_length=1)
    非法样例: dict[str, object] = Field(min_length=1)
    变更原因: str = Field(min_length=1)


class 启用平台规则版本请求(BaseModel):
    平台名称: str = Field(min_length=1)
    规则版本: str = Field(min_length=1)
    启用原因: str = Field(min_length=1)


class 回滚平台规则版本请求(BaseModel):
    平台名称: str = Field(min_length=1)
    目标版本: str = Field(min_length=1)
    回滚原因: str = Field(min_length=1)


class 创建受众画像请求(BaseModel):
    画像名称: str = Field(min_length=1)
    年龄段: str = Field(min_length=1)
    兴趣标签: list[str] = Field(min_length=3)
    使用场景: list[str] = Field(min_length=3)
    风格偏好: list[str] = Field(min_length=1)
    禁用内容: list[str] = Field(min_length=1)
    风险等级: str = Field(min_length=1)


class 创建热点请求(BaseModel):
    热点名称: str = Field(min_length=1)
    热点来源: str = Field(min_length=1)
    热度分: int = Field(ge=0, le=100)
    生命周期: str = Field(min_length=1)
    风险分: int = Field(ge=0, le=100)
    受众匹配: list[str] = Field(min_length=1)
    风险标签: list[str] = Field(default_factory=list)


class 创建原创角色请求(BaseModel):
    角色名称: str = Field(min_length=1)
    人设: str = Field(min_length=1)
    动作库: list[str] = Field(min_length=3)
    口头禅: list[str] = Field(min_length=1)
    风格关键词: list[str] = Field(min_length=1)
    是否依赖真人肖像: bool = False
    是否疑似已有IP: bool = False


class 创建生成策略请求(BaseModel):
    目标平台: str = Field(min_length=1)
    目标受众: str = Field(min_length=1)
    生成类型: str = Field(min_length=1)
    表情数量: int = Field(gt=0)
    风格标签: list[str] = Field(min_length=1)
    情绪标签: list[str] = Field(min_length=1)
    场景标签: list[str] = Field(min_length=1)
    关联热点: str | None = None
    关联角色: str | None = None
    风险阈值: str = Field(min_length=1)


class 表情包审核请求(BaseModel):
    套装编号: str = Field(min_length=1)
    审核结论: str = Field(min_length=1)
    风险标签: list[str] = Field(default_factory=list)
    审核意见: str = Field(min_length=1)
    是否需要二审: bool = False


class 自动初审请求(BaseModel):
    套装编号: str = Field(min_length=1)
    风险标签: list[str] = Field(default_factory=list)
    审核意见: str = "自动初审完成"


class 二审请求(BaseModel):
    套装编号: str = Field(min_length=1)
    审核结论: str = Field(min_length=1)
    风险标签: list[str] = Field(default_factory=list)
    审核意见: str = Field(min_length=1)


class 退回重生成请求(BaseModel):
    套装编号: str = Field(min_length=1)
    退回原因: str = Field(min_length=1)
    新策略: 创建生成策略请求


class 创建发布任务请求(BaseModel):
    套装编号: str = Field(min_length=1)
    发布平台: str = Field(min_length=1)
    发布账号: str = Field(min_length=1)
    发布方式: str = Field(min_length=1)
    是否定时: bool = False
    计划发布时间: str | None = None
    是否真实发布: bool = False


class 发布前复核请求(BaseModel):
    套装编号: str = Field(min_length=1)
    复核结论: str = Field(min_length=1)
    复核意见: str = Field(min_length=1)


class 执行发布请求(BaseModel):
    发布任务编号: str = Field(min_length=1)
    确认真实发布: bool


class 记录表现请求(BaseModel):
    套装编号: str = Field(min_length=1)
    下载量: int = Field(ge=0)
    发送量: int = Field(ge=0)
    收藏量: int = Field(ge=0)
    分享量: int = Field(ge=0)
    收益: float = Field(ge=0)
    标签表现: dict[str, int] = Field(default_factory=dict)
    受众表现: dict[str, int] = Field(default_factory=dict)
    拒审原因: list[str] = Field(default_factory=list)


class 创建优化周报请求(BaseModel):
    周期: str = Field(min_length=1)


class 处理规则反馈请求(BaseModel):
    反馈编号: str = Field(min_length=1)
    目标状态: str = Field(min_length=1)
    处理意见: str = Field(min_length=1)


class 创建下一轮策略请求(BaseModel):
    报告编号: str = Field(min_length=1)
    目标平台: str = Field(min_length=1)
    目标受众: str = Field(min_length=1)
    表情数量: int = Field(gt=0)
    基础风格标签: list[str] = Field(min_length=1)
    情绪标签: list[str] = Field(min_length=1)
    场景标签: list[str] = Field(min_length=1)


class 转正式策略请求(BaseModel):
    草案编号: str = Field(min_length=1)
    生成类型: str = Field(min_length=1)
    风险阈值: str = Field(min_length=1)


class LOOP验收请求(BaseModel):
    验收范围: str = Field(default="第一阶段", min_length=1)


class 第一阶段总门禁请求(BaseModel):
    LOOP报告编号: str = Field(min_length=1)


class 再执行队列领取请求(BaseModel):
    队列编号: str = Field(min_length=1)


class 再执行记录请求(BaseModel):
    队列编号: str = Field(min_length=1)
    执行记录: str = Field(min_length=1)


class 再执行完成请求(BaseModel):
    队列编号: str = Field(min_length=1)
    完成说明: str = Field(min_length=1)


class 交付包索引请求(BaseModel):
    门禁编号: str = Field(min_length=1)


class 平台包生成请求(BaseModel):
    套装编号: str = Field(min_length=1)
    平台名称: str = Field(min_length=1)


class 平台包下载前检查请求(BaseModel):
    平台名称: str = Field(min_length=1)
