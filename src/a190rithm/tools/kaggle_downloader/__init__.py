"""
Kaggle 数据下载与 Parquet 格式转换工具

该模块提供了从 Kaggle 平台下载数据集并将其转换为高效 Parquet 格式的功能。
通过该工具，数据科学家可以轻松获取 Kaggle 上的数据集，并优化其存储格式以提高数据处理效率。

基本用法:
    ```python
    from a190rithm.tools.kaggle_downloader import download_and_convert

    dataset, parquet_files = download_and_convert("username/dataset-name")
    ```

也可以通过命令行使用:
    ```bash
    kaggle-parquet download username/dataset-name
    ```
"""

__version__ = "0.1.0"

# 导出主要类和函数，方便用户直接从包中导入
from .kaggle_client import KaggleClient
from .converter import DataConverter
from .storage import StorageManager
from .models import Dataset, DataFile, ParquetFile, FileFormat
from .exceptions import (
    KaggleAPIError, AuthenticationError, DatasetNotFoundError,
    DownloadError, ConversionError, StorageError
)

__all__ = [
    "Dataset",
    "DataFile",
    "ParquetFile",
    "FileFormat",
    "KaggleClient",
    "DataConverter",
    "StorageManager",
    "download_and_convert",
    "KaggleAPIError",
    "AuthenticationError",
    "DatasetNotFoundError",
    "DownloadError",
    "ConversionError",
    "StorageError"
]

def download_and_convert(
    dataset_id: str,
    output_dir: str = "./data",
    include_files: list = None,
    exclude_files: list = None,
    force: bool = False,
    compression: str = "snappy",
    processes: int = None,
    **kwargs
):
    """
    一站式函数，从Kaggle下载数据集并转换为Parquet格式。

    参数:
        dataset_id: Kaggle数据集标识符，格式为 'username/dataset-name'
        output_dir: 输出目录，默认为 ./data
        include_files: 包含的文件类型列表，如 ['csv', 'json']
        exclude_files: 排除的文件类型列表，如 ['zip', 'tar']
        force: 是否覆盖已存在的文件，默认为False
        compression: Parquet压缩算法，默认为"snappy"
        processes: 并行处理使用的进程数，默认为None（使用CPU核心数）
        **kwargs: 传递给KaggleClient、DataConverter或StorageManager的额外参数

    返回:
        tuple: (Dataset, List[ParquetFile]) - 下载的数据集对象和转换后的Parquet文件列表

    示例:
        >>> from a190rithm.tools.kaggle_downloader import download_and_convert
        >>> dataset, parquet_files = download_and_convert("username/dataset-name")
        >>> print(f"下载了 {len(dataset.files)} 个文件，转换了 {len(parquet_files)} 个Parquet文件")
    """
    # 创建客户端
    client = KaggleClient()

    # 下载数据集
    dataset = client.download_dataset(
        dataset_id=dataset_id,
        path=output_dir,
        force=force,
        include_files=include_files,
        exclude_files=exclude_files
    )

    # 创建转换器
    converter = DataConverter(
        compression=compression,
        processes=processes
    )

    # 转换文件
    parquet_output_dir = f"{output_dir}/parquet"
    parquet_files = converter.convert_dataset(
        files=dataset.files,
        output_dir=parquet_output_dir,
        force=force
    )

    # 创建存储管理器
    storage_manager = StorageManager(base_dir=output_dir)

    # 存储转换后的文件
    storage_dir = storage_manager.store_parquet_files(dataset, parquet_files)

    return dataset, parquet_files