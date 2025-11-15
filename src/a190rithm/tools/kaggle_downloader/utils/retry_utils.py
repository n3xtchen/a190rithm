"""
重试工具类模块

提供重试功能，支持指数退避策略。
"""

import random
import time
from functools import wraps
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, cast

from ..utils.logging_utils import LoggerAdapter

# 创建一个日志记录器
logger = LoggerAdapter("retry_utils")

# 定义泛型类型变量
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def retry(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    logger: Optional[LoggerAdapter] = None
) -> Callable[[F], F]:
    """
    装饰器，用于在失败时重试函数。

    参数:
        exceptions: 要捕获的异常类型或异常类型列表
        tries: 最大重试次数（不包括第一次尝试）
        delay: 初始延迟（秒）
        backoff: 退避因子，用于计算下一次延迟
        jitter: 抖动因子，增加随机性避免雷同请求
        logger: 日志记录器

    返回:
        装饰过的函数
    """
    if isinstance(exceptions, list):
        exceptions_tuple = tuple(exceptions)
    else:
        exceptions_tuple = (exceptions,)

    log = logger or LoggerAdapter("retry")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            local_tries, local_delay = tries, delay
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions_tuple as e:
                    local_tries -= 1
                    if local_tries < 0:
                        log.error(f"已达到最大重试次数 {tries}，放弃：{e}")
                        raise

                    # 增加随机抖动避免雷同请求
                    jitter_value = random.uniform(-jitter, jitter)
                    sleep_time = local_delay * (1 + jitter_value)

                    log.warning(
                        f"调用 {func.__name__} 失败，{e}，将在 {sleep_time:.2f} 秒后重试，剩余重试次数：{local_tries}",
                        exc_info=True
                    )

                    time.sleep(sleep_time)
                    # 增加下一次延迟
                    local_delay *= backoff

        return cast(F, wrapper)

    return decorator


class RetryWithExponentialBackoff:
    """
    提供指数退避重试策略的类。

    用法示例:
        retry = RetryWithExponentialBackoff(max_retries=3, base_delay=1.0)
        result = retry.execute(lambda: some_function())
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
        jitter: float = 0.1,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
        logger: Optional[LoggerAdapter] = None
    ):
        """
        初始化重试对象。

        参数:
            max_retries: 最大重试次数（不包括第一次尝试）
            base_delay: 初始延迟（秒）
            backoff_factor: 退避因子，用于计算下一次延迟
            jitter: 抖动因子，增加随机性避免雷同请求
            exceptions: 要捕获的异常类型或异常类型列表
            logger: 日志记录器
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        if isinstance(exceptions, list):
            self.exceptions = tuple(exceptions)
        else:
            self.exceptions = (exceptions,)
        self.logger = logger or LoggerAdapter("retry")

    def execute(self, func: Callable[[], T], *args: Any, **kwargs: Any) -> T:
        """
        执行函数，失败时使用指数退避策略重试。

        参数:
            func: 要执行的函数
            args: 传递给函数的位置参数
            kwargs: 传递给函数的关键字参数

        返回:
            函数的返回值

        抛出:
            最后一次尝试的异常（如果所有尝试都失败）
        """
        tries = 0
        delay = self.base_delay

        while True:
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                tries += 1
                if tries > self.max_retries:
                    self.logger.error(f"已达到最大重试次数 {self.max_retries}，放弃：{e}")
                    raise

                # 增加随机抖动避免雷同请求
                jitter_value = random.uniform(-self.jitter, self.jitter)
                sleep_time = delay * (1 + jitter_value)

                self.logger.warning(
                    f"调用失败，{e}，将在 {sleep_time:.2f} 秒后重试，剩余重试次数：{self.max_retries - tries}",
                    exc_info=True
                )

                time.sleep(sleep_time)
                # 增加下一次延迟
                delay *= self.backoff_factor