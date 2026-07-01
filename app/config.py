from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class 应用配置(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_EMOJI_", extra="ignore")

    应用名称: str = "企业级表情包后台"
    数据库路径: Path = Field(default=Path("data/emoji_pack.sqlite"))
    日志路径: Path = Field(default=Path("logs/app.log"))
    视觉评分端点: str = ""
    视觉评分超时秒: float = Field(default=3.0, gt=0)
    视觉评分密钥: str = ""


@lru_cache
def 获取配置() -> 应用配置:
    配置 = 应用配置()
    配置.数据库路径.parent.mkdir(parents=True, exist_ok=True)
    配置.日志路径.parent.mkdir(parents=True, exist_ok=True)
    return 配置
