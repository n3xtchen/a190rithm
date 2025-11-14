"""
存储管理模块

提供将Parquet文件存储到data目录的功能，并管理元数据。
"""

import os
import json
import time
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import shutil

from .config import Config
from .models import Dataset, ParquetFile
from .utils.logging_utils import LoggerAdapter
from .exceptions import StorageError

# 创建日志记录器
logger = LoggerAdapter("storage_manager")


class StorageManager:
    """
    管理Parquet文件存储和数据集元数据。

    属性:
        config: 配置对象
        base_dir: 基础存储目录
        structure_template: 目录结构模板
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        base_dir: Optional[str] = None,
        structure_template: str = "kaggle/{dataset_name}_{timestamp}"
    ):
        """
        初始化存储管理器。

        参数:
            config: 配置对象，如果为None则创建默认配置
            base_dir: 基础存储目录，如果为None则使用配置中的data_dir
            structure_template: 目录结构模板
        """
        self.config = config if config else Config()
        self.base_dir = base_dir if base_dir else self.config.get("data_dir", os.path.join(os.getcwd(), "data"))
        self.structure_template = structure_template

        logger.debug(f"初始化存储管理器，基础目录: {self.base_dir}")

        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)

    def get_dataset_path(
        self,
        dataset: Dataset,
        timestamp: Optional[datetime.datetime] = None,
        create: bool = True
    ) -> str:
        """
        获取数据集的存储路径。

        参数:
            dataset: 数据集对象
            timestamp: 时间戳，如果为None则使用当前时间
            create: 是否创建目录

        返回:
            数据集存储路径
        """
        if timestamp is None:
            timestamp = datetime.datetime.now()

        # 格式化时间戳
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

        # 提取数据集名称
        dataset_name = dataset.name
        # 安全化数据集名称（移除不安全的字符）
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in dataset_name)

        # 构建路径
        path_template = self.structure_template.format(
            dataset_name=safe_name,
            timestamp=timestamp_str,
            owner=dataset.owner,
            ref=dataset.id,
            size=dataset.size,
            version=getattr(dataset, 'version', 'latest')
        )

        # 构建完整路径
        dataset_path = os.path.join(self.base_dir, path_template)

        # 如果需要，创建目录
        if create:
            os.makedirs(dataset_path, exist_ok=True)
            logger.debug(f"为数据集 {dataset.id} 创建目录: {dataset_path}")

        return dataset_path

    def store_parquet_files(
        self,
        dataset: Dataset,
        parquet_files: List[ParquetFile],
        timestamp: Optional[datetime.datetime] = None,
        organize: bool = True
    ) -> str:
        """
        存储Parquet文件到数据目录。

        参数:
            dataset: 数据集对象
            parquet_files: Parquet文件列表
            timestamp: 时间戳，如果为None则使用当前时间
            organize: 是否按结构组织文件

        返回:
            存储目录路径
        """
        if not parquet_files:
            logger.warning("没有Parquet文件需要存储")
            return ""

        # 获取存储路径
        storage_dir = self.get_dataset_path(dataset, timestamp)

        # 存储每个Parquet文件
        stored_files = []
        for pf in parquet_files:
            try:
                # 构建目标文件路径
                target_path = os.path.join(storage_dir, pf.filename)

                # 复制文件
                shutil.copy2(pf.path, target_path)

                # 更新Parquet文件路径
                pf.storage_path = target_path

                stored_files.append({
                    "original_filename": pf.original_file.filename,
                    "parquet_filename": pf.filename,
                    "size": pf.size,
                    "rows": pf.rows,
                    "compression_ratio": pf.compression_ratio
                })

                logger.debug(f"存储Parquet文件: {pf.filename} -> {target_path}")

            except Exception as e:
                logger.error(f"存储Parquet文件 {pf.filename} 失败: {e}")
                raise StorageError(f"存储Parquet文件失败: {e}")

        # 保存元数据
        self.save_metadata(dataset, parquet_files, storage_dir)

        logger.info(f"成功将 {len(parquet_files)} 个Parquet文件存储到 {storage_dir}")
        return storage_dir

    def save_metadata(
        self,
        dataset: Dataset,
        parquet_files: List[ParquetFile],
        storage_dir: str
    ) -> str:
        """
        保存数据集和Parquet文件的元数据。

        参数:
            dataset: 数据集对象
            parquet_files: Parquet文件列表
            storage_dir: 存储目录

        返回:
            元数据文件路径
        """
        metadata_path = os.path.join(storage_dir, "metadata.json")

        # 构建元数据
        metadata = {
            "dataset": {
                "ref": dataset.id,
                "name": dataset.name,
                "owner": dataset.owner,
                "size": dataset.size,
                "url": dataset.url,
                "download_timestamp": datetime.datetime.now().isoformat(),
                "file_count": len(dataset.files) if dataset.files else 0
            },
            "parquet_files": [
                {
                    "filename": pf.filename,
                    "original_filename": pf.original_file.filename if pf.original_file else "",
                    "size": pf.size,
                    "rows": pf.rows,
                    "compression_ratio": pf.compression_ratio,
                    "schema": pf.schema,
                    "partition_cols": pf.partition_cols,
                    "conversion_timestamp": pf.timestamp.isoformat() if pf.timestamp else None
                }
                for pf in parquet_files
            ],
            "storage": {
                "base_dir": self.base_dir,
                "structure_template": self.structure_template,
                "storage_dir": storage_dir,
                "created_at": datetime.datetime.now().isoformat()
            }
        }

        # 写入元数据文件
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"保存元数据到 {metadata_path}")
            return metadata_path

        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise StorageError(f"保存元数据失败: {e}")

    def list_datasets(
        self,
        pattern: Optional[str] = None,
        detail: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        列出存储的数据集。

        参数:
            pattern: 匹配模式（数据集名称）
            detail: 是否返回详细信息
            limit: 限制结果数量

        返回:
            数据集信息列表
        """
        # 基础路径模式匹配
        base_path = Path(self.base_dir)
        if not base_path.exists():
            logger.warning(f"基础目录不存在: {self.base_dir}")
            return []

        # 寻找所有kaggle子目录
        kaggle_dir = base_path / "kaggle"
        if not kaggle_dir.exists():
            logger.warning(f"Kaggle目录不存在: {kaggle_dir}")
            return []

        # 查找所有数据集目录
        dataset_dirs = list(kaggle_dir.glob("*"))

        # 过滤匹配模式
        if pattern:
            dataset_dirs = [d for d in dataset_dirs if pattern.lower() in d.name.lower()]

        # 限制结果数量
        if limit is not None and limit > 0:
            dataset_dirs = dataset_dirs[:limit]

        # 收集数据集信息
        datasets_info = []
        for dataset_dir in dataset_dirs:
            metadata_file = dataset_dir / "metadata.json"

            if detail:
                # 如果需要详细信息，读取元数据文件
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        datasets_info.append({
                            "dir": str(dataset_dir),
                            "name": dataset_dir.name,
                            "created": metadata["storage"]["created_at"],
                            "dataset": metadata["dataset"],
                            "parquet_files": metadata["parquet_files"],
                            "storage": metadata["storage"]
                        })
                    except Exception as e:
                        logger.warning(f"读取元数据文件失败: {metadata_file}: {e}")
                        datasets_info.append({
                            "dir": str(dataset_dir),
                            "name": dataset_dir.name,
                            "error": f"读取元数据失败: {e}"
                        })
                else:
                    # 如果没有元数据文件，添加基本信息
                    datasets_info.append({
                        "dir": str(dataset_dir),
                        "name": dataset_dir.name,
                        "metadata_missing": True
                    })
            else:
                # 简要信息
                created_time = ""
                dataset_ref = ""
                file_count = 0

                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        created_time = metadata["storage"]["created_at"]
                        dataset_ref = metadata["dataset"]["ref"]
                        file_count = len(metadata["parquet_files"])
                    except Exception:
                        pass

                datasets_info.append({
                    "name": dataset_dir.name,
                    "path": str(dataset_dir),
                    "created": created_time,
                    "dataset_ref": dataset_ref,
                    "file_count": file_count
                })

        # 按创建时间排序（最新的在前）
        datasets_info.sort(
            key=lambda x: x.get("created", ""),
            reverse=True
        )

        return datasets_info