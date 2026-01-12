"""
数据转换模块

提供将各种格式的数据文件转换为 Parquet 格式的功能。
"""

import os
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from .config import Config
from .models import DataFile, FileFormat, ParquetFile, ConversionStatus, DownloadStatus
from .exceptions import ConversionError, UnsupportedFormatError
from .utils.logging_utils import LoggerAdapter


# 创建日志记录器
logger = LoggerAdapter("data_converter")


def _convert_worker(file_data_dict, output_dir, compression, chunk_size, row_group_size, preserve_index, partition_cols):
    """
    工作进程的转换函数。
    """
    import os
    from datetime import datetime
    import pyarrow as pa
    import pyarrow.parquet as pq
    from .models import DataFile, FileFormat, DownloadStatus, ConversionStatus, ParquetFile

    try:
        # 重新创建 DataFile 对象
        data_file = DataFile(
            filename=file_data_dict['filename'],
            format=FileFormat(file_data_dict['format']),
            size=file_data_dict['size'],
            path=file_data_dict['path'],
            columns=file_data_dict.get('columns'),
            schema=file_data_dict.get('schema'),
            download_status=DownloadStatus(file_data_dict['download_status']),
            download_progress=file_data_dict['download_progress'],
            checksum=file_data_dict.get('checksum')
        )

        # 创建转换器实例（每个进程一个）
        converter = DataConverter(
            compression=compression,
            chunk_size=chunk_size,
            row_group_size=row_group_size,
            preserve_index=preserve_index,
            partition_cols=partition_cols,
            processes=1  # 在工作进程中只使用单线程
        )

        # 转换文件
        result = converter.convert_file(data_file, output_dir)
        
        if result is None:
            return {
                'success': False,
                'filename': file_data_dict['filename'],
                'error': '转换结果为 None'
            }

        # 由于不能直接返回 ParquetFile 对象（多进程 pickle 限制），
        # 我们返回一个字典，稍后会用它重建 ParquetFile 对象
        return {
            'success': True,
            'original_file': {
                'filename': data_file.filename,
                'format': data_file.format.value,
                'size': data_file.size,
                'path': data_file.path,
                'columns': data_file.columns,
                'schema': data_file.schema,
                'download_status': data_file.download_status.value,
                'download_progress': data_file.download_progress,
                'checksum': data_file.checksum
            },
            'filename': result.filename,
            'path': result.path,
            'size': result.size,
            'schema': result.schema,
            'rows': result.rows,
            'compression_ratio': result.compression_ratio,
            'partition_cols': result.partition_cols,
            'conversion_status': result.conversion_status.value,
            'timestamp': result.timestamp.isoformat(),
            'metadata': getattr(result, 'metadata', {})
        }
    except Exception as e:
        # 在多进程环境中，logger 可能会有问题，所以我们也捕获并打印
        print(f"工作进程转换文件失败: {file_data_dict['filename']} - {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'filename': file_data_dict['filename'],
            'error': str(e)
        }


class DataConverter:
    """
    提供将各种格式的数据文件转换为 Parquet 格式的功能。

    属性:
        config: 配置对象
        compression: Parquet 压缩算法
        chunk_size: 处理大文件时的分块大小（行数）
        row_group_size: Parquet 行组大小
        preserve_index: 是否保留原始数据索引
        partition_cols: 分区列（如果适用）
    """

    # 支持的文件格式
    SUPPORTED_FORMATS = {
        FileFormat.CSV,
        FileFormat.JSON,
        FileFormat.EXCEL,
        FileFormat.TSV,
        FileFormat.PARQUET  # 已经是 Parquet 格式，会直接复制
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        compression: str = "snappy",
        chunk_size: int = 100000,
        row_group_size: int = 100000,
        preserve_index: bool = False,
        partition_cols: Optional[List[str]] = None,
        processes: Optional[int] = None
    ):
        """
        初始化数据转换器。

        参数:
            config: 配置对象，如果为 None 则创建默认配置
            compression: Parquet 压缩算法（none, snappy, gzip, brotli, lz4, zstd）
            chunk_size: 处理大文件时的分块大小（行数）
            row_group_size: Parquet 行组大小
            preserve_index: 是否保留原始数据索引
            partition_cols: 分区列（如果适用）
            processes: 并行处理使用的进程数，默认为 CPU 核心数
        """
        self.config = config if config else Config()
        self.compression = compression
        self.chunk_size = chunk_size
        self.row_group_size = row_group_size
        self.preserve_index = preserve_index
        self.partition_cols = partition_cols
        self.processes = processes if processes is not None else max(1, mp.cpu_count() - 1)

        logger.debug(f"初始化数据转换器，压缩算法: {compression}，进程数: {self.processes}")

    def detect_format(self, file_path: Union[str, Path]) -> FileFormat:
        """
        检测文件格式。

        参数:
            file_path: 文件路径

        返回:
            FileFormat 枚举值

        抛出:
            UnsupportedFormatError: 当文件格式不受支持时
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        suffix = file_path.suffix.lower()

        # 根据文件扩展名判断格式
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

    def is_supported_format(self, file_format: FileFormat) -> bool:
        """
        检查文件格式是否受支持。

        参数:
            file_format: 文件格式

        返回:
            如果格式受支持则返回 True，否则返回 False
        """
        return file_format in self.SUPPORTED_FORMATS

    def convert_file(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """
        将单个数据文件转换为 Parquet 格式。

        参数:
            data_file: 数据文件对象
            output_dir: 输出目录

        返回:
            ParquetFile 对象

        抛出:
            UnsupportedFormatError: 当文件格式不受支持时
            ConversionError: 当转换过程中发生错误时
        """
        logger.info(f"转换文件: {data_file.filename}")

        # 检查格式是否支持
        if not self.is_supported_format(data_file.format):
            message = f"不支持的文件格式: {data_file.format.value}"
            logger.warning(message)
            raise UnsupportedFormatError(message)

        # 如果已经是 Parquet 格式，直接复制
        if data_file.format == FileFormat.PARQUET:
            return self._copy_parquet_file(data_file, output_dir)

        try:
            # 根据文件格式调用相应的转换方法
            if data_file.format == FileFormat.CSV:
                return self._convert_csv(data_file, output_dir)
            elif data_file.format == FileFormat.JSON:
                return self._convert_json(data_file, output_dir)
            elif data_file.format == FileFormat.EXCEL:
                return self._convert_excel(data_file, output_dir)
            elif data_file.format == FileFormat.TSV:
                return self._convert_tsv(data_file, output_dir)
            else:
                # 不应该到达这里，因为我们已经检查了格式是否支持
                message = f"未知的文件格式: {data_file.format.value}"
                logger.error(message)
                raise UnsupportedFormatError(message)

        except Exception as e:
            message = f"转换文件 {data_file.filename} 失败: {e}"
            logger.error(message)
            raise ConversionError(message, file=data_file.filename)

    def _copy_parquet_file(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """复制 Parquet 文件"""
        import shutil
        import pyarrow.parquet as pq

        # 构建输出文件路径
        output_filename = os.path.basename(data_file.filename)
        output_path = os.path.join(output_dir, output_filename)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 复制文件（如果源路径和目标路径不同）
        if os.path.abspath(data_file.path) != os.path.abspath(output_path):
            shutil.copy2(data_file.path, output_path)

        # 读取 Parquet 元数据
        parquet_file = pq.ParquetFile(output_path)
        row_count = parquet_file.metadata.num_rows
        schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
        parquet_size = os.path.getsize(output_path)

        return ParquetFile(
            original_file=data_file,
            filename=output_filename,
            path=output_path,
            size=parquet_size,
            schema=schema_dict,
            rows=row_count,
            compression_ratio=1.0,
            conversion_status=ConversionStatus.COMPLETED
        )

    def _convert_csv(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """
        将 CSV 文件转换为 Parquet 格式。

        参数:
            data_file: 数据文件对象
            output_dir: 输出目录

        返回:
            ParquetFile 对象

        抛出:
            ConversionError: 当转换过程中发生错误时
        """
        import pyarrow as pa
        import pyarrow.parquet as pq
        start_time = time.time()
        logger.info(f"转换 CSV 文件: {data_file.filename}")

        # 检查文件是否存在
        if not os.path.exists(data_file.path):
            raise ConversionError(f"文件不存在: {data_file.path}", file=data_file.filename)

        # 构建输出文件路径
        output_filename = os.path.splitext(os.path.basename(data_file.filename))[0] + ".parquet"
        output_path = os.path.join(output_dir, output_filename)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.join(output_dir, output_filename)), exist_ok=True)

        # 检查文件大小，决定是否使用分块读取
        file_size = os.path.getsize(data_file.path)
        use_chunks = file_size > 100 * 1024 * 1024  # 超过 100MB 使用分块读取

        try:
            if use_chunks:
                # 使用分块读取大文件
                logger.debug(f"文件较大 ({file_size / 1024 / 1024:.2f} MB)，使用分块读取")

                # 首先读取少量样本以推断数据类型和列名
                sample_df = pd.read_csv(
                    data_file.path,
                    nrows=1000,
                    low_memory=False
                )

                # 存储列信息
                columns = list(sample_df.columns)
                dtypes = sample_df.dtypes.to_dict()

                # 分块读取并写入
                # 指定 dtype 以确保所有块的一致性，特别是对于可能包含混合类型的列
                # 这里我们尝试使用 sample_df 的 dtypes，但对于 Object 类型，我们强制为 String
                # 以避免 pyarrow 在不同块中推断出不同的子类型
                forced_dtypes = {}
                for col, dtype in dtypes.items():
                    if dtype == 'object':
                        forced_dtypes[col] = str
                    else:
                        forced_dtypes[col] = dtype

                chunks = pd.read_csv(
                    data_file.path,
                    chunksize=self.chunk_size,
                    low_memory=False,
                    dtype=forced_dtypes
                )

                writer = None
                row_count = 0
                
                try:
                    for chunk in tqdm(chunks, desc="处理数据块"):
                        # 处理 NaN 值，以便更好地映射到 Parquet 类型
                        # chunk = chunk.where(pd.notnull(chunk), None)
                        
                        # 转换为 pyarrow Table
                        table = pa.Table.from_pandas(chunk, preserve_index=self.preserve_index)
                        
                        if writer is None:
                            # 初始化 Parquet 写入器
                            writer = pq.ParquetWriter(
                                output_path,
                                table.schema,
                                compression=self.compression
                            )
                        
                        # 写入数据块
                        writer.write_table(table)
                        row_count += len(chunk)
                finally:
                    if writer:
                        writer.close()
            else:
                # 直接读取小文件
                logger.debug(f"文件较小 ({file_size / 1024 / 1024:.2f} MB)，直接读取")
                df = pd.read_csv(data_file.path, low_memory=False)

                # 存储列信息
                columns = list(df.columns)
                dtypes = df.dtypes.to_dict()
                row_count = len(df)

                # 转换为 Parquet
                df.to_parquet(
                    output_path,
                    engine='pyarrow',
                    compression=self.compression,
                    index=self.preserve_index,
                    partition_cols=self.partition_cols,
                    row_group_size=self.row_group_size
                )

            # 计算压缩比
            parquet_size = os.path.getsize(output_path)
            compression_ratio = parquet_size / file_size if file_size > 0 else 1.0

            # 读取 Parquet 架构
            parquet_schema = {}
            try:
                # 使用 pyarrow 读取 Parquet 文件以获取架构
                import pyarrow.parquet as pq
                parquet_file = pq.ParquetFile(output_path)
                schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
                parquet_schema = schema_dict
            except Exception as e:
                logger.warning(f"读取 Parquet 架构失败: {e}")
                # 使用 pandas 数据类型作为备用
                parquet_schema = {col: str(dtype) for col, dtype in dtypes.items()}

            # 创建 ParquetFile 对象
            parquet_file = ParquetFile(
                original_file=data_file,
                filename=output_filename,
                path=output_path,
                size=parquet_size,
                schema=parquet_schema,
                rows=row_count,
                compression_ratio=compression_ratio,
                partition_cols=self.partition_cols,
                conversion_status=ConversionStatus.COMPLETED
            )

            # 更新数据文件列信息
            if data_file.columns is None:
                data_file.columns = columns

            elapsed_time = time.time() - start_time
            logger.info(
                f"CSV 转换完成: {data_file.filename} -> {output_filename} "
                f"({parquet_size / 1024 / 1024:.2f} MB, "
                f"压缩比: {compression_ratio:.2f}, "
                f"耗时: {elapsed_time:.2f}s)"
            )

            return parquet_file

        except Exception as e:
            logger.error(f"CSV 转换失败: {data_file.filename}, 错误: {e}")
            raise ConversionError(f"CSV 转换失败: {e}", file=data_file.filename)

    def _convert_json(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """
        将 JSON 文件转换为 Parquet 格式。

        参数:
            data_file: 数据文件对象
            output_dir: 输出目录

        返回:
            ParquetFile 对象

        抛出:
            ConversionError: 当转换过程中发生错误时
        """
        start_time = time.time()
        logger.info(f"转换 JSON 文件: {data_file.filename}")

        # 检查文件是否存在
        if not os.path.exists(data_file.path):
            raise ConversionError(f"文件不存在: {data_file.path}", file=data_file.filename)

        # 构建输出文件路径
        output_filename = os.path.splitext(os.path.basename(data_file.filename))[0] + ".parquet"
        output_path = os.path.join(output_dir, output_filename)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.join(output_dir, output_filename)), exist_ok=True)

        # 检查文件大小
        file_size = os.path.getsize(data_file.path)

        try:
            # 检查是否为 JSON Lines 格式
            is_json_lines = self._is_json_lines_format(data_file.path)
            logger.debug(f"检测为 {'JSON Lines' if is_json_lines else 'JSON'} 格式")

            if is_json_lines:
                # 处理 JSON Lines 格式 (每行一个独立的 JSON 对象)
                df = pd.read_json(data_file.path, lines=True, orient='records')
            else:
                # 处理常规 JSON 格式
                # 首先尝试使用 pandas 读取，处理多种可能的 JSON 格式
                try:
                    # 尝试读取为数据记录列表
                    df = pd.read_json(data_file.path, orient='records')
                except Exception as e1:
                    try:
                        # 尝试读取为表格格式 (列作为 key)
                        df = pd.read_json(data_file.path)
                    except Exception as e2:
                        try:
                            # 尝试读取嵌套的 JSON
                            import json
                            with open(data_file.path, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            # 处理嵌套结构，尝试平面化为 DataFrame
                            if isinstance(data, dict):
                                if any(isinstance(v, list) for v in data.values()):
                                    # 如果值中有列表，可能是 {column1: [value1, value2], column2: [value1, value2]} 格式
                                    df = pd.DataFrame(data)
                                else:
                                    # 单个字典，转为单行 DataFrame
                                    df = pd.DataFrame([data])
                            elif isinstance(data, list):
                                if all(isinstance(item, dict) for item in data):
                                    # 字典列表，转为 DataFrame
                                    df = pd.DataFrame(data)
                                else:
                                    # 简单列表，转为单列 DataFrame
                                    df = pd.DataFrame(data, columns=['value'])
                            else:
                                raise ValueError(f"无法解析 JSON 格式: {type(data)}")
                        except Exception as e3:
                            # 所有尝试都失败，抛出异常
                            logger.error(f"JSON 解析失败: {e1}, {e2}, {e3}")
                            raise ConversionError(f"无法解析 JSON 格式: {e1}", file=data_file.filename)

            # 存储列信息
            columns = list(df.columns)
            dtypes = df.dtypes.to_dict()
            row_count = len(df)

            # 转换为 Parquet
            df.to_parquet(
                output_path,
                engine='pyarrow',
                compression=self.compression,
                index=self.preserve_index,
                row_group_size=self.row_group_size,
                partition_cols=self.partition_cols
            )

            # 计算压缩比
            parquet_size = os.path.getsize(output_path)
            compression_ratio = parquet_size / file_size if file_size > 0 else 1.0

            # 读取 Parquet 架构
            parquet_schema = {}
            try:
                # 使用 pyarrow 读取 Parquet 文件以获取架构
                import pyarrow.parquet as pq
                parquet_file = pq.ParquetFile(output_path)
                schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
                parquet_schema = schema_dict
            except Exception as e:
                logger.warning(f"读取 Parquet 架构失败: {e}")
                # 使用 pandas 数据类型作为备用
                parquet_schema = {col: str(dtype) for col, dtype in dtypes.items()}

            # 创建 ParquetFile 对象
            parquet_file = ParquetFile(
                original_file=data_file,
                filename=output_filename,
                path=output_path,
                size=parquet_size,
                schema=parquet_schema,
                rows=row_count,
                compression_ratio=compression_ratio,
                partition_cols=self.partition_cols,
                conversion_status=ConversionStatus.COMPLETED
            )

            # 更新数据文件列信息
            if data_file.columns is None:
                data_file.columns = columns

            elapsed_time = time.time() - start_time
            logger.info(
                f"JSON 转换完成: {data_file.filename} -> {output_filename} "
                f"({parquet_size / 1024 / 1024:.2f} MB, "
                f"压缩比: {compression_ratio:.2f}, "
                f"耗时: {elapsed_time:.2f}s)"
            )

            return parquet_file

        except Exception as e:
            logger.error(f"JSON 转换失败: {data_file.filename}, 错误: {e}")
            raise ConversionError(f"JSON 转换失败: {e}", file=data_file.filename)

    def _is_json_lines_format(self, file_path: str, sample_size: int = 3) -> bool:
        """
        判断文件是否为 JSON Lines 格式（每行一个 JSON 对象）。

        参数:
            file_path: 文件路径
            sample_size: 采样的行数

        返回:
            如果是 JSON Lines 格式返回 True，否则返回 False
        """
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取前几行
                lines = [line.strip() for line in f.readlines()[:sample_size] if line.strip()]

                if not lines:
                    return False

                # 尝试解析每行为 JSON
                for line in lines:
                    try:
                        obj = json.loads(line)
                        if not isinstance(obj, (dict, list)):
                            return False
                    except json.JSONDecodeError:
                        return False

                return True
        except Exception as e:
            logger.warning(f"判断 JSON Lines 格式失败: {e}")
            return False

    def _convert_excel(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """
        将 Excel 文件转换为 Parquet 格式。

        参数:
            data_file: 数据文件对象
            output_dir: 输出目录

        返回:
            ParquetFile 对象

        抛出:
            ConversionError: 当转换过程中发生错误时
        """
        start_time = time.time()
        logger.info(f"转换 Excel 文件: {data_file.filename}")

        # 检查文件是否存在
        if not os.path.exists(data_file.path):
            raise ConversionError(f"文件不存在: {data_file.path}", file=data_file.filename)

        # 构建输出文件路径基础名称（不包含扩展名）
        output_base = os.path.splitext(os.path.basename(data_file.filename))[0]

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 检查文件大小
        file_size = os.path.getsize(data_file.path)

        try:
            # 使用 pandas 读取 Excel 文件
            # 首先获取所有工作表名称
            import pandas as pd
            xl = pd.ExcelFile(data_file.path)
            sheet_names = xl.sheet_names

            logger.debug(f"Excel 文件包含 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")

            # 如果只有一个工作表，直接转换为单个 Parquet 文件
            if len(sheet_names) == 1:
                sheet_name = sheet_names[0]
                output_filename = f"{output_base}.parquet"
                output_path = os.path.join(output_dir, output_filename)

                # 读取工作表
                df = pd.read_excel(data_file.path, sheet_name=sheet_name)
                columns = list(df.columns)
                dtypes = df.dtypes.to_dict()
                row_count = len(df)

                # 转换为 Parquet
                df.to_parquet(
                    output_path,
                    engine='pyarrow',
                    compression=self.compression,
                    index=self.preserve_index,
                    row_group_size=self.row_group_size,
                    partition_cols=self.partition_cols
                )

                # 计算压缩比
                parquet_size = os.path.getsize(output_path)
                compression_ratio = parquet_size / file_size if file_size > 0 else 1.0

                # 读取 Parquet 架构
                parquet_schema = {}
                try:
                    import pyarrow.parquet as pq
                    parquet_file = pq.ParquetFile(output_path)
                    schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
                    parquet_schema = schema_dict
                except Exception as e:
                    logger.warning(f"读取 Parquet 架构失败: {e}")
                    parquet_schema = {col: str(dtype) for col, dtype in dtypes.items()}

                # 创建 ParquetFile 对象
                parquet_file = ParquetFile(
                    original_file=data_file,
                    filename=output_filename,
                    path=output_path,
                    size=parquet_size,
                    schema=parquet_schema,
                    rows=row_count,
                    compression_ratio=compression_ratio,
                    partition_cols=self.partition_cols,
                    conversion_status=ConversionStatus.COMPLETED
                )

                # 更新数据文件列信息
                if data_file.columns is None:
                    data_file.columns = columns

                elapsed_time = time.time() - start_time
                logger.info(
                    f"Excel 转换完成: {data_file.filename} (工作表: {sheet_name}) -> {output_filename} "
                    f"({parquet_size / 1024 / 1024:.2f} MB, "
                    f"压缩比: {compression_ratio:.2f}, "
                    f"耗时: {elapsed_time:.2f}s)"
                )

                return parquet_file

            else:
                # 多个工作表，为每个工作表创建单独的 Parquet 文件
                # 但仅返回第一个工作表的 ParquetFile 对象作为代表
                sheets_info = []
                first_parquet_file = None

                # 创建一个目录存储多个工作表
                sheets_dir = os.path.join(output_dir, output_base)
                os.makedirs(sheets_dir, exist_ok=True)

                for sheet_name in sheet_names:
                    # 安全的文件名
                    safe_sheet_name = "".join([c if c.isalnum() else "_" for c in sheet_name])
                    output_filename = f"{safe_sheet_name}.parquet"
                    output_path = os.path.join(sheets_dir, output_filename)

                    # 读取工作表
                    df = pd.read_excel(data_file.path, sheet_name=sheet_name)
                    columns = list(df.columns)
                    dtypes = df.dtypes.to_dict()
                    row_count = len(df)

                    # 转换为 Parquet
                    df.to_parquet(
                        output_path,
                        engine='pyarrow',
                        compression=self.compression,
                        index=self.preserve_index,
                        row_group_size=self.row_group_size,
                        partition_cols=self.partition_cols
                    )

                    # 计算此工作表的压缩比（近似值，因为我们不知道每个工作表在原始文件中的确切大小）
                    parquet_size = os.path.getsize(output_path)

                    # 读取 Parquet 架构
                    parquet_schema = {}
                    try:
                        import pyarrow.parquet as pq
                        parquet_file = pq.ParquetFile(output_path)
                        schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
                        parquet_schema = schema_dict
                    except Exception as e:
                        logger.warning(f"读取工作表 {sheet_name} 的 Parquet 架构失败: {e}")
                        parquet_schema = {col: str(dtype) for col, dtype in dtypes.items()}

                    # 创建每个工作表的 ParquetFile 对象
                    sheet_parquet = ParquetFile(
                        original_file=data_file,
                        filename=output_filename,
                        path=output_path,
                        size=parquet_size,
                        schema=parquet_schema,
                        rows=row_count,
                        partition_cols=self.partition_cols,
                        conversion_status=ConversionStatus.COMPLETED
                    )

                    sheets_info.append({
                        "sheet_name": sheet_name,
                        "filename": output_filename,
                        "path": output_path,
                        "size": parquet_size,
                        "rows": row_count
                    })

                    # 保存第一个工作表的 ParquetFile 作为返回值
                    if first_parquet_file is None:
                        first_parquet_file = sheet_parquet

                # 计算总大小
                total_parquet_size = sum(sheet["size"] for sheet in sheets_info)
                compression_ratio = total_parquet_size / file_size if file_size > 0 else 1.0

                elapsed_time = time.time() - start_time
                logger.info(
                    f"Excel 转换完成: {data_file.filename} ({len(sheets_info)} 个工作表) -> {sheets_dir} "
                    f"(总计: {total_parquet_size / 1024 / 1024:.2f} MB, "
                    f"压缩比: {compression_ratio:.2f}, "
                    f"耗时: {elapsed_time:.2f}s)"
                )

                # 详细记录每个工作表信息
                for sheet in sheets_info:
                    logger.debug(
                        f"  - 工作表: {sheet['sheet_name']}, "
                        f"文件: {sheet['filename']}, "
                        f"大小: {sheet['size'] / 1024 / 1024:.2f} MB, "
                        f"行数: {sheet['rows']}"
                    )

                # 更新第一个 ParquetFile 对象的元数据以包含所有工作表信息
                if first_parquet_file:
                    # 添加工作表信息到元数据
                    first_parquet_file.metadata = {
                        "excel_sheets": sheets_info,
                        "total_parquet_size": total_parquet_size,
                        "compression_ratio": compression_ratio
                    }

                return first_parquet_file

        except Exception as e:
            logger.error(f"Excel 转换失败: {data_file.filename}, 错误: {e}")
            raise ConversionError(f"Excel 转换失败: {e}", file=data_file.filename)

    def _convert_tsv(self, data_file: DataFile, output_dir: str) -> ParquetFile:
        """
        将 TSV 文件转换为 Parquet 格式。

        TSV 格式是 CSV 的变体，使用制表符而非逗号作为分隔符。
        本方法使用与 CSV 转换相同的逻辑，但指定制表符为分隔符。

        参数:
            data_file: 数据文件对象
            output_dir: 输出目录

        返回:
            ParquetFile 对象

        抛出:
            ConversionError: 当转换过程中发生错误时
        """
        start_time = time.time()
        logger.info(f"转换 TSV 文件: {data_file.filename}")

        # 检查文件是否存在
        if not os.path.exists(data_file.path):
            raise ConversionError(f"文件不存在: {data_file.path}", file=data_file.filename)

        # 构建输出文件路径
        output_filename = os.path.splitext(os.path.basename(data_file.filename))[0] + ".parquet"
        output_path = os.path.join(output_dir, output_filename)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.join(output_dir, output_filename)), exist_ok=True)

        # 检查文件大小，决定是否使用分块读取
        file_size = os.path.getsize(data_file.path)
        use_chunks = file_size > 100 * 1024 * 1024  # 超过 100MB 使用分块读取

        try:
            if use_chunks:
                # 使用分块读取大文件，指定制表符为分隔符
                logger.debug(f"文件较大 ({file_size / 1024 / 1024:.2f} MB)，使用分块读取")

                # 首先读取少量样本以推断数据类型和列名
                sample_df = pd.read_csv(
                    data_file.path,
                    sep='\t',  # 制表符分隔
                    nrows=1000,
                    low_memory=False
                )

                # 存储列信息
                columns = list(sample_df.columns)
                dtypes = sample_df.dtypes.to_dict()

                # 创建 Parquet 写入器
                schema = None  # 自动推断

                # 分块读取并写入
                chunks = pd.read_csv(
                    data_file.path,
                    sep='\t',  # 制表符分隔
                    chunksize=self.chunk_size,
                    low_memory=False
                )

                # 第一个块写入（包括元数据）
                for i, chunk in enumerate(tqdm(chunks, desc="处理数据块")):
                    if i == 0:
                        # 第一个块，写入模式为 'w'
                        chunk.to_parquet(
                            output_path,
                            engine='pyarrow',
                            compression=self.compression,
                            index=self.preserve_index,
                            partition_cols=self.partition_cols,
                            row_group_size=self.row_group_size
                        )
                    else:
                        # 后续块，写入模式为 'a'
                        chunk.to_parquet(
                            output_path,
                            engine='pyarrow',
                            compression=self.compression,
                            index=self.preserve_index,
                            partition_cols=self.partition_cols,
                            row_group_size=self.row_group_size,
                            append=True
                        )

                # 计算行数
                row_count = sum(len(chunk) for chunk in pd.read_csv(
                    data_file.path,
                    sep='\t',
                    chunksize=self.chunk_size,
                    low_memory=False
                ))
            else:
                # 直接读取小文件
                logger.debug(f"文件较小 ({file_size / 1024 / 1024:.2f} MB)，直接读取")
                df = pd.read_csv(data_file.path, sep='\t', low_memory=False)

                # 存储列信息
                columns = list(df.columns)
                dtypes = df.dtypes.to_dict()
                row_count = len(df)

                # 转换为 Parquet
                df.to_parquet(
                    output_path,
                    engine='pyarrow',
                    compression=self.compression,
                    index=self.preserve_index,
                    partition_cols=self.partition_cols,
                    row_group_size=self.row_group_size
                )

            # 计算压缩比
            parquet_size = os.path.getsize(output_path)
            compression_ratio = parquet_size / file_size if file_size > 0 else 1.0

            # 读取 Parquet 架构
            parquet_schema = {}
            try:
                # 使用 pyarrow 读取 Parquet 文件以获取架构
                import pyarrow.parquet as pq
                parquet_file = pq.ParquetFile(output_path)
                schema_dict = {field.name: str(field.type) for field in parquet_file.schema.to_arrow_schema()}
                parquet_schema = schema_dict
            except Exception as e:
                logger.warning(f"读取 Parquet 架构失败: {e}")
                # 使用 pandas 数据类型作为备用
                parquet_schema = {col: str(dtype) for col, dtype in dtypes.items()}

            # 创建 ParquetFile 对象
            parquet_file = ParquetFile(
                original_file=data_file,
                filename=output_filename,
                path=output_path,
                size=parquet_size,
                schema=parquet_schema,
                rows=row_count,
                compression_ratio=compression_ratio,
                partition_cols=self.partition_cols,
                conversion_status=ConversionStatus.COMPLETED
            )

            # 更新数据文件列信息
            if data_file.columns is None:
                data_file.columns = columns

            elapsed_time = time.time() - start_time
            logger.info(
                f"TSV 转换完成: {data_file.filename} -> {output_filename} "
                f"({parquet_size / 1024 / 1024:.2f} MB, "
                f"压缩比: {compression_ratio:.2f}, "
                f"耗时: {elapsed_time:.2f}s)"
            )

            return parquet_file

        except Exception as e:
            logger.error(f"TSV 转换失败: {data_file.filename}, 错误: {e}")
            raise ConversionError(f"TSV 转换失败: {e}", file=data_file.filename)

    def convert_dataset(
        self,
        files: List[DataFile],
        output_dir: str,
        force: bool = False
    ) -> List[ParquetFile]:
        """
        批量转换数据文件为 Parquet 格式。

        参数:
            files: 数据文件列表
            output_dir: 输出目录
            force: 是否覆盖已存在的 Parquet 文件

        返回:
            ParquetFile 对象列表
        """
        logger.info(f"批量转换 {len(files)} 个文件")

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 筛选支持的文件格式
        supported_files = []
        unsupported_files = []
        already_converted_files = []

        for file in files:
            # 检查是否支持该格式
            if not self.is_supported_format(file.format):
                unsupported_files.append(file)
                continue

            # 如果不强制覆盖，检查是否已经存在对应的 Parquet 文件
            if not force:
                output_filename = os.path.splitext(os.path.basename(file.filename))[0] + ".parquet"
                output_path = os.path.join(output_dir, output_filename)

                if os.path.exists(output_path):
                    already_converted_files.append(file)
                    logger.debug(f"跳过已存在的 Parquet 文件: {output_path}")
                    continue

            # 添加到待转换列表
            supported_files.append(file)

        if unsupported_files:
            logger.warning(f"跳过 {len(unsupported_files)} 个不支持的文件")
            for file in unsupported_files:
                logger.debug(f"  - 不支持的文件: {file.filename} (格式: {file.format.value})")

        if already_converted_files and not force:
            logger.warning(f"跳过 {len(already_converted_files)} 个已转换的文件 (使用 force=True 覆盖)")

        # 检查是否有文件需要转换
        if not supported_files:
            logger.warning("没有需要转换的文件")
            return []

        # 单个文件或文件较少时，使用单进程转换
        if len(supported_files) == 1 or self.processes <= 1:
            logger.debug("使用单进程转换")
            result = []
            for file in tqdm(supported_files, desc="转换文件"):
                try:
                    parquet_file = self.convert_file(file, output_dir)
                    result.append(parquet_file)
                except (UnsupportedFormatError, ConversionError) as e:
                    logger.error(f"转换失败: {e}")
            return result

        # 文件较多时，使用多进程转换
        logger.debug(f"使用多进程转换，进程数: {self.processes}")
        return self.multi_process_convert(supported_files, output_dir, self.processes)

    def multi_process_convert(
        self,
        files: List[DataFile],
        output_dir: str,
        processes: Optional[int] = None
    ) -> List[ParquetFile]:
        """
        使用多进程并行转换文件。

        参数:
            files: 数据文件列表
            output_dir: 输出目录
            processes: 进程数量，默认使用配置的值

        返回:
            ParquetFile 对象列表
        """
        if processes is None:
            processes = self.processes

        # 确保进程数量合理
        processes = max(1, min(processes, len(files), mp.cpu_count()))

        logger.info(f"使用 {processes} 个进程并行转换 {len(files)} 个文件")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 筛选支持的文件
        supported_files = [f for f in files if self.is_supported_format(f.format)]

        if not supported_files:
            logger.warning("没有需要转换的文件")
            return []

        if len(supported_files) == 1 or processes <= 1:
            # 单个文件或只有一个进程，使用单进程转换
            logger.debug("使用单进程转换")
            result = []
            for file in tqdm(supported_files, desc="转换文件"):
                try:
                    parquet_file = self.convert_file(file, output_dir)
                    result.append(parquet_file)
                except (UnsupportedFormatError, ConversionError) as e:
                    logger.error(f"转换失败: {e}")
            return result

        # 准备进程池
        start_time = time.time()
        logger.debug(f"启动 {processes} 个转换 processes")

        # 准备转换任务
        tasks = []
        for file in supported_files:
            # 将 DataFile 对象转换为可序列化字典
            file_dict = {
                'filename': file.filename,
                'format': file.format.value,
                'size': file.size,
                'path': file.path,
                'columns': file.columns,
                'schema': file.schema,
                'download_status': file.download_status.value,
                'download_progress': file.download_progress,
                'checksum': file.checksum
            }
            tasks.append(file_dict)

        # 使用进程池执行转换任务
        results = []
        try:
            with ProcessPoolExecutor(max_workers=processes) as executor:
                # 提交所有任务
                future_to_file = {
                    executor.submit(
                        _convert_worker,
                        task,
                        output_dir,
                        self.compression,
                        self.chunk_size,
                        self.row_group_size,
                        self.preserve_index,
                        self.partition_cols
                    ): task['filename']
                    for task in tasks
                }

                # 收集结果
                for future in tqdm(
                    future_to_file.keys(),
                    desc=f"转换文件 (使用 {processes} 个进程)",
                    total=len(tasks)
                ):
                    filename = future_to_file[future]
                    try:
                        result = future.result()
                        if result['success']:
                            logger.debug(f"文件 {filename} 转换成功")
                            results.append(result)
                        else:
                            logger.error(f"文件 {filename} 转换失败: {result['error']}")
                    except Exception as e:
                        logger.error(f"获取文件 {filename} 的转换结果时出错: {e}")

        except Exception as e:
            logger.error(f"多进程转换时发生错误: {e}")

        # 重建 ParquetFile 对象
        parquet_files = []
        for result in results:
            try:
                # 重建原始 DataFile
                original_file = DataFile(
                    filename=result['original_file']['filename'],
                    format=FileFormat(result['original_file']['format']),
                    size=result['original_file']['size'],
                    path=result['original_file']['path'],
                    columns=result['original_file']['columns'],
                    schema=result['original_file']['schema'],
                    download_status=DownloadStatus(result['original_file']['download_status']),
                    download_progress=result['original_file']['download_progress'],
                    checksum=result['original_file'].get('checksum')
                )

                # 重建 ParquetFile
                parquet_file = ParquetFile(
                    original_file=original_file,
                    filename=result['filename'],
                    path=result['path'],
                    size=result['size'],
                    schema=result['schema'],
                    rows=result['rows'],
                    compression_ratio=result['compression_ratio'],
                    partition_cols=result['partition_cols'],
                    conversion_status=ConversionStatus(result['conversion_status']),
                    timestamp=datetime.fromisoformat(result['timestamp'])
                )

                # 添加元数据
                if 'metadata' in result and result['metadata']:
                    parquet_file.metadata = result['metadata']

                parquet_files.append(parquet_file)

            except Exception as e:
                logger.error(f"重建 ParquetFile 对象失败: {e}")

        elapsed_time = time.time() - start_time
        logger.info(
            f"多进程转换完成: {len(parquet_files)}/{len(supported_files)} 个文件成功, "
            f"耗时: {elapsed_time:.2f}s, "
            f"平均每个文件: {elapsed_time / len(supported_files):.2f}s"
        )

        return parquet_files