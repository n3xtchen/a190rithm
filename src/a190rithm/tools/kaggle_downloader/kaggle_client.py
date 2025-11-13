"""
Kaggle 客户端模块

提供与 Kaggle API 交互的功能，支持数据集搜索和下载。
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import kaggle
import keyring
from kaggle.api.kaggle_api_extended import KaggleApi
from tqdm import tqdm

from .config import Config
from .exceptions import (
    AuthenticationError, DatasetNotFoundError, DownloadError,
    KaggleAPIError, RateLimitError
)
from .models import Dataset, DataFile, DatasetStatus, DownloadStatus, FileFormat
from .utils.logging_utils import LoggerAdapter
from .utils.retry_utils import retry


# 创建日志记录器
logger = LoggerAdapter("kaggle_client")


class KaggleClient:
    """
    Kaggle API 客户端，处理与 Kaggle 平台的交互。

    属性:
        api: Kaggle API 实例
        config: 配置对象
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        retry_backoff_factor: 重试退避因子
    """

    def __init__(
        self,
        username: Optional[str] = None,
        key: Optional[str] = None,
        timeout: int = 600,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        use_keyring: bool = True,
        ssl_verify: bool = True
    ):
        """
        初始化 Kaggle 客户端。

        参数:
            username: Kaggle 用户名，如果为 None 则从密钥环、环境变量或配置获取
            key: Kaggle API 密钥，如果为 None 则从密钥环、环境变量或配置获取
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_backoff_factor: 重试退避因子
            use_keyring: 是否使用系统密钥环存储凭证
            ssl_verify: 是否验证SSL证书
        """
        self.config = Config()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.use_keyring = use_keyring
        self.ssl_verify = ssl_verify

        # 设置凭证
        self._setup_credentials(username, key)

        # 初始化 Kaggle API
        self.api = KaggleApi()
        self._authenticate()

    def _setup_credentials(self, username: Optional[str], key: Optional[str]) -> None:
        """
        设置 Kaggle API 凭证。

        参数:
            username: Kaggle 用户名，如果为 None 则从密钥环、环境变量或配置获取
            key: Kaggle API 密钥，如果为 None 则从密钥环、环境变量或配置获取
        """
        # 优先使用传入的凭证
        if username and key:
            os.environ["KAGGLE_USERNAME"] = username
            os.environ["KAGGLE_KEY"] = key
            return

        # 尝试从密钥环获取凭证
        if self.use_keyring:
            try:
                keyring_username = keyring.get_password("kaggle-parquet", "username")
                keyring_key = keyring.get_password("kaggle-parquet", "key")
                if keyring_username and keyring_key:
                    os.environ["KAGGLE_USERNAME"] = keyring_username
                    os.environ["KAGGLE_KEY"] = keyring_key
                    logger.debug("从系统密钥环加载凭证")
                    return
            except Exception as e:
                logger.warning(f"从密钥环获取凭证失败: {e}")

        # 尝试从配置获取凭证
        config_username = self.config.get("kaggle.username")
        config_key = self.config.get("kaggle.key")

        # 如果配置值不是环境变量引用，则直接使用
        if config_username and not config_username.startswith("${") and config_key and not config_key.startswith("${"):
            os.environ["KAGGLE_USERNAME"] = config_username
            os.environ["KAGGLE_KEY"] = config_key
            logger.debug("从配置文件加载凭证")

    def _authenticate(self) -> None:
        """
        向 Kaggle API 进行身份验证。

        抛出:
            AuthenticationError: 当身份验证失败时
        """
        try:
            self.api.authenticate()
            logger.debug("Kaggle API 认证成功")
        except Exception as e:
            logger.error(f"Kaggle API 认证失败: {e}")
            raise AuthenticationError(f"Kaggle API 认证失败: {e}")

    @retry(exceptions=[KaggleAPIError, RateLimitError], tries=3, delay=1.0, backoff=2.0)
    def search_datasets(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        搜索 Kaggle 数据集。

        参数:
            query: 搜索查询
            max_results: 最大结果数量

        返回:
            符合查询的数据集列表

        抛出:
            KaggleAPIError: 当 API 请求失败时
        """
        try:
            logger.info(f"搜索数据集，查询: '{query}'")
            datasets = self.api.dataset_list(search=query, page_size=max_results)
            return [self._parse_dataset_metadata(ds) for ds in datasets]
        except Exception as e:
            logger.error(f"搜索数据集失败: {e}")
            raise KaggleAPIError(f"搜索数据集失败: {e}")

    def _parse_dataset_metadata(self, kaggle_dataset) -> Dict:
        """
        解析 Kaggle 数据集元数据。

        参数:
            kaggle_dataset: Kaggle API 返回的数据集对象

        返回:
            包含数据集信息的字典
        """
        return {
            "ref": f"{kaggle_dataset.owner}/{kaggle_dataset.ref}",
            "title": kaggle_dataset.title,
            "url": kaggle_dataset.url,
            "size": kaggle_dataset.size,
            "lastUpdated": kaggle_dataset.lastUpdated,
            "downloadCount": kaggle_dataset.downloadCount,
            "description": kaggle_dataset.description
        }

    @retry(exceptions=[KaggleAPIError, RateLimitError], tries=3, delay=1.0, backoff=2.0)
    def dataset_metadata(self, dataset_id: str) -> Dict:
        """
        获取数据集元数据。

        参数:
            dataset_id: 数据集标识符，格式为 'username/dataset-name'

        返回:
            数据集元数据字典

        抛出:
            KaggleAPIError: 当 API 请求失败时
            DatasetNotFoundError: 当数据集不存在时
        """
        try:
            logger.info(f"获取数据集元数据: {dataset_id}")
            # 检查数据集是否存在
            owner, name = dataset_id.split("/")
            datasets = self.api.dataset_list(owner=owner, search=name)

            # 找到匹配的数据集
            matching_datasets = [ds for ds in datasets if f"{ds.owner}/{ds.ref}" == dataset_id]
            if not matching_datasets:
                raise DatasetNotFoundError(f"找不到数据集: {dataset_id}")

            # 获取数据集文件列表
            dataset = matching_datasets[0]
            files = self.api.dataset_list_files(dataset_id).files

            # 解析元数据
            metadata = self._parse_dataset_metadata(dataset)
            metadata["files"] = [{"name": f.name, "size": f.size} for f in files]
            return metadata
        except DatasetNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取数据集元数据失败: {e}")
            raise KaggleAPIError(f"获取数据集元数据失败: {e}")

    def download_dataset(
        self,
        dataset_id: str,
        path: str = None,
        force: bool = False,
        quiet: bool = False,
        include_files: List[str] = None,
        exclude_files: List[str] = None
    ) -> Dataset:
        """
        下载 Kaggle 数据集。

        参数:
            dataset_id: 数据集标识符，格式为 'username/dataset-name'
            path: 下载路径，如果为 None 则使用默认路径
            force: 是否强制重新下载已存在的文件
            quiet: 是否静默模式
            include_files: 要包含的文件列表（支持通配符）
            exclude_files: 要排除的文件列表（支持通配符）

        返回:
            Dataset 对象

        抛出:
            KaggleAPIError: 当 API 请求失败时
            DatasetNotFoundError: 当数据集不存在时
            DownloadError: 当下载失败时
        """
        # 如果路径为 None，使用配置的输出目录
        if path is None:
            path = self.config.get("output.dir")

        # 确保路径存在
        path = os.path.expanduser(path)
        os.makedirs(path, exist_ok=True)

        try:
            # 获取数据集元数据
            logger.info(f"开始下载数据集: {dataset_id}")
            metadata = self.dataset_metadata(dataset_id)

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 使用 Kaggle API 下载数据集
                logger.debug(f"将数据集 {dataset_id} 下载到临时目录: {temp_dir}")
                try:
                    self.api.dataset_download_files(
                        dataset_id,
                        path=temp_dir,
                        unzip=True,
                        quiet=quiet,
                        force=force
                    )
                except Exception as e:
                    logger.error(f"下载数据集失败: {e}")
                    raise DownloadError(f"下载数据集失败: {e}", dataset_id=dataset_id)

                # 创建 Dataset 对象
                dataset = self._create_dataset_from_metadata(metadata)
                dataset.status = DatasetStatus.DOWNLOADING

                # 创建目标目录（根据配置的结构）
                owner, name = dataset_id.split("/")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                dataset_dir_name = f"{name}_{timestamp}"
                dataset_path = os.path.join(path, "kaggle", dataset_dir_name)
                original_path = os.path.join(dataset_path, "original")
                logs_path = os.path.join(dataset_path, "logs")

                os.makedirs(original_path, exist_ok=True)
                os.makedirs(logs_path, exist_ok=True)

                # 处理下载的文件
                temp_path = Path(temp_dir)
                downloaded_files = []

                # 查找所有文件
                all_files = list(temp_path.glob("**/*"))
                files = [f for f in all_files if f.is_file()]

                # 过滤文件（如果指定了包含/排除模式）
                if include_files or exclude_files:
                    # 实现文件过滤逻辑
                    pass

                # 移动文件到目标目录
                for file_path in files:
                    # 构建目标路径
                    rel_path = file_path.relative_to(temp_path)
                    dest_path = os.path.join(original_path, str(rel_path))

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    # 复制文件
                    shutil.copy2(file_path, dest_path)

                    # 创建 DataFile 对象
                    file_size = os.path.getsize(file_path)
                    file_format = self._detect_file_format(file_path)
                    data_file = DataFile(
                        filename=str(rel_path),
                        format=file_format,
                        size=file_size,
                        path=dest_path,
                        download_status=DownloadStatus.COMPLETED,
                        download_progress=100.0
                    )
                    downloaded_files.append(data_file)

                # 更新数据集对象
                dataset.files = downloaded_files
                dataset.size = sum(f.size for f in downloaded_files)
                dataset.status = DatasetStatus.DOWNLOADED

                # 将数据集元数据保存到文件
                self._save_metadata(dataset, dataset_path)

                logger.info(f"数据集 {dataset_id} 下载完成，共 {len(downloaded_files)} 个文件")
                return dataset

        except (DatasetNotFoundError, DownloadError):
            raise
        except Exception as e:
            logger.error(f"下载数据集时出错: {e}")
            raise DownloadError(f"下载数据集时出错: {e}", dataset_id=dataset_id)

    def _create_dataset_from_metadata(self, metadata: Dict) -> Dataset:
        """
        从元数据创建 Dataset 对象。

        参数:
            metadata: 数据集元数据字典

        返回:
            Dataset 对象
        """
        dataset_id = metadata["ref"]
        owner, name = dataset_id.split("/")

        return Dataset(
            id=dataset_id,
            name=name,
            owner=owner,
            url=metadata["url"],
            description=metadata.get("description", ""),
            metadata=metadata
        )

    def _detect_file_format(self, file_path: Union[str, Path]) -> FileFormat:
        """
        检测文件格式。

        参数:
            file_path: 文件路径

        返回:
            FileFormat 枚举值
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return FileFormat.CSV
        elif suffix in (".json", ".jsonl"):
            return FileFormat.JSON
        elif suffix in (".xls", ".xlsx"):
            return FileFormat.EXCEL
        elif suffix == ".tsv":
            return FileFormat.TSV
        elif suffix == ".parquet":
            return FileFormat.PARQUET
        elif suffix == ".avro":
            return FileFormat.AVRO
        elif suffix == ".orc":
            return FileFormat.ORC
        elif suffix in (".xml", ".svg"):
            return FileFormat.XML
        elif suffix in (".html", ".htm"):
            return FileFormat.HTML
        elif suffix in (".txt", ".md", ".rst"):
            return FileFormat.TXT
        else:
            return FileFormat.OTHER

    def _save_metadata(self, dataset: Dataset, dataset_path: str) -> None:
        """
        保存数据集元数据到文件。

        参数:
            dataset: Dataset 对象
            dataset_path: 数据集目录路径
        """
        import json

        # 准备要保存的元数据
        metadata = {
            "id": dataset.id,
            "name": dataset.name,
            "owner": dataset.owner,
            "url": dataset.url,
            "size": dataset.size,
            "timestamp": datetime.now().isoformat(),
            "description": dataset.description,
            "files": [
                {
                    "filename": file.filename,
                    "format": file.format.value,
                    "size": file.size,
                    "path": file.path,
                    "columns": file.columns
                }
                for file in dataset.files
            ],
            "status": dataset.status.value
        }

        # 添加原始元数据
        if dataset.metadata:
            metadata["original_metadata"] = dataset.metadata

        # 保存到文件
        metadata_path = os.path.join(dataset_path, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.debug(f"数据集元数据已保存到 {metadata_path}")

    def download_file(
        self,
        dataset_id: str,
        file_name: str,
        path: str = None,
        force: bool = False
    ) -> DataFile:
        """
        下载单个文件。

        参数:
            dataset_id: 数据集标识符
            file_name: 文件名
            path: 下载路径
            force: 是否强制重新下载

        返回:
            DataFile 对象

        抛出:
            KaggleAPIError: 当 API 请求失败时
            FileNotFoundError: 当文件不存在时
            DownloadError: 当下载失败时
        """
        # 此方法将在后续实现
        raise NotImplementedError("此方法尚未实现")

    def verify_credentials(self) -> bool:
        """
        验证 Kaggle API 凭证。

        返回:
            凭证有效时返回 True，否则返回 False
        """
        try:
            self._authenticate()
            return True
        except AuthenticationError:
            return False