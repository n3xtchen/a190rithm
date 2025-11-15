"""
下载状态跟踪模块

提供跟踪和记录数据集下载进度的功能。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import Dataset, DataFile, DatasetStatus, DownloadStatus
from .utils.logging_utils import LoggerAdapter


# 创建日志记录器
logger = LoggerAdapter("download_tracker")


class DownloadTracker:
    """
    跟踪和记录数据集下载进度。

    属性:
        dataset_path: 数据集存储路径
        log_file: 日志文件路径
        status_file: 状态文件路径
    """

    def __init__(self, dataset_path: str):
        """
        初始化下载跟踪器。

        参数:
            dataset_path: 数据集存储路径
        """
        self.dataset_path = Path(dataset_path)
        self.logs_dir = self.dataset_path / "logs"
        self.log_file = self.logs_dir / "download.log"
        self.status_file = self.logs_dir / "download_status.json"

        # 确保日志目录存在
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def start_tracking(self, dataset: Dataset) -> None:
        """
        开始跟踪数据集下载。

        参数:
            dataset: 要跟踪的数据集
        """
        logger.info(f"开始跟踪数据集下载: {dataset.id}")

        # 记录开始下载的时间
        dataset.status = DatasetStatus.DOWNLOADING
        dataset.timestamp = datetime.now()

        # 初始化文件下载状态
        for file in dataset.files:
            file.download_status = DownloadStatus.PENDING
            file.download_progress = 0.0

        # 保存初始状态
        self.update_status(dataset)
        self.log_event(dataset, "开始下载数据集")

    def update_file_progress(self, dataset: Dataset, filename: str, progress: float) -> None:
        """
        更新文件下载进度。

        参数:
            dataset: 数据集
            filename: 文件名
            progress: 下载进度（0-100）
        """
        # 查找对应的文件
        for file in dataset.files:
            if file.filename == filename:
                old_progress = file.download_progress
                file.download_progress = progress

                # 记录重要的进度节点
                if int(old_progress / 10) < int(progress / 10):
                    self.log_event(
                        dataset,
                        f"文件 {filename} 下载进度: {progress:.1f}%",
                        file=file
                    )

                # 如果下载完成，更新状态
                if progress >= 100.0:
                    file.download_status = DownloadStatus.COMPLETED
                    self.log_event(dataset, f"文件 {filename} 下载完成", file=file)
                elif progress > 0:
                    file.download_status = DownloadStatus.IN_PROGRESS

                # 更新状态文件
                self.update_status(dataset)
                break

    def complete_file(self, dataset: Dataset, filename: str) -> None:
        """
        标记文件下载完成。

        参数:
            dataset: 数据集
            filename: 文件名
        """
        for file in dataset.files:
            if file.filename == filename:
                file.download_status = DownloadStatus.COMPLETED
                file.download_progress = 100.0
                self.log_event(dataset, f"文件 {filename} 下载完成", file=file)
                self.update_status(dataset)
                break

    def fail_file(self, dataset: Dataset, filename: str, error_message: str) -> None:
        """
        标记文件下载失败。

        参数:
            dataset: 数据集
            filename: 文件名
            error_message: 错误信息
        """
        for file in dataset.files:
            if file.filename == filename:
                file.download_status = DownloadStatus.FAILED
                self.log_event(dataset, f"文件 {filename} 下载失败: {error_message}", file=file, level="ERROR")
                self.update_status(dataset)
                break

    def skip_file(self, dataset: Dataset, filename: str, reason: str) -> None:
        """
        标记文件被跳过。

        参数:
            dataset: 数据集
            filename: 文件名
            reason: 跳过原因
        """
        for file in dataset.files:
            if file.filename == filename:
                file.download_status = DownloadStatus.SKIPPED
                file.download_progress = 100.0
                self.log_event(dataset, f"文件 {filename} 跳过: {reason}", file=file)
                self.update_status(dataset)
                break

    def complete_download(self, dataset: Dataset) -> None:
        """
        标记数据集下载完成。

        参数:
            dataset: 数据集
        """
        # 检查所有文件的状态
        all_completed = all(
            file.download_status in (DownloadStatus.COMPLETED, DownloadStatus.SKIPPED)
            for file in dataset.files
        )

        if all_completed:
            dataset.status = DatasetStatus.DOWNLOADED
            self.log_event(dataset, f"数据集 {dataset.id} 下载完成，共 {len(dataset.files)} 个文件")
        else:
            # 如果有文件失败，标记为失败
            has_failed = any(file.download_status == DownloadStatus.FAILED for file in dataset.files)
            if has_failed:
                dataset.status = DatasetStatus.FAILED
                self.log_event(dataset, f"数据集 {dataset.id} 下载失败，部分文件未成功下载", level="ERROR")
            else:
                # 其他情况保持下载中状态
                self.log_event(dataset, f"数据集 {dataset.id} 下载进行中，部分文件尚未完成")

        self.update_status(dataset)

    def fail_download(self, dataset: Dataset, error_message: str) -> None:
        """
        标记数据集下载失败。

        参数:
            dataset: 数据集
            error_message: 错误信息
        """
        dataset.status = DatasetStatus.FAILED
        self.log_event(dataset, f"数据集 {dataset.id} 下载失败: {error_message}", level="ERROR")
        self.update_status(dataset)

    def update_status(self, dataset: Dataset) -> None:
        """
        更新下载状态文件。

        参数:
            dataset: 数据集
        """
        try:
            # 准备状态数据
            status_data = {
                "dataset_id": dataset.id,
                "name": dataset.name,
                "status": dataset.status.value,
                "timestamp": datetime.now().isoformat(),
                "files": [
                    {
                        "filename": file.filename,
                        "status": file.download_status.value,
                        "progress": file.download_progress,
                        "size": file.size
                    }
                    for file in dataset.files
                ]
            }

            # 保存到状态文件
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"更新状态文件失败: {e}")

    def log_event(
        self,
        dataset: Dataset,
        message: str,
        file: Optional[DataFile] = None,
        level: str = "INFO"
    ) -> None:
        """
        记录下载事件到日志文件。

        参数:
            dataset: 数据集
            message: 日志消息
            file: 相关的文件（可选）
            level: 日志级别
        """
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} [{level}] {message}"

            # 确保日志目录存在
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            # 追加到日志文件
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")

            # 同时使用日志记录器
            if level == "ERROR":
                logger.error(message)
            else:
                logger.info(message)

        except Exception as e:
            logger.error(f"写入日志文件失败: {e}")

    def get_status(self) -> Dict:
        """
        获取当前下载状态。

        返回:
            包含当前状态信息的字典
        """
        if self.status_file.exists():
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取状态文件失败: {e}")
                return {}
        else:
            return {}

    def resume_download(self) -> Optional[Dataset]:
        """
        从中断处恢复下载。

        返回:
            恢复的 Dataset 对象，如果没有可恢复的下载则返回 None
        """
        # 将在后续实现
        return None