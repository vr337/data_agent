"""日志配置模块"""

from math import sin
from pathlib import Path
import sys

from loguru import logger

from data_agent.core.configs.app_config import app_config
from data_agent.core.context import get_request_id

# 移除默认的日志配置
logger.remove()


# 日志输出的格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 绿色显示日志时间（精确到毫秒）
    "<level>{level: <8}</level> | "  # 按级别颜色显示日志级别（左对齐，占8个字符）
    "<magenta>request_id - {extra[request_id]}</magenta> | "  # 品红色显示request_id（从日志extra中获取）
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 青色显示日志所在文件、函数、行号
    "<level>{message}</level>"  # 按级别颜色显示日志正文
)


# 设置回调函数(钩子函数)，给日志填充request_id
def inject_request_id(record) -> None:
    """
    每输出一条日志时，自动往record里的extra注入request_id
    Args:
        record (_type_): 每条日志记录
    """
    # 获取当前请求的request_id
    request_id = get_request_id()
    # 注入到日志里
    record["extra"]["request_id"] = request_id


# 打补丁(注册回调函数)，出发后有返回值，要更新logger
logger = logger.patch(inject_request_id)

if app_config.logging.console.enable:
    # 自定义控制台日志格式
    logger.add(
        sink=sys.stdout,  # 控制台输出
        level=app_config.logging.console.level,  # 控制台日志输出级别
        format=log_format,  # 自定义的日志格式
    )

if app_config.logging.file.enable:
    # 自定义保存到文件的日志格式
    # 获取保存文件的Path对象
    path = Path(app_config.logging.file.path)
    # 自动递归创建目录
    path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=path / "app.log",  # 日志保存的文件路基
        level=app_config.logging.file.level,  # 文件的日志输出级别
        format=log_format,  # 自定义的日志格式
        rotation=app_config.logging.file.rotation,  # 日志文件的分割规则(文件大小/时间)
        retention=app_config.logging.file.retention,  # 日志文件的有效器
        encoding="utf-8",  # 日志文件的编码格式
    )
