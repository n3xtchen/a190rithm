"""
Pytest 配置文件

定义所有测试使用的共享夹具。
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from a190rithm.tools.kaggle_downloader.models import (
    Dataset, DataFile, ParquetFile, FileFormat,
    DatasetStatus, DownloadStatus, ConversionStatus
)


@pytest.fixture
def sample_dataset():
    """创建示例数据集对象"""
    file1 = DataFile(
        filename="file1.csv",
        format=FileFormat.CSV,
        size=1024,
        path="/path/to/file1.csv",
        columns=["id", "name", "value"],
        download_status=DownloadStatus.COMPLETED,
        download_progress=100.0
    )

    file2 = DataFile(
        filename="file2.json",
        format=FileFormat.JSON,
        size=2048,
        path="/path/to/file2.json",
        download_status=DownloadStatus.COMPLETED,
        download_progress=100.0
    )

    return Dataset(
        id="username/dataset-name",
        name="dataset-name",
        owner="username",
        url="https://www.kaggle.com/datasets/username/dataset-name",
        size=3072,
        description="示例数据集",
        files=[file1, file2],
        status=DatasetStatus.DOWNLOADED
    )


@pytest.fixture
def sample_parquet_file(sample_dataset):
    """创建示例 Parquet 文件对象"""
    original_file = sample_dataset.files[0]  # 使用第一个 CSV 文件

    return ParquetFile(
        original_file=original_file,
        filename="file1.parquet",
        path="/path/to/file1.parquet",
        size=512,
        schema={"fields": [{"name": "id", "type": "integer"}]},
        rows=100,
        compression_ratio=0.5,
        conversion_status=ConversionStatus.COMPLETED
    )


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        kaggle_dir = base_dir / "kaggle"
        dataset_dir = kaggle_dir / "dataset_name_20251113"
        original_dir = dataset_dir / "original"
        parquet_dir = dataset_dir / "parquet"
        logs_dir = dataset_dir / "logs"

        # 创建目录结构
        for dir_path in [kaggle_dir, dataset_dir, original_dir, parquet_dir, logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 创建元数据文件
        metadata = {
            "id": "username/dataset-name",
            "name": "dataset-name",
            "owner": "username",
            "timestamp": "2025-11-13T00:00:00Z"
        }
        with open(dataset_dir / "metadata.json", "w") as f:
            yaml.dump(metadata, f)

        yield base_dir