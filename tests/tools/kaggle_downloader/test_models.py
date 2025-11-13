"""
数据模型模块测试

测试 Dataset, DataFile 和 ParquetFile 类的功能。
"""

import pytest
from datetime import datetime

from a190rithm.tools.kaggle_downloader.models import (
    Dataset, DataFile, ParquetFile,
    DatasetStatus, DownloadStatus, ConversionStatus, FileFormat
)


def test_dataset_creation():
    """测试创建 Dataset 实例"""
    # 创建一个基本的数据集实例
    dataset = Dataset(
        id="username/dataset-name",
        name="dataset-name",
        owner="username",
        url="https://www.kaggle.com/datasets/username/dataset-name"
    )

    # 验证基本属性
    assert dataset.id == "username/dataset-name"
    assert dataset.name == "dataset-name"
    assert dataset.owner == "username"
    assert dataset.url == "https://www.kaggle.com/datasets/username/dataset-name"
    assert dataset.size == 0
    assert isinstance(dataset.timestamp, datetime)
    assert dataset.description == ""
    assert dataset.files == []
    assert dataset.metadata == {}
    assert dataset.status == DatasetStatus.PENDING


def test_datafile_creation():
    """测试创建 DataFile 实例"""
    # 创建一个数据文件实例
    datafile = DataFile(
        filename="sample.csv",
        format=FileFormat.CSV,
        size=1024,
        path="/path/to/sample.csv",
        columns=["id", "name", "value"]
    )

    # 验证基本属性
    assert datafile.filename == "sample.csv"
    assert datafile.format == FileFormat.CSV
    assert datafile.size == 1024
    assert datafile.path == "/path/to/sample.csv"
    assert datafile.columns == ["id", "name", "value"]
    assert datafile.schema is None
    assert datafile.download_status == DownloadStatus.PENDING
    assert datafile.download_progress == 0.0
    assert datafile.checksum is None


def test_parquetfile_creation():
    """测试创建 ParquetFile 实例"""
    # 创建一个数据文件实例
    datafile = DataFile(
        filename="sample.csv",
        format=FileFormat.CSV,
        size=1024,
        path="/path/to/sample.csv"
    )

    # 创建一个 Parquet 文件实例
    parquetfile = ParquetFile(
        original_file=datafile,
        filename="sample.parquet",
        path="/path/to/sample.parquet",
        size=512,
        schema={"fields": [{"name": "id", "type": "integer"}]},
        rows=100,
        compression_ratio=0.5
    )

    # 验证基本属性
    assert parquetfile.original_file == datafile
    assert parquetfile.filename == "sample.parquet"
    assert parquetfile.path == "/path/to/sample.parquet"
    assert parquetfile.size == 512
    assert parquetfile.schema == {"fields": [{"name": "id", "type": "integer"}]}
    assert parquetfile.rows == 100
    assert parquetfile.compression_ratio == 0.5
    assert parquetfile.partition_cols is None
    assert isinstance(parquetfile.timestamp, datetime)
    assert parquetfile.conversion_status == ConversionStatus.PENDING


def test_dataset_with_files():
    """测试带有文件的数据集"""
    # 创建数据文件
    file1 = DataFile(
        filename="file1.csv",
        format=FileFormat.CSV,
        size=1000,
        path="/path/to/file1.csv"
    )
    file2 = DataFile(
        filename="file2.json",
        format=FileFormat.JSON,
        size=2000,
        path="/path/to/file2.json"
    )

    # 创建数据集
    dataset = Dataset(
        id="username/dataset-name",
        name="dataset-name",
        owner="username",
        url="https://www.kaggle.com/datasets/username/dataset-name",
        files=[file1, file2],
        size=3000,
        status=DatasetStatus.DOWNLOADED
    )

    # 验证数据集属性
    assert len(dataset.files) == 2
    assert dataset.files[0].filename == "file1.csv"
    assert dataset.files[1].filename == "file2.json"
    assert dataset.size == 3000
    assert dataset.status == DatasetStatus.DOWNLOADED