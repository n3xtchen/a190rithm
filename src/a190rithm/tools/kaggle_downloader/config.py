"""
配置管理模块

提供配置管理功能，支持从文件和环境变量加载配置。
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """
    配置管理类，支持从文件和环境变量加载配置。

    属性:
        config_path: 配置文件路径
        config: 配置字典
    """

    DEFAULT_CONFIG = {
        "kaggle": {
            "username": "${KAGGLE_USERNAME}",
            "key": "${KAGGLE_KEY}",
        },
        "download": {
            "timeout": 600,
            "retries": 3,
            "concurrent": 2,
        },
        "convert": {
            "compression": "snappy",
            "chunk_size": 100000,
            "row_group_size": 100000,
            "processes": None,
        },
        "output": {
            "dir": "./data",
            "structure": "kaggle/{dataset_name}_{timestamp}",
        },
        "logging": {
            "level": "INFO",
            "file": "~/.kaggle-parquet/logs/kaggle-parquet.log",
            "rotation": "5MB",
            "max_files": 3,
            "format": "structured",
            "include_timestamps": True,
        },
        "security": {
            "use_keyring": True,
            "allow_insecure": False,
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器。

        参数:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """
        解析配置文件路径。

        参数:
            config_path: 配置文件路径，如果为 None 则使用默认路径

        返回:
            Path: 配置文件路径对象
        """
        if config_path:
            path = Path(os.path.expanduser(config_path))
        else:
            env_path = os.environ.get("KAGGLE_PARQUET_CONFIG_PATH")
            if env_path:
                path = Path(os.path.expanduser(env_path))
            else:
                path = Path(os.path.expanduser("~/.kaggle-parquet/config.yml"))

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def _load_config(self) -> Dict[str, Any]:
        """
        从文件加载配置，如果文件不存在则使用默认配置。

        返回:
            Dict[str, Any]: 配置字典
        """
        if not self.config_path.exists():
            return self._create_default_config()

        try:
            with open(self.config_path, "r", encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not config:
                    return self._create_default_config()

                # 将默认配置与加载的配置合并
                merged_config = self._deep_merge(dict(self.DEFAULT_CONFIG), config)
                return merged_config
        except Exception:
            return self._create_default_config()

    def _deep_merge(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典，用第二个字典的值覆盖第一个字典中的值。

        参数:
            default: 默认字典
            override: 覆盖字典

        返回:
            合并后的字典
        """
        result = dict(default)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _create_default_config(self) -> Dict[str, Any]:
        """
        创建默认配置并保存到文件。

        返回:
            Dict[str, Any]: 默认配置字典
        """
        # 创建一个深拷贝，确保不会修改类变量
        config = dict(self.DEFAULT_CONFIG)
        try:
            with open(self.config_path, "w", encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception:
            pass  # 忽略写入错误

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值。

        参数:
            key: 配置键，支持点号分隔的嵌套键（如 'kaggle.username'）
            default: 默认值，如果键不存在则返回此值

        返回:
            配置值或默认值
        """
        value = self._get_nested(self.config, key.split("."))
        if value is None:
            return default

        # 处理环境变量
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, default)

        return value

    def _get_nested(self, data: Dict, keys: list) -> Any:
        """
        获取嵌套字典中的值。

        参数:
            data: 字典
            keys: 键列表

        返回:
            找到的值或 None
        """
        if not keys or not data:
            return None

        if len(keys) == 1:
            return data.get(keys[0])

        # 尝试获取下一级
        sub_data = data.get(keys[0])
        if not isinstance(sub_data, dict):
            # 查看是否存在默认配置中
            default_key_path = keys.copy()
            current = self.DEFAULT_CONFIG
            for k in default_key_path[:-1]:
                if k not in current:
                    return None
                current = current.get(k, {})
            return current.get(default_key_path[-1])

        return self._get_nested(sub_data, keys[1:])

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值并保存到文件。

        参数:
            key: 配置键，支持点号分隔的嵌套键（如 'kaggle.username'）
            value: 配置值
        """
        keys = key.split(".")
        self._set_nested(self.config, keys, value)
        self.save()

    def _set_nested(self, data: Dict, keys: list, value: Any) -> None:
        """
        设置嵌套字典中的值。

        参数:
            data: 字典
            keys: 键列表
            value: 值
        """
        if not keys:
            return

        if len(keys) == 1:
            data[keys[0]] = value
            return

        if keys[0] not in data:
            data[keys[0]] = {}
        elif not isinstance(data[keys[0]], dict):
            data[keys[0]] = {}

        self._set_nested(data[keys[0]], keys[1:], value)

    def save(self) -> None:
        """保存配置到文件。"""
        try:
            with open(self.config_path, "w", encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            print(f"保存配置文件时出错: {e}")

    def reset(self) -> None:
        """重置为默认配置。"""
        # 清除当前配置，创建一个深拷贝的新配置
        self.config = self._create_default_config()
        # 确保重写文件
        with open(self.config_path, "w", encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False)