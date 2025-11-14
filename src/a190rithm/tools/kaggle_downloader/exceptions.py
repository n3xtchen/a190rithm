"""
异常类层次结构模块

定义 Kaggle 数据下载与 Parquet 格式转换功能可能抛出的各种异常。
"""


class KaggleParquetError(Exception):
    """基础异常类，所有自定义异常的父类"""
    pass


# API 相关错误
class APIError(KaggleParquetError):
    """API 相关错误的基类"""
    pass


class KaggleAPIError(APIError):
    """Kaggle API 交互时出现错误"""
    pass


class AuthenticationError(APIError):
    """API 认证失败或凭证无效"""
    pass


# 数据集相关错误
class DatasetError(KaggleParquetError):
    """数据集相关错误的基类"""
    pass


class DatasetNotFoundError(DatasetError):
    """指定的数据集不存在"""
    pass


class FileNotFoundError(DatasetError):
    """指定的文件不存在于数据集中"""
    pass


class InvalidDatasetError(DatasetError):
    """数据集格式或内容无效"""
    pass


# 存储相关错误
class StorageError(KaggleParquetError):
    """存储相关错误的基类"""
    def __init__(self, message, **kwargs):
        super().__init__(message)
        for key, value in kwargs.items():
            setattr(self, key, value)


class DirectoryNotFoundError(StorageError):
    """指定的目录不存在"""
    pass


class PermissionDeniedError(StorageError):
    """没有足够的权限执行操作"""
    pass


class InsufficientSpaceError(StorageError):
    """存储空间不足"""
    pass


# 转换相关错误
class ConversionError(KaggleParquetError):
    """转换相关错误的基类"""
    pass


class UnsupportedFormatError(ConversionError):
    """不支持转换的文件格式"""
    pass


class InvalidSchemaError(ConversionError):
    """数据架构无效或不兼容"""
    pass


class DataCorruptionError(ConversionError):
    """数据已损坏或格式错误"""
    pass


# 网络相关错误
class NetworkError(KaggleParquetError):
    """网络相关错误的基类"""
    pass


class DownloadError(NetworkError):
    """下载过程中出现错误"""
    def __init__(self, message, **kwargs):
        super().__init__(message)
        for key, value in kwargs.items():
            setattr(self, key, value)


class TimeoutError(NetworkError):
    """网络操作超时"""
    pass


class RateLimitError(NetworkError):
    """达到 API 速率限制"""
    pass


# 配置相关错误
class ConfigurationError(KaggleParquetError):
    """配置相关错误"""
    pass