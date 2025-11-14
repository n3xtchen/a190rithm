"""
测试数据转换模块
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from a190rithm.tools.kaggle_downloader.converter import DataConverter
from a190rithm.tools.kaggle_downloader.exceptions import UnsupportedFormatError, ConversionError
from a190rithm.tools.kaggle_downloader.models import DataFile, FileFormat, DownloadStatus


class TestDataConverter:
    """
    测试 DataConverter 类的功能
    """

    def setup_method(self):
        """设置测试环境"""
        self.converter = DataConverter(compression="snappy", processes=1)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name

    def teardown_method(self):
        """清理测试环境"""
        self.temp_dir.cleanup()

    def create_test_csv_file(self):
        """创建测试用 CSV 文件"""
        test_file_path = os.path.join(self.temp_dir.name, "test.csv")
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eva"],
            "age": [25, 30, 35, 40, 45],
            "score": [95.5, 80.3, 75.9, 90.2, 88.7]
        })
        df.to_csv(test_file_path, index=False)
        return test_file_path

    def create_test_json_file(self):
        """创建测试用 JSON 文件"""
        test_file_path = os.path.join(self.temp_dir.name, "test.json")
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eva"],
            "age": [25, 30, 35, 40, 45],
            "score": [95.5, 80.3, 75.9, 90.2, 88.7]
        })
        df.to_json(test_file_path, orient="records")
        return test_file_path

    def create_test_jsonl_file(self):
        """创建测试用 JSON Lines 文件"""
        test_file_path = os.path.join(self.temp_dir.name, "test.jsonl")
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eva"],
            "age": [25, 30, 35, 40, 45],
            "score": [95.5, 80.3, 75.9, 90.2, 88.7]
        })
        df.to_json(test_file_path, orient="records", lines=True)
        return test_file_path

    def create_test_excel_file(self):
        """创建测试用 Excel 文件"""
        test_file_path = os.path.join(self.temp_dir.name, "test.xlsx")
        df1 = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eva"],
            "age": [25, 30, 35, 40, 45],
        })
        df2 = pd.DataFrame({
            "id": [1, 2, 3],
            "score": [95.5, 80.3, 75.9],
            "grade": ["A", "B", "C"]
        })
        with pd.ExcelWriter(test_file_path) as writer:
            df1.to_excel(writer, sheet_name="Sheet1", index=False)
            df2.to_excel(writer, sheet_name="Sheet2", index=False)
        return test_file_path

    def create_test_tsv_file(self):
        """创建测试用 TSV 文件"""
        test_file_path = os.path.join(self.temp_dir.name, "test.tsv")
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eva"],
            "age": [25, 30, 35, 40, 45],
            "score": [95.5, 80.3, 75.9, 90.2, 88.7]
        })
        df.to_csv(test_file_path, sep='\t', index=False)
        return test_file_path

    def test_detect_format(self):
        """测试格式检测功能"""
        # 创建测试文件
        csv_path = self.create_test_csv_file()
        json_path = self.create_test_json_file()
        excel_path = self.create_test_excel_file()
        tsv_path = self.create_test_tsv_file()

        # 测试格式检测
        assert self.converter.detect_format(csv_path) == FileFormat.CSV
        assert self.converter.detect_format(json_path) == FileFormat.JSON
        assert self.converter.detect_format(excel_path) == FileFormat.EXCEL
        assert self.converter.detect_format(tsv_path) == FileFormat.TSV

        # 测试不存在的格式
        unknown_path = os.path.join(self.temp_dir.name, "test.xyz")
        with open(unknown_path, "w") as f:
            f.write("test content")
        assert self.converter.detect_format(unknown_path) == FileFormat.OTHER

    def test_is_supported_format(self):
        """测试支持的格式检查"""
        assert self.converter.is_supported_format(FileFormat.CSV) is True
        assert self.converter.is_supported_format(FileFormat.JSON) is True
        assert self.converter.is_supported_format(FileFormat.EXCEL) is True
        assert self.converter.is_supported_format(FileFormat.TSV) is True
        assert self.converter.is_supported_format(FileFormat.PARQUET) is True
        assert self.converter.is_supported_format(FileFormat.OTHER) is False

    def test_convert_csv(self):
        """测试 CSV 转换功能"""
        # 创建测试文件和 DataFile 对象
        csv_path = self.create_test_csv_file()
        data_file = DataFile(
            filename="test.csv",
            format=FileFormat.CSV,
            size=os.path.getsize(csv_path),
            path=csv_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_file = self.converter.convert_file(data_file, output_dir)

        # 验证结果
        assert parquet_file is not None
        assert parquet_file.filename == "test.parquet"
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))
        assert parquet_file.rows == 5
        assert parquet_file.size > 0
        assert parquet_file.compression_ratio > 0

    def test_convert_json(self):
        """测试 JSON 转换功能"""
        # 创建测试文件和 DataFile 对象
        json_path = self.create_test_json_file()
        data_file = DataFile(
            filename="test.json",
            format=FileFormat.JSON,
            size=os.path.getsize(json_path),
            path=json_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_file = self.converter.convert_file(data_file, output_dir)

        # 验证结果
        assert parquet_file is not None
        assert parquet_file.filename == "test.parquet"
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))
        assert parquet_file.rows == 5
        assert parquet_file.size > 0
        assert parquet_file.compression_ratio > 0

    def test_convert_jsonl(self):
        """测试 JSON Lines 转换功能"""
        # 创建测试文件和 DataFile 对象
        jsonl_path = self.create_test_jsonl_file()
        data_file = DataFile(
            filename="test.jsonl",
            format=FileFormat.JSON,
            size=os.path.getsize(jsonl_path),
            path=jsonl_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 检测是否为 JSON Lines 格式
        assert self.converter._is_json_lines_format(jsonl_path) is True

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_file = self.converter.convert_file(data_file, output_dir)

        # 验证结果
        assert parquet_file is not None
        assert parquet_file.filename == "test.parquet"
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))
        assert parquet_file.rows == 5
        assert parquet_file.size > 0
        assert parquet_file.compression_ratio > 0

    def test_convert_excel(self):
        """测试 Excel 转换功能"""
        # 创建测试文件和 DataFile 对象
        excel_path = self.create_test_excel_file()
        data_file = DataFile(
            filename="test.xlsx",
            format=FileFormat.EXCEL,
            size=os.path.getsize(excel_path),
            path=excel_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_file = self.converter.convert_file(data_file, output_dir)

        # 验证结果
        assert parquet_file is not None
        # 由于是多工作表文件，应该创建目录
        sheets_dir = os.path.join(output_dir, "test")
        assert os.path.exists(sheets_dir)
        assert os.path.exists(os.path.join(sheets_dir, "Sheet1.parquet"))
        assert os.path.exists(os.path.join(sheets_dir, "Sheet2.parquet"))

    def test_convert_tsv(self):
        """测试 TSV 转换功能"""
        # 创建测试文件和 DataFile 对象
        tsv_path = self.create_test_tsv_file()
        data_file = DataFile(
            filename="test.tsv",
            format=FileFormat.TSV,
            size=os.path.getsize(tsv_path),
            path=tsv_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_file = self.converter.convert_file(data_file, output_dir)

        # 验证结果
        assert parquet_file is not None
        assert parquet_file.filename == "test.parquet"
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))
        assert parquet_file.rows == 5
        assert parquet_file.size > 0
        assert parquet_file.compression_ratio > 0

    def test_unsupported_format(self):
        """测试不支持的格式"""
        # 创建测试文件和 DataFile 对象
        test_path = os.path.join(self.temp_dir.name, "test.xyz")
        with open(test_path, "w") as f:
            f.write("test content")

        data_file = DataFile(
            filename="test.xyz",
            format=FileFormat.OTHER,
            size=os.path.getsize(test_path),
            path=test_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 尝试转换文件，应该抛出异常
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        with pytest.raises(UnsupportedFormatError):
            self.converter.convert_file(data_file, output_dir)

    def test_convert_dataset_single_file(self):
        """测试批量转换单个文件"""
        # 创建测试文件和 DataFile 对象
        csv_path = self.create_test_csv_file()
        data_file = DataFile(
            filename="test.csv",
            format=FileFormat.CSV,
            size=os.path.getsize(csv_path),
            path=csv_path,
            download_status=DownloadStatus.COMPLETED
        )

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_files = self.converter.convert_dataset([data_file], output_dir)

        # 验证结果
        assert len(parquet_files) == 1
        assert parquet_files[0].filename == "test.parquet"
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))

    def test_convert_dataset_multiple_files(self):
        """测试批量转换多个文件"""
        # 创建测试文件和 DataFile 对象
        files = []
        for i, create_func in enumerate([
            self.create_test_csv_file,
            self.create_test_json_file,
            self.create_test_tsv_file
        ]):
            path = create_func()
            filename = os.path.basename(path)
            format_map = {
                "test.csv": FileFormat.CSV,
                "test.json": FileFormat.JSON,
                "test.tsv": FileFormat.TSV
            }
            data_file = DataFile(
                filename=filename,
                format=format_map[filename],
                size=os.path.getsize(path),
                path=path,
                download_status=DownloadStatus.COMPLETED
            )
            files.append(data_file)

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        parquet_files = self.converter.convert_dataset(files, output_dir)

        # 验证结果
        assert len(parquet_files) == 3
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))

    def test_multi_process_convert(self):
        """测试多进程转换"""
        # 创建测试文件和 DataFile 对象
        files = []
        for i, create_func in enumerate([
            self.create_test_csv_file,
            self.create_test_json_file,
            self.create_test_tsv_file
        ]):
            path = create_func()
            filename = os.path.basename(path)
            format_map = {
                "test.csv": FileFormat.CSV,
                "test.json": FileFormat.JSON,
                "test.tsv": FileFormat.TSV
            }
            data_file = DataFile(
                filename=filename,
                format=format_map[filename],
                size=os.path.getsize(path),
                path=path,
                download_status=DownloadStatus.COMPLETED
            )
            files.append(data_file)

        # 创建使用多进程的转换器
        converter = DataConverter(compression="snappy", processes=2)

        # 转换文件
        output_dir = os.path.join(self.output_dir, "output_mp")
        os.makedirs(output_dir, exist_ok=True)
        parquet_files = converter.convert_dataset(files, output_dir)

        # 验证结果
        assert len(parquet_files) == 3
        assert os.path.exists(os.path.join(output_dir, "test.parquet"))