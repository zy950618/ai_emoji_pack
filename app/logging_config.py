import logging
from pathlib import Path


def 配置日志(日志路径: Path) -> None:
    日志路径.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(日志路径, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )
