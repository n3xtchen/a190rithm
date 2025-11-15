"""
日志工具类模块

提供结构化日志功能，集成 structlog 和标准库 logging。
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True,
    include_timestamps: bool = True
) -> None:
    """
    设置日志系统。

    参数:
        level: 日志级别，可以是 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        log_file: 日志文件路径，如果为 None 则只输出到控制台
        structured: 是否使用结构化日志（使用 structlog）
        include_timestamps: 是否在日志中包含时间戳
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除所有现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    handlers = [console_handler]

    # 文件处理器（如果提供了日志文件）
    if log_file:
        log_path = os.path.expanduser(log_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    # 使用 structlog 进行结构化日志
    if structured:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        if include_timestamps:
            processors.append(structlog.processors.TimeStamper(fmt="iso"))

        if sys.stderr.isatty():
            # 终端彩色输出
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            # JSON 格式化
            processors.append(structlog.processors.JSONRenderer())

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # 为标准库日志配置处理器和格式化器
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
            foreign_pre_chain=processors,
        )

        for handler in handlers:
            handler.setFormatter(formatter)
    else:
        # 使用传统的日志格式
        format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s" if include_timestamps else "[%(levelname)s] %(name)s: %(message)s"
        formatter = logging.Formatter(format_str)
        for handler in handlers:
            handler.setFormatter(formatter)

    # 添加处理器到根日志记录器
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str) -> Any:
    """
    获取配置好的日志记录器。

    参数:
        name: 日志记录器名称

    返回:
        日志记录器
    """
    try:
        return structlog.get_logger(name)
    except Exception:
        return logging.getLogger(name)


class LoggerAdapter:
    """
    日志适配器，提供标准接口无论是否使用 structlog。

    这个类封装了 structlog 和标准库 logging 的接口差异，提供统一的日志记录方法。
    """

    def __init__(self, name: str):
        """
        初始化日志适配器。

        参数:
            name: 日志记录器名称
        """
        self.logger = get_logger(name)
        self._is_structlog = hasattr(self.logger, "bind")

    def debug(self, message: str, **kwargs) -> None:
        """记录调试级别日志。"""
        if self._is_structlog:
            self.logger.debug(message, **kwargs)
        else:
            if kwargs:
                message = f"{message} {kwargs}"
            self.logger.debug(message)

    def info(self, message: str, **kwargs) -> None:
        """记录信息级别日志。"""
        if self._is_structlog:
            self.logger.info(message, **kwargs)
        else:
            if kwargs:
                message = f"{message} {kwargs}"
            self.logger.info(message)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告级别日志。"""
        if self._is_structlog:
            self.logger.warning(message, **kwargs)
        else:
            if kwargs:
                message = f"{message} {kwargs}"
            self.logger.warning(message)

    def error(self, message: str, **kwargs) -> None:
        """记录错误级别日志。"""
        if self._is_structlog:
            self.logger.error(message, **kwargs)
        else:
            if kwargs:
                message = f"{message} {kwargs}"
            self.logger.error(message)

    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误级别日志。"""
        if self._is_structlog:
            self.logger.critical(message, **kwargs)
        else:
            if kwargs:
                message = f"{message} {kwargs}"
            self.logger.critical(message)

    def bind(self, **kwargs) -> 'LoggerAdapter':
        """
        创建带有额外上下文数据的新日志适配器。

        参数:
            **kwargs: 要绑定到日志记录器的上下文数据

        返回:
            新的 LoggerAdapter 实例
        """
        if self._is_structlog:
            new_adapter = LoggerAdapter("")
            new_adapter.logger = self.logger.bind(**kwargs)
            new_adapter._is_structlog = True
            return new_adapter
        else:
            # 对于标准日志，我们创建一个子适配器并存储上下文
            new_adapter = LoggerAdapter("")
            new_adapter.logger = self.logger
            new_adapter._is_structlog = False
            new_adapter._context = kwargs
            return new_adapter