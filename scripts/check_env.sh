#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. 检查 uv 是否可用
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}[ERROR] 未找到 uv 命令${NC}"
        echo -e "${YELLOW}请先安装 uv 包管理器: https://github.com/astral-sh/uv${NC}"
        echo -e "${YELLOW}安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        return 1
    else
        echo -e "${GREEN}[SUCCESS] 发现 uv: $(which uv)${NC}"
        return 0
    fi
}

# 2. 检查虚拟环境
check_venv() {
    local venv_path="$PROJECT_ROOT/.venv"
    if [ ! -d "$venv_path" ]; then
        echo -e "${RED}[ERROR] 未检测到虚拟环境 (.venv)${NC}"
        echo -e "${YELLOW}请运行初始化脚本以配置开发环境: ./scripts/init.sh${NC}"
        return 1
    else
        echo -e "${GREEN}[SUCCESS] 发现虚拟环境: $venv_path${NC}"
        return 0
    fi
}

# 3. 检查环境可用性
check_environment_availability() {
    local venv_path="$PROJECT_ROOT/.venv"
    local python_bin="$venv_path/bin/python"

    if [ ! -x "$python_bin" ]; then
        echo -e "${RED}[ERROR] 虚拟环境中的 Python 解析器不可执行${NC}"
        return 1
    fi

    local py_ver
    py_ver=$("$python_bin" --version 2>&1)
    echo -e "${GREEN}[SUCCESS] 环境 Python 版本: $py_ver${NC}"

    # 检查能否导入项目包
    if "$python_bin" -c "import a190rithm" 2>/dev/null; then
        echo -e "${GREEN}[SUCCESS] 项目包 (a190rithm) 可正常导入${NC}"
        return 0
    else
        echo -e "${YELLOW}[WARNING] 项目包无法导入，建议运行 'uv sync' 修复${NC}"
        return 1
    fi
}

# 主函数
main() {
    echo -e "${BLUE}=== 环境检查器 ===${NC}"
    echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"

    local status=0

    check_uv || status=1

    # 只有当 uv 检查通过或失败不影响 venv 检查逻辑时才继续？
    # 这里我们继续检查，但如果 uv 都没有，后面的其实意义不大，不过 venv 检查独立于 uv 命令
    check_venv
    if [ $? -ne 0 ]; then
        status=1
        # 如果没有 venv，无法检查 availability
        echo ""
        echo -e "${RED}❌ 环境检查未通过${NC}"
        exit 1
    fi

    check_environment_availability || status=1

    echo ""
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✨ 环境检查通过！${NC}"
        exit 0
    else
        echo -e "${RED}❌ 环境检查未通过${NC}"
        exit 1
    fi
}

# 如果脚本是直接执行的，则运行 main
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
