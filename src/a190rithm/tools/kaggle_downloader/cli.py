"""
命令行接口模块

提供 kaggle-parquet 命令行工具的实现，允许通过命令行下载和转换 Kaggle 数据集。
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。

    返回:
        argparse.ArgumentParser: 配置好的参数解析器
    """
    parser = argparse.ArgumentParser(
        prog="kaggle-parquet",
        description="从 Kaggle 下载数据集并转换为 Parquet 格式",
        epilog="了解更多信息，请访问 https://github.com/user/a190rithm"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="设置日志级别 (默认: INFO)"
    )
    parser.add_argument(
        "--config", "-c",
        default="~/.kaggle-parquet/config.yml",
        help="指定配置文件路径 (默认: ~/.kaggle-parquet/config.yml)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./data",
        help="指定数据输出目录 (默认: ./data)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细输出模式"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，只显示错误信息"
    )

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # download 子命令
    download_parser = subparsers.add_parser(
        "download",
        help="从 Kaggle 下载数据集"
    )
    download_parser.add_argument(
        "dataset_id",
        help="Kaggle 数据集标识符，格式为 'username/dataset-name'"
    )
    download_parser.add_argument(
        "--no-convert",
        action="store_true",
        help="仅下载数据集，不进行 Parquet 转换"
    )
    download_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="覆盖已存在的文件"
    )
    download_parser.add_argument(
        "--limit",
        type=int,
        help="限制下载的文件数量"
    )
    download_parser.add_argument(
        "--include",
        help="包含的文件类型，多个类型用逗号分隔 (例如 'csv,json')"
    )
    download_parser.add_argument(
        "--exclude",
        help="排除的文件类型，多个类型用逗号分隔"
    )
    download_parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="下载超时时间（秒）(默认: 600)"
    )
    download_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="下载失败重试次数 (默认: 3)"
    )
    download_parser.add_argument(
        "--concurrent",
        type=int,
        default=2,
        help="并发下载文件数量 (默认: 2)"
    )

    # convert 子命令
    convert_parser = subparsers.add_parser(
        "convert",
        help="将已下载的数据文件转换为 Parquet 格式"
    )
    convert_parser.add_argument(
        "path",
        help="数据文件或目录路径"
    )
    convert_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="递归处理子目录"
    )
    convert_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="覆盖已存在的 Parquet 文件"
    )
    convert_parser.add_argument(
        "--compression",
        choices=["none", "snappy", "gzip", "brotli", "lz4", "zstd"],
        default="snappy",
        help="Parquet 压缩算法 (默认: snappy)"
    )
    convert_parser.add_argument(
        "--chunk-size",
        type=int,
        default=100000,
        help="处理大文件时的分块大小（行数）(默认: 100000)"
    )
    convert_parser.add_argument(
        "--preserve-index",
        action="store_true",
        help="保留原始数据索引"
    )
    convert_parser.add_argument(
        "--partition-by",
        help="按指定列分区 (例如 'year,month')"
    )
    convert_parser.add_argument(
        "--row-group-size",
        type=int,
        default=100000,
        help="Parquet 行组大小 (默认: 100000)"
    )
    convert_parser.add_argument(
        "--processes", "-p",
        type=int,
        help="并行处理使用的进程数 (默认: CPU核心数)"
    )

    # config 子命令
    config_parser = subparsers.add_parser(
        "config",
        help="管理配置设置"
    )
    config_parser.add_argument(
        "key",
        nargs="?",
        help="配置键名"
    )
    config_parser.add_argument(
        "value",
        nargs="?",
        help="配置值"
    )
    config_parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出当前配置"
    )
    config_parser.add_argument(
        "--reset",
        action="store_true",
        help="重置为默认配置"
    )
    config_parser.add_argument(
        "--set-kaggle-credentials",
        action="store_true",
        help="交互式设置 Kaggle API 凭据"
    )
    config_parser.add_argument(
        "--use-keyring",
        action="store_true",
        help="使用系统密钥环存储凭据"
    )

    # list 子命令
    list_parser = subparsers.add_parser(
        "list",
        help="列出已下载的数据集"
    )
    list_parser.add_argument(
        "--detail", "-d",
        action="store_true",
        help="显示详细信息"
    )
    list_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="输出格式 (默认: table)"
    )
    list_parser.add_argument(
        "--filter",
        help="按属性过滤 (例如 'name=iris')"
    )

    return parser


def handle_download(args: argparse.Namespace) -> int:
    """
    处理 download 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    from .kaggle_client import KaggleClient
    from .download_tracker import DownloadTracker
    from .converter import DataConverter
    from .storage import StorageManager
    from .exceptions import (
        AuthenticationError, DatasetNotFoundError,
        DownloadError, KaggleAPIError, ConversionError, StorageError
    )
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 解析包含/排除文件参数
    include_files = args.include.split(",") if args.include else None
    exclude_files = args.exclude.split(",") if args.exclude else None

    try:
        # 创建 Kaggle 客户端
        client = KaggleClient(
            timeout=args.timeout,
            max_retries=args.retries
        )

        # 验证凭证
        if not client.verify_credentials():
            print("错误: Kaggle API 凭证无效，请设置有效的凭证")
            print("可以使用以下方式设置凭证:")
            print("1. 运行 'kaggle-parquet config --set-kaggle-credentials'")
            print("2. 设置环境变量 KAGGLE_USERNAME 和 KAGGLE_KEY")
            print("3. 编辑 ~/.kaggle-parquet/config.yml 文件")
            return 3

        # 下载数据集
        print(f"下载数据集: {args.dataset_id}")
        print(f"目标目录: {args.output_dir or client.config.get('output.dir')}")

        dataset = client.download_dataset(
            dataset_id=args.dataset_id,
            path=args.output_dir,
            force=args.force,
            quiet=args.quiet,
            include_files=include_files,
            exclude_files=exclude_files
        )

        # 创建下载跟踪器并完成下载
        tracker = DownloadTracker(dataset.files[0].path.rsplit("/original", 1)[0])
        tracker.complete_download(dataset)

        print(f"数据集下载完成: {dataset.id}")
        print(f"  - 文件数量: {len(dataset.files)}")
        print(f"  - 总大小: {dataset.size / 1024 / 1024:.2f} MB")

        # 如果不需要转换，直接返回
        if args.no_convert:
            print("跳过转换，下载过程已完成")
            return 0

        # 进行转换
        print("开始转换文件为 Parquet 格式...")

        # 创建转换器
        converter = DataConverter(
            compression="snappy",  # 默认使用snappy压缩
            processes=args.concurrent  # 使用与下载相同的并发数
        )

        # 转换文件
        parquet_output_dir = os.path.join(os.path.dirname(dataset.files[0].path), "parquet")
        os.makedirs(parquet_output_dir, exist_ok=True)

        try:
            parquet_files = converter.convert_dataset(
                files=dataset.files,
                output_dir=parquet_output_dir,
                force=args.force
            )

            print(f"转换完成: {len(parquet_files)}/{len(dataset.files)} 个文件成功转换")

            # 创建存储管理器
            storage_manager = StorageManager(base_dir=args.output_dir)

            # 存储转换后的文件
            print("存储转换后的文件...")
            storage_dir = storage_manager.store_parquet_files(dataset, parquet_files)

            print(f"数据集已存储到: {storage_dir}")
            print("可以使用 'kaggle-parquet list' 命令查看已下载的数据集")

        except ConversionError as e:
            print(f"转换错误: {e}")
            return 5

        except StorageError as e:
            print(f"存储错误: {e}")
            return 6

        return 0

    except AuthenticationError as e:
        print(f"认证错误: {e}")
        return 3
    except DatasetNotFoundError as e:
        print(f"数据集不存在: {e}")
        return 1
    except DownloadError as e:
        print(f"下载错误: {e}")
        return 4
    except KaggleAPIError as e:
        print(f"Kaggle API 错误: {e}")
        return 3
    except Exception as e:
        print(f"未知错误: {e}")
        return 1


def handle_convert(args: argparse.Namespace) -> int:
    """
    处理 convert 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    import os
    import glob
    from pathlib import Path
    import time
    from tqdm import tqdm

    from .converter import DataConverter
    from .exceptions import ConversionError, UnsupportedFormatError
    from .models import DataFile
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 创建转换器
    converter = DataConverter(
        compression=args.compression,
        chunk_size=args.chunk_size,
        row_group_size=args.row_group_size,
        preserve_index=args.preserve_index,
        partition_cols=args.partition_by.split(",") if args.partition_by else None,
        processes=args.processes
    )

    # 处理分区列
    partition_cols = None
    if args.partition_by:
        partition_cols = [col.strip() for col in args.partition_by.split(",")]

    # 准备输出目录
    output_dir = os.path.dirname(args.path) if os.path.isfile(args.path) else args.path
    output_dir = os.path.join(output_dir, "parquet")
    os.makedirs(output_dir, exist_ok=True)

    # 收集需要转换的文件
    files_to_convert = []
    total_size = 0

    # 根据路径是文件还是目录进行不同处理
    if os.path.isfile(args.path):
        # 单个文件
        try:
            file_path = args.path
            file_size = os.path.getsize(file_path)
            file_format = converter.detect_format(file_path)

            if not converter.is_supported_format(file_format):
                print(f"警告: 文件格式不受支持: {file_path}")
                return 2

            data_file = DataFile(
                filename=os.path.basename(file_path),
                format=file_format,
                size=file_size,
                path=file_path
            )
            files_to_convert.append(data_file)
            total_size += file_size
            print(f"将转换文件: {file_path} ({file_format.value} 格式)")

        except Exception as e:
            print(f"处理文件时出错: {e}")
            return 1
    else:
        # 目录
        path_pattern = args.path
        if args.recursive:
            # 递归搜索
            search_pattern = os.path.join(path_pattern, "**", "*")
            file_paths = glob.glob(search_pattern, recursive=True)
        else:
            # 非递归搜索
            search_pattern = os.path.join(path_pattern, "*")
            file_paths = glob.glob(search_pattern, recursive=False)

        # 筛选文件并排除目录
        file_paths = [p for p in file_paths if os.path.isfile(p)]

        if not file_paths:
            print(f"没有找到文件: {search_pattern}")
            return 1

        # 添加到转换列表
        supported_count = 0
        unsupported_count = 0

        for file_path in tqdm(file_paths, desc="检查文件"):
            try:
                file_size = os.path.getsize(file_path)
                file_format = converter.detect_format(file_path)

                if converter.is_supported_format(file_format):
                    data_file = DataFile(
                        filename=os.path.relpath(file_path, path_pattern),
                        format=file_format,
                        size=file_size,
                        path=file_path
                    )
                    files_to_convert.append(data_file)
                    total_size += file_size
                    supported_count += 1
                else:
                    unsupported_count += 1
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")

        print(f"找到 {len(file_paths)} 个文件: {supported_count} 个支持转换, {unsupported_count} 个不支持")

    # 如果没有可转换的文件，退出
    if not files_to_convert:
        print("没有找到可转换的文件")
        return 0

    # 执行转换
    print(f"开始转换 {len(files_to_convert)} 个文件 (总大小: {total_size / 1024 / 1024:.2f} MB)")

    start_time = time.time()
    try:
        parquet_files = converter.convert_dataset(
            files=files_to_convert,
            output_dir=output_dir,
            force=args.force
        )

        # 计算总转换时间和压缩比
        elapsed_time = time.time() - start_time
        total_parquet_size = sum(f.size for f in parquet_files)
        compression_ratio = total_parquet_size / total_size if total_size > 0 else 1.0

        print(f"转换完成: {len(parquet_files)}/{len(files_to_convert)} 个文件成功转换")
        print(f"原始数据大小: {total_size / 1024 / 1024:.2f} MB")
        print(f"Parquet 数据大小: {total_parquet_size / 1024 / 1024:.2f} MB")
        print(f"平均压缩比: {compression_ratio:.2f}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"输出目录: {output_dir}")

        return 0

    except ConversionError as e:
        print(f"转换错误: {e}")
        return 3

    except UnsupportedFormatError as e:
        print(f"不支持的格式: {e}")
        return 4

    except Exception as e:
        print(f"未知错误: {e}")
        return 1


def handle_config(args: argparse.Namespace) -> int:
    """
    处理 config 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    import getpass
    import keyring
    import tabulate
    from .config import Config
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 创建配置对象
    config = Config(args.config)

    if args.list:
        # 列出所有配置
        configs = []
        for section in ["kaggle", "download", "convert", "output", "logging", "security"]:
            for key, value in _get_nested_config(config, section).items():
                configs.append([f"{section}.{key}", str(value)])

        # 以表格形式输出
        print(tabulate.tabulate(configs, headers=["配置项", "值"], tablefmt="psql"))
        return 0

    elif args.reset:
        # 重置配置
        config.reset()
        print("配置已重置为默认值")
        return 0

    elif args.set_kaggle_credentials:
        # 交互式设置 Kaggle 凭据
        print("设置 Kaggle API 凭据")
        print("请在 Kaggle 网站上创建 API 令牌: https://www.kaggle.com/settings")
        print()

        username = input("Kaggle 用户名: ").strip()
        key = getpass.getpass("Kaggle API 密钥: ").strip()

        if not username or not key:
            print("错误: 用户名和密钥不能为空")
            return 1

        # 保存凭据
        if args.use_keyring:
            try:
                keyring.set_password("kaggle-parquet", "username", username)
                keyring.set_password("kaggle-parquet", "key", key)
                print("凭据已保存到系统密钥环")
            except Exception as e:
                print(f"保存到密钥环失败: {e}")
                print("尝试保存到配置文件...")
                config.set("kaggle.username", username)
                config.set("kaggle.key", key)
                print("凭据已保存到配置文件")
        else:
            config.set("kaggle.username", username)
            config.set("kaggle.key", key)
            print("凭据已保存到配置文件")

        # 确保设置了使用密钥环的配置
        config.set("security.use_keyring", args.use_keyring)
        return 0

    elif args.key and args.value is not None:
        # 设置指定配置项
        config.set(args.key, args.value)
        print(f"已设置配置 {args.key}={args.value}")
        return 0

    elif args.key:
        # 获取指定配置项
        value = config.get(args.key)
        if value is None:
            print(f"配置项 {args.key} 不存在")
            return 1
        print(f"{args.key}={value}")
        return 0

    else:
        print("请指定操作或使用 --help 查看帮助")
        return 0


def _get_nested_config(config: 'Config', section: str) -> dict:
    """获取嵌套的配置部分"""
    result = {}
    section_dict = config.config.get(section, {})
    for key, value in section_dict.items():
        result[key] = value
    return result


def handle_list(args: argparse.Namespace) -> int:
    """
    处理 list 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    import json
    import os
    import tabulate
    import csv
    import sys

    from .config import Config
    from .storage import StorageManager
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 获取数据目录
    config = Config(args.config)
    base_dir = os.path.expanduser(config.get("output.dir", "./data"))

    # 创建存储管理器
    storage_manager = StorageManager(base_dir=base_dir)

    # 获取过滤模式
    pattern = None
    if args.filter:
        # 提取过滤参数
        try:
            filter_parts = args.filter.split("=", 1)
            if len(filter_parts) == 2:
                key, value = filter_parts
                if key == "name":
                    pattern = value
                # 暂时只支持按名称过滤，后续可以扩展
            else:
                # 如果没有等号，将整个过滤器视为名称模式
                pattern = args.filter
        except Exception as e:
            print(f"解析过滤器失败: {e}")

    # 列出数据集
    try:
        datasets = storage_manager.list_datasets(
            pattern=pattern,
            detail=args.detail,
            limit=100  # 设置一个合理的限制，防止输出过多
        )

        if not datasets:
            print("未找到符合条件的数据集")
            return 0

        # 输出结果
        if args.format == "json":
            # JSON 格式输出
            json.dump(datasets, sys.stdout, ensure_ascii=False, indent=2)
        elif args.format == "csv":
            # CSV 格式输出
            if not datasets:
                print("没有数据可导出为CSV")
                return 0

            # 确保所有记录有相同的字段
            all_keys = set()
            for dataset in datasets:
                all_keys.update(dataset.keys())

            # 将缺失的键添加到每个记录
            for dataset in datasets:
                for key in all_keys:
                    if key not in dataset:
                        dataset[key] = ""

            writer = csv.DictWriter(sys.stdout, fieldnames=sorted(list(all_keys)))
            writer.writeheader()
            writer.writerows(datasets)
        else:
            # 表格格式输出
            if args.detail:
                # 详细表格 - 展示部分元数据信息
                headers = ["名称", "数据集引用", "创建日期", "文件数量", "大小", "路径"]
                rows = []

                for d in datasets:
                    # 数据集名称
                    name = d.get("name", "")

                    # 数据集引用
                    dataset_ref = ""
                    if "dataset" in d and isinstance(d["dataset"], dict):
                        dataset_ref = d["dataset"].get("ref", "")

                    # 创建日期
                    created = ""
                    if "storage" in d and isinstance(d["storage"], dict):
                        created = d["storage"].get("created_at", "").split("T")[0]

                    # 文件数量
                    file_count = 0
                    if "parquet_files" in d and isinstance(d["parquet_files"], list):
                        file_count = len(d["parquet_files"])

                    # 大小信息
                    size = "未知"
                    if "parquet_files" in d and isinstance(d["parquet_files"], list):
                        total_size = sum(pf.get("size", 0) for pf in d["parquet_files"])
                        size = f"{total_size / 1024 / 1024:.2f} MB"

                    # 路径
                    path = d.get("dir", "")

                    rows.append([name, dataset_ref, created, file_count, size, path])
            else:
                # 简单表格
                headers = ["名称", "数据集引用", "文件数", "创建日期", "路径"]
                rows = []

                for d in datasets:
                    name = d.get("name", "")
                    dataset_ref = d.get("dataset_ref", "")
                    file_count = d.get("file_count", 0)
                    created = d.get("created", "").split("T")[0] if d.get("created") else ""
                    path = d.get("path", "")

                    rows.append([name, dataset_ref, file_count, created, path])

            print(tabulate.tabulate(rows, headers=headers, tablefmt="psql"))

            # 打印汇总信息
            print(f"\n找到 {len(datasets)} 个数据集")

        return 0

    except Exception as e:
        print(f"列出数据集时发生错误: {e}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    主函数，程序入口点。

    参数:
        argv: 命令行参数，默认为 None 使用 sys.argv

    返回:
        int: 退出状态码
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # 设置日志级别
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    if not args.command:
        parser.print_help()
        return 0

    # 处理子命令
    if args.command == "download":
        return handle_download(args)
    elif args.command == "convert":
        return handle_convert(args)
    elif args.command == "config":
        return handle_config(args)
    elif args.command == "list":
        return handle_list(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())