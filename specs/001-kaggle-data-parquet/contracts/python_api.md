# Python API 接口规范

## 概述

除了命令行接口外，`kaggle-parquet` 还提供 Python API，允许开发者在自己的 Python 应用程序中集成 Kaggle 数据下载和 Parquet 转换功能。本文档定义了 Python API 的类、方法和使用方式。

## 模块结构

```python
from a190rithm.applications.kaggle_downloader import (
    KaggleClient,
    DataConverter,
    StorageManager,
    Dataset,
    DataFile,
    ParquetFile,
    download_and_convert,
)
```

## 核心类和方法

### KaggleClient

负责与 Kaggle API 交互的客户端类。

```python
class KaggleClient:
    """Kaggle API 客户端，处理与 Kaggle 平台的交互。"""

    def __init__(
        self,
        username: Optional[str] = None,
        key: Optional[str] = None,
        timeout: int = 600,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5
    ):
        """
        初始化 Kaggle 客户端。

        参数:
            username: Kaggle 用户名，如果为 None 则从环境变量或配置获取
            key: Kaggle API 密钥，如果为 None 则从环境变量或配置获取
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_backoff_factor: 重试退避因子
        """
        pass

    def search_datasets(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        搜索 Kaggle 数据集。

        参数:
            query: 搜索查询
            max_results: 最大结果数量

        返回:
            符合查询的数据集列表
        """
        pass

    def dataset_metadata(
        self,
        dataset_id: str
    ) -> Dict:
        """
        获取数据集元数据。

        参数:
            dataset_id: 数据集标识符，格式为 'username/dataset-name'

        返回:
            数据集元数据字典

        异常:
            KaggleAPIError: 当 API 请求失败时
            DatasetNotFoundError: 当数据集不存在时
        """
        pass

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

        异常:
            KaggleAPIError: 当 API 请求失败时
            DatasetNotFoundError: 当数据集不存在时
            DownloadError: 当下载失败时
        """
        pass

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

        异常:
            KaggleAPIError: 当 API 请求失败时
            FileNotFoundError: 当文件不存在时
            DownloadError: 当下载失败时
        """
        pass

    def verify_credentials(self) -> bool:
        """
        验证 Kaggle API 凭证。

        返回:
            凭证有效时返回 True，否则返回 False
        """
        pass
```

### DataConverter

负责将数据文件转换为 Parquet 格式的转换器类。

```python
class DataConverter:
    """将各种数据格式转换为 Parquet 格式的转换器。"""

    def __init__(
        self,
        compression: str = 'snappy',
        chunk_size: int = 100000,
        row_group_size: int = 100000,
        preserve_index: bool = False,
        processes: int = None
    ):
        """
        初始化数据转换器。

        参数:
            compression: Parquet 压缩算法
            chunk_size: 处理大文件时的分块大小（行数）
            row_group_size: Parquet 行组大小
            preserve_index: 是否保留原始数据索引
            processes: 并行处理使用的进程数，None 表示使用所有可用核心
        """
        pass

    def convert_file(
        self,
        file: Union[str, DataFile],
        output_path: str = None,
        partition_by: List[str] = None
    ) -> ParquetFile:
        """
        将单个文件转换为 Parquet 格式。

        参数:
            file: 文件路径或 DataFile 对象
            output_path: 输出路径，如果为 None 则在同目录下创建
            partition_by: 按指定列分区

        返回:
            ParquetFile 对象

        异常:
            FileNotFoundError: 当文件不存在时
            ConversionError: 当转换失败时
            UnsupportedFormatError: 当文件格式不受支持时
        """
        pass

    def convert_directory(
        self,
        directory: str,
        output_directory: str = None,
        recursive: bool = False,
        file_pattern: str = "*",
        force: bool = False
    ) -> List[ParquetFile]:
        """
        转换目录中的所有文件。

        参数:
            directory: 输入目录路径
            output_directory: 输出目录路径
            recursive: 是否递归处理子目录
            file_pattern: 文件模式（glob 格式）
            force: 是否覆盖已存在的文件

        返回:
            ParquetFile 对象列表

        异常:
            DirectoryNotFoundError: 当目录不存在时
            ConversionError: 当转换失败时
        """
        pass

    def convert_dataset(
        self,
        dataset: Dataset,
        output_path: str = None,
        include_formats: List[str] = None,
        exclude_formats: List[str] = None
    ) -> List[ParquetFile]:
        """
        转换整个数据集。

        参数:
            dataset: Dataset 对象
            output_path: 输出路径
            include_formats: 要包含的文件格式列表
            exclude_formats: 要排除的文件格式列表

        返回:
            ParquetFile 对象列表

        异常:
            ConversionError: 当转换失败时
        """
        pass

    @staticmethod
    def is_format_supported(file_format: str) -> bool:
        """
        检查文件格式是否支持转换为 Parquet。

        参数:
            file_format: 文件格式（如 'csv', 'json' 等）

        返回:
            格式受支持时返回 True，否则返回 False
        """
        pass
```

### StorageManager

负责管理数据文件存储的类。

```python
class StorageManager:
    """管理数据文件存储和组织。"""

    def __init__(
        self,
        base_dir: str = "./data",
        structure_template: str = "kaggle/{dataset_name}_{timestamp}"
    ):
        """
        初始化存储管理器。

        参数:
            base_dir: 基础目录
            structure_template: 目录结构模板
        """
        pass

    def get_dataset_path(
        self,
        dataset: Dataset
    ) -> str:
        """
        获取数据集存储路径。

        参数:
            dataset: Dataset 对象

        返回:
            数据集存储路径
        """
        pass

    def save_dataset_metadata(
        self,
        dataset: Dataset
    ) -> str:
        """
        保存数据集元数据。

        参数:
            dataset: Dataset 对象

        返回:
            元数据文件路径
        """
        pass

    def list_datasets(
        self,
        filter_expr: str = None
    ) -> List[Dataset]:
        """
        列出已下载的数据集。

        参数:
            filter_expr: 过滤表达式

        返回:
            Dataset 对象列表
        """
        pass

    def clean_temporary_files(
        self,
        dataset: Dataset = None,
        older_than: int = None
    ) -> int:
        """
        清理临时文件。

        参数:
            dataset: 指定数据集，如果为 None 则清理所有
            older_than: 清理早于指定天数的文件

        返回:
            清理的文件数量
        """
        pass
```

### 辅助函数

```python
def download_and_convert(
    dataset_id: str,
    output_dir: str = None,
    compression: str = 'snappy',
    include_files: List[str] = None,
    exclude_files: List[str] = None,
    partition_by: List[str] = None,
    force: bool = False,
    processes: int = None
) -> Tuple[Dataset, List[ParquetFile]]:
    """
    一步完成数据集下载和转换的辅助函数。

    参数:
        dataset_id: 数据集标识符
        output_dir: 输出目录
        compression: Parquet 压缩算法
        include_files: 要包含的文件列表
        exclude_files: 要排除的文件列表
        partition_by: 按指定列分区
        force: 是否覆盖已存在的文件
        processes: 并行处理使用的进程数

    返回:
        (Dataset, ParquetFiles列表) 元组

    异常:
        KaggleAPIError: 当 API 请求失败时
        DatasetNotFoundError: 当数据集不存在时
        ConversionError: 当转换失败时
    """
    pass
```

## 使用示例

```python
# 基本用法
from a190rithm.applications.kaggle_downloader import download_and_convert

# 下载并转换数据集
dataset, parquet_files = download_and_convert(
    "username/dataset-name",
    output_dir="./my_data",
    compression="snappy"
)

# 打印结果信息
print(f"下载了 {len(dataset.files)} 个文件")
print(f"转换了 {len(parquet_files)} 个 Parquet 文件")
for pf in parquet_files:
    print(f"{pf.filename}: {pf.rows} 行, 压缩比 {pf.compression_ratio:.2f}")

# 高级用法
from a190rithm.applications.kaggle_downloader import KaggleClient, DataConverter, StorageManager

# 初始化客户端
client = KaggleClient(
    max_retries=5,
    retry_backoff_factor=1.0
)

# 下载数据集
dataset = client.download_dataset(
    "username/dataset-name",
    include_files=["*.csv", "*.json"]
)

# 初始化转换器
converter = DataConverter(
    compression="zstd",
    processes=4
)

# 转换为 Parquet
parquet_files = converter.convert_dataset(
    dataset,
    partition_by=["year", "month"]
)

# 管理存储
storage = StorageManager(base_dir="./my_data")
metadata_path = storage.save_dataset_metadata(dataset)

# 列出已下载的数据集
all_datasets = storage.list_datasets()
```

## 异常类层次

```
BaseException
└── Exception
    └── KaggleParquetError                # 基础异常类
        ├── APIError                      # API 相关错误
        │   ├── KaggleAPIError            # Kaggle API 错误
        │   └── AuthenticationError       # 认证错误
        ├── DatasetError                  # 数据集相关错误
        │   ├── DatasetNotFoundError      # 数据集不存在
        │   ├── FileNotFoundError         # 文件不存在
        │   └── InvalidDatasetError       # 无效数据集
        ├── StorageError                  # 存储相关错误
        │   ├── DirectoryNotFoundError    # 目录不存在
        │   ├── PermissionDeniedError     # 权限被拒绝
        │   └── InsufficientSpaceError    # 存储空间不足
        ├── ConversionError               # 转换相关错误
        │   ├── UnsupportedFormatError    # 不支持的格式
        │   ├── InvalidSchemaError        # 无效架构
        │   └── DataCorruptionError       # 数据损坏
        ├── NetworkError                  # 网络相关错误
        │   ├── DownloadError             # 下载错误
        │   ├── TimeoutError              # 超时错误
        │   └── RateLimitError            # 速率限制错误
        └── ConfigurationError            # 配置相关错误
```