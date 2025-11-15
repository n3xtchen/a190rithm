"""
异常类层次结构测试

测试异常类的继承关系和功能。
"""

import pytest

from a190rithm.tools.kaggle_downloader.exceptions import (
    KaggleParquetError, APIError, KaggleAPIError, AuthenticationError,
    DatasetError, DatasetNotFoundError, FileNotFoundError, InvalidDatasetError,
    StorageError, DirectoryNotFoundError, PermissionDeniedError, InsufficientSpaceError,
    ConversionError, UnsupportedFormatError, InvalidSchemaError, DataCorruptionError,
    NetworkError, DownloadError, TimeoutError, RateLimitError,
    ConfigurationError
)


def test_exception_inheritance():
    """测试异常继承关系"""
    # 测试基类继承
    assert issubclass(APIError, KaggleParquetError)
    assert issubclass(DatasetError, KaggleParquetError)
    assert issubclass(StorageError, KaggleParquetError)
    assert issubclass(ConversionError, KaggleParquetError)
    assert issubclass(NetworkError, KaggleParquetError)
    assert issubclass(ConfigurationError, KaggleParquetError)

    # 测试 API 错误继承
    assert issubclass(KaggleAPIError, APIError)
    assert issubclass(AuthenticationError, APIError)

    # 测试数据集错误继承
    assert issubclass(DatasetNotFoundError, DatasetError)
    assert issubclass(FileNotFoundError, DatasetError)
    assert issubclass(InvalidDatasetError, DatasetError)

    # 测试存储错误继承
    assert issubclass(DirectoryNotFoundError, StorageError)
    assert issubclass(PermissionDeniedError, StorageError)
    assert issubclass(InsufficientSpaceError, StorageError)

    # 测试转换错误继承
    assert issubclass(UnsupportedFormatError, ConversionError)
    assert issubclass(InvalidSchemaError, ConversionError)
    assert issubclass(DataCorruptionError, ConversionError)

    # 测试网络错误继承
    assert issubclass(DownloadError, NetworkError)
    assert issubclass(TimeoutError, NetworkError)
    assert issubclass(RateLimitError, NetworkError)


def test_exception_messages():
    """测试异常消息"""
    # 测试基本异常消息
    error = KaggleParquetError("基本错误消息")
    assert str(error) == "基本错误消息"

    # 测试 API 异常消息
    error = KaggleAPIError("Kaggle API 调用失败")
    assert str(error) == "Kaggle API 调用失败"
    assert isinstance(error, APIError)

    # 测试数据集异常消息
    error = DatasetNotFoundError("找不到数据集 'username/dataset-name'")
    assert str(error) == "找不到数据集 'username/dataset-name'"
    assert isinstance(error, DatasetError)

    # 测试自定义属性
    error = DownloadError("下载失败", url="https://example.com/file.csv")
    assert str(error) == "下载失败"
    assert hasattr(error, "url")
    assert error.url == "https://example.com/file.csv"