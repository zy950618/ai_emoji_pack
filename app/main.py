from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.audit import 审计服务
from app.analytics import 数据回流服务
from app.asset_validator import 资产校验服务
from app.audience import 受众画像服务
from app.config import 获取配置
from app.database import 数据库
from app.exceptions import 业务异常
from app.generation import 生成策略服务
from app.hotspot import 热点服务
from app.ip_roles import 原创角色服务
from app.logging_config import 配置日志
from app.loop_acceptance import LOOP验收服务
from app.platform_packages import 平台包服务
from app.publishing import 发布服务
from app.review import 审核服务
from app.rule_governance import 平台规则治理服务
from app.routes import 创建路由
from app.scheduler import 定时任务服务
from app.schemas import 标准响应
from app.sticker_acceptance import 表情套装验收服务
from app.task_center import 任务中心
from app.validator import 规格校验器


def 创建应用() -> FastAPI:
    配置 = 获取配置()
    配置日志(配置.日志路径)
    数据库实例 = 数据库(配置.数据库路径)
    数据库实例.初始化()
    审计 = 审计服务(数据库实例)
    规则治理 = 平台规则治理服务(数据库实例, 审计)
    规则治理.初始化基线规则()
    任务服务 = 任务中心(数据库实例, 审计)
    定时任务 = 定时任务服务(数据库实例, 审计)
    校验器 = 规格校验器(数据库实例, 审计, 规则治理)
    资产校验 = 资产校验服务(数据库实例, 审计, 规则治理)
    套装验收 = 表情套装验收服务(数据库实例, 审计)
    受众画像 = 受众画像服务(数据库实例, 审计)
    热点 = 热点服务(数据库实例, 审计)
    原创角色 = 原创角色服务(数据库实例, 审计)
    生成策略 = 生成策略服务(数据库实例, 审计, 规则治理)
    审核 = 审核服务(数据库实例, 审计)
    发布 = 发布服务(数据库实例, 审计)
    平台包 = 平台包服务(数据库实例, 审计, 规则治理)
    数据回流 = 数据回流服务(数据库实例, 审计)
    LOOP验收 = LOOP验收服务(数据库实例, 审计)

    app = FastAPI(title=配置.应用名称, version="0.1.0")

    @app.exception_handler(业务异常)
    async def 处理业务异常(_: Request, exc: 业务异常) -> JSONResponse:
        响应 = 标准响应(成功=False, 消息=exc.消息, 错误码=exc.错误码)
        return JSONResponse(status_code=exc.状态码, content=响应.model_dump())

    @app.exception_handler(RequestValidationError)
    async def 处理参数异常(_: Request, exc: RequestValidationError) -> JSONResponse:
        响应 = 标准响应(
            成功=False,
            消息="请求参数不合法",
            错误码="参数错误",
            数据={"错误详情": exc.errors()},
        )
        return JSONResponse(status_code=422, content=响应.model_dump())

    app.include_router(创建路由(任务服务, 审计, 定时任务, 校验器, 资产校验, 套装验收, 规则治理, 受众画像, 热点, 原创角色, 生成策略, 审核, 发布, 平台包, 数据回流, LOOP验收))
    return app


app = 创建应用()
