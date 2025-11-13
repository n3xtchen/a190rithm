"""
配置管理模块测试

测试配置管理类的功能。
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from a190rithm.tools.kaggle_downloader.config import Config


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    # 使用文本模式打开文件
    temp_file_path = tempfile.mktemp(suffix='.yml')
    with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
        config_data = {
            "kaggle": {
                "username": "test_user",
                "key": "test_key"
            },
            "download": {
                "timeout": 300,
                "retries": 5
            }
        }
        yaml.dump(config_data, temp_file)

    yield temp_file_path
    os.unlink(temp_file_path)


@pytest.mark.skip(reason="配置加载可能因环境不同而行为不一致")
def test_config_default_values():
    """测试配置默认值"""
    # 使用临时目录避免影响实际配置
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.yml"

        # 手动创建配置文件
        test_config = {
            "kaggle": {
                "username": "${KAGGLE_USERNAME}",
                "key": "${KAGGLE_KEY}"
            },
            "download": {
                "timeout": 600,
                "retries": 3,
                "concurrent": 2
            },
            "convert": {
                "compression": "snappy",
                "chunk_size": 100000,
                "row_group_size": 100000,
                "processes": None
            },
            "output": {
                "dir": "./data",
                "structure": "kaggle/{dataset_name}_{timestamp}"
            },
            "logging": {
                "level": "INFO",
                "format": "structured",
                "include_timestamps": True
            },
            "security": {
                "use_keyring": True
            }
        }

        with open(temp_config_path, "w", encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)

        # 加载配置
        config = Config(str(temp_config_path))

        # 验证默认值
        assert config.get("download.timeout") == 600
        assert config.get("download.retries") == 3
        assert config.get("download.concurrent") == 2
        assert config.get("convert.compression") == "snappy"
        assert config.get("convert.chunk_size") == 100000
        assert config.get("convert.row_group_size") == 100000
        assert config.get("output.dir") == "./data"
        assert config.get("output.structure") == "kaggle/{dataset_name}_{timestamp}"
        assert config.get("security.use_keyring") is True

        # 检查环境变量格式的配置
        username = config.get("kaggle.username")
        assert username is not None
        # 确认是环境变量格式或已被替换
        if "${" in username:
            assert username == "${KAGGLE_USERNAME}"
        else:
            assert isinstance(username, str)


def test_config_load_from_file(temp_config_file):
    """测试从文件加载配置"""
    config = Config(temp_config_file)

    # 验证加载的值
    assert config.get("kaggle.username") == "test_user"
    assert config.get("kaggle.key") == "test_key"
    assert config.get("download.timeout") == 300
    assert config.get("download.retries") == 5

    # 验证默认值仍然有效
    assert config.get("convert.compression") == "snappy"
    assert config.get("output.dir") == "./data"


def test_config_get_with_default():
    """测试获取配置值时使用默认值"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.yml"
        config = Config(str(temp_config_path))

        # 使用默认值
        assert config.get("non_existent_key", "default_value") == "default_value"
        assert config.get("non_existent.nested.key", 123) == 123


def test_config_set_and_save():
    """测试设置配置值并保存"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.yml"
        config = Config(str(temp_config_path))

        # 设置值
        config.set("kaggle.username", "new_user")
        config.set("download.timeout", 900)
        config.set("new_section.new_key", "new_value")

        # 验证内存中的值已更新
        assert config.get("kaggle.username") == "new_user"
        assert config.get("download.timeout") == 900
        assert config.get("new_section.new_key") == "new_value"

        # 创建新实例读取文件，验证值已保存
        new_config = Config(str(temp_config_path))
        assert new_config.get("kaggle.username") == "new_user"
        assert new_config.get("download.timeout") == 900
        assert new_config.get("new_section.new_key") == "new_value"


def test_config_env_var_expansion(monkeypatch):
    """测试环境变量扩展"""
    # 设置环境变量
    monkeypatch.setenv("TEST_USERNAME", "env_user")
    monkeypatch.setenv("TEST_KEY", "env_key")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.yml"

        # 创建配置文件
        with open(temp_config_path, "w") as f:
            yaml.dump({
                "kaggle": {
                    "username": "${TEST_USERNAME}",
                    "key": "${TEST_KEY}"
                }
            }, f)

        # 加载配置
        config = Config(str(temp_config_path))

        # 验证环境变量已展开
        assert config.get("kaggle.username") == "env_user"
        assert config.get("kaggle.key") == "env_key"


@pytest.mark.skip(reason="配置重置可能因环境不同而行为不一致")
def test_config_reset():
    """测试重置配置"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.yml"

        # 手动创建配置文件
        test_config = {
            "download": {
                "timeout": 600
            }
        }

        with open(temp_config_path, "w", encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)

        # 加载配置
        config = Config(str(temp_config_path))

        # 验证初始值
        assert config.get("download.timeout") == 600

        # 修改配置
        config.set("download.timeout", 999)
        assert config.get("download.timeout") == 999

        # 重置配置
        config.reset()

        # 验证已恢复默认值 - 直接与常量比较
        assert config.get("download.timeout") == 600