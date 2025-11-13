"""
数据模型模块

定义 Kaggle 数据下载与 Parquet 格式转换功能所需的核心数据模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class DatasetStatus(Enum):
    """数据集处理状态枚举类型"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadStatus(Enum):
    """文件下载状态枚举类型"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConversionStatus(Enum):
    """转换状态枚举类型"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


class FileFormat(Enum):
    """支持的文件格式枚举类型"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    TSV = "tsv"
    PARQUET = "parquet"
    AVRO = "avro"
    ORC = "orc"
    XML = "xml"
    HTML = "html"
    TXT = "txt"
    OTHER = "other"


@dataclass
class DataFile:
    """
    表示数据集中的单个数据文件。

    属性:
        filename: 文件名称
        format: 文件格式
        size: 文件大小（字节）
        path: 本地存储路径
        columns: 数据列名称（表格数据）
        schema: 数据架构
        download_status: 下载状态
        download_progress: 下载进度（0-100）
        checksum: 文件校验和（用于验证完整性）
    """
    filename: str
    format: FileFormat
    size: int
    path: str
    columns: Optional[List[str]] = None
    schema: Optional[Dict] = None
    download_status: DownloadStatus = DownloadStatus.PENDING
    download_progress: float = 0.0
    checksum: Optional[str] = None


@dataclass
class Dataset:
    """
    表示 Kaggle 上的数据集。

    属性:
        id: 数据集在 Kaggle 平台上的唯一标识符
        name: 数据集名称
        owner: 数据集创建者/所有者
        url: 数据集在 Kaggle 平台的 URL
        size: 数据集大小（字节）
        timestamp: 下载时间戳
        description: 数据集描述信息
        files: 数据集包含的文件列表
        metadata: 其他元数据信息
        status: 数据集处理状态
    """
    id: str
    name: str
    owner: str
    url: str
    size: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    files: List[DataFile] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    status: DatasetStatus = DatasetStatus.PENDING


@dataclass
class ParquetFile:
    """
    表示转换后的 Parquet 格式文件。

    属性:
        original_file: 对应的原始数据文件
        filename: Parquet 文件名称
        path: 存储路径
        size: 文件大小（字节）
        schema: Parquet 架构
        rows: 数据行数
        compression_ratio: 相对原始文件的压缩比
        partition_cols: 分区列（如果适用）
        timestamp: 转换时间戳
        conversion_status: 转换状态
    """
    original_file: DataFile
    filename: str
    path: str
    size: int
    schema: Dict
    rows: int = 0
    compression_ratio: float = 1.0
    partition_cols: Optional[List[str]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    conversion_status: ConversionStatus = ConversionStatus.PENDING