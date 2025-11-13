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

# 将在模块完成后导入核心类和函数
# from .models import Dataset, DataFile, ParquetFile
# from .kaggle_client import KaggleClient
# from .converter import DataConverter
# from .storage import StorageManager
# from .helpers import download_and_convert

__all__ = [
    # "Dataset",
    # "DataFile",
    # "ParquetFile",
    # "KaggleClient",
    # "DataConverter",
    # "StorageManager",
    # "download_and_convert"
]