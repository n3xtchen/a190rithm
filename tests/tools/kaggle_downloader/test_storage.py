"""
测试存储管理模块
"""

import os
import tempfile
import json
import shutil
from pathlib import Path
import datetime
from unittest.mock import patch, MagicMock

import pytest

from a190rithm.tools.kaggle_downloader.storage import StorageManager
from a190rithm.tools.kaggle_downloader.models import Dataset, DataFile, ParquetFile, FileFormat, DownloadStatus, ConversionStatus
from a190rithm.tools.kaggle_downloader.exceptions import StorageError


class TestStorageManager:
    """
    测试 StorageManager 类的功能
    """

    def setup_method(self):
        """设置测试环境"""
        # 创建临时目录作为数据存储位置
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.temp_dir.name
        self.storage_manager = StorageManager(base_dir=self.base_dir)

        # 创建测试数据集
        self.dataset = Dataset(
            id="testowner/testdataset",
            name="testdataset",
            owner="testowner",
            size=1000,
            url="https://www.kaggle.com/datasets/testowner/testdataset"
        )

        # 创建测试原始文件
        self.data_file = DataFile(
            filename="test.csv",
            format=FileFormat.CSV,
            size=500,
            path=os.path.join(self.temp_dir.name, "test.csv"),
            download_status=DownloadStatus.COMPLETED
        )

        # 创建测试 Parquet 文件
        self.temp_parquet_path = os.path.join(self.temp_dir.name, "test.parquet")
        # 创建一个空的 Parquet 文件用于测试
        with open(self.temp_parquet_path, 'wb') as f:
            f.write(b'TESTPARQUETFILE')

        self.parquet_file = ParquetFile(
            original_file=self.data_file,
            filename="test.parquet",
            path=self.temp_parquet_path,
            size=100,
            schema={"column1": "string", "column2": "int64"},
            rows=10,
            compression_ratio=0.2,
            conversion_status=ConversionStatus.COMPLETED
        )

    def teardown_method(self):
        """清理测试环境"""
        self.temp_dir.cleanup()

    def test_get_dataset_path(self):
        """测试获取数据集路径功能"""
        # 使用固定时间戳进行测试，确保路径可预测
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)

        # 获取数据集路径
        dataset_path = self.storage_manager.get_dataset_path(
            self.dataset, timestamp=timestamp, create=True
        )

        # 构建预期路径
        expected_path = os.path.join(
            self.base_dir,
            "kaggle",
            "testdataset_20230101_120000"
        )

        # 验证路径正确并且已创建
        assert dataset_path == expected_path
        assert os.path.exists(dataset_path)

    def test_store_parquet_files(self):
        """测试存储 Parquet 文件功能"""
        # 使用固定时间戳
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)

        # 存储 Parquet 文件
        storage_dir = self.storage_manager.store_parquet_files(
            self.dataset, [self.parquet_file], timestamp=timestamp
        )

        # 构建预期路径
        expected_dir = os.path.join(
            self.base_dir,
            "kaggle",
            "testdataset_20230101_120000"
        )

        # 验证存储目录正确
        assert storage_dir == expected_dir

        # 验证文件已复制
        expected_file_path = os.path.join(expected_dir, "test.parquet")
        assert os.path.exists(expected_file_path)

        # 验证元数据已保存
        metadata_path = os.path.join(expected_dir, "metadata.json")
        assert os.path.exists(metadata_path)

    def test_save_metadata(self):
        """测试保存元数据功能"""
        # 使用固定时间戳
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)

        # 创建存储目录
        storage_dir = self.storage_manager.get_dataset_path(
            self.dataset, timestamp=timestamp
        )

        # 保存元数据
        metadata_path = self.storage_manager.save_metadata(
            self.dataset, [self.parquet_file], storage_dir
        )

        # 验证元数据文件已创建
        assert os.path.exists(metadata_path)

        # 读取元数据并验证内容
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 验证基本结构
        assert "dataset" in metadata
        assert "parquet_files" in metadata
        assert "storage" in metadata

        # 验证数据集信息
        assert metadata["dataset"]["ref"] == "testowner/testdataset"
        assert metadata["dataset"]["name"] == "testdataset"

        # 验证 Parquet 文件信息
        assert len(metadata["parquet_files"]) == 1
        assert metadata["parquet_files"][0]["filename"] == "test.parquet"
        assert metadata["parquet_files"][0]["rows"] == 10

    def test_list_datasets_empty(self):
        """测试列出数据集功能 - 空目录"""
        # 确保目录为空
        datasets = self.storage_manager.list_datasets()
        assert datasets == []

    def test_list_datasets(self):
        """测试列出数据集功能 - 有数据集"""
        # 创建两个测试数据集目录
        timestamp1 = datetime.datetime(2023, 1, 1, 12, 0, 0)
        dataset1 = Dataset(
            id="owner1/dataset1",
            name="dataset1",
            owner="owner1",
            size=1000,
            url="https://www.kaggle.com/datasets/owner1/dataset1"
        )

        timestamp2 = datetime.datetime(2023, 1, 2, 12, 0, 0)
        dataset2 = Dataset(
            id="owner2/dataset2",
            name="dataset2",
            owner="owner2",
            size=2000,
            url="https://www.kaggle.com/datasets/owner2/dataset2"
        )

        # 存储测试数据集
        self.storage_manager.store_parquet_files(
            dataset1, [self.parquet_file], timestamp=timestamp1
        )

        # 创建第二个 Parquet 文件
        parquet_file2 = ParquetFile(
            original_file=self.data_file,
            filename="test2.parquet",
            path=self.temp_parquet_path,  # 重用同一路径
            size=200,
            schema={"col1": "string", "col2": "float64"},
            rows=20,
            compression_ratio=0.3,
            conversion_status=ConversionStatus.COMPLETED
        )

        self.storage_manager.store_parquet_files(
            dataset2, [parquet_file2], timestamp=timestamp2
        )

        # 列出所有数据集
        datasets = self.storage_manager.list_datasets()

        # 验证结果
        assert len(datasets) == 2

        # 按名称过滤
        filtered = self.storage_manager.list_datasets(pattern="dataset1")
        assert len(filtered) == 1
        assert filtered[0]["name"].endswith("dataset1_20230101_120000")

        # 测试详细信息
        detailed = self.storage_manager.list_datasets(detail=True)
        assert len(detailed) == 2
        assert "dataset" in detailed[0]
        assert "parquet_files" in detailed[0]