#!/bin/bash

# 获取当前脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 引入 check_env.sh 中的变量和函数
# 这将导入: 颜色定义, PROJECT_ROOT, check_uv, check_venv, check_environment_availability
source "$SCRIPT_DIR/check_env.sh"

echo -e "${BLUE}=== 项目环境初始化 ===${NC}"

# 1. 确保 uv 已安装
echo -e "\n${BLUE}[1/3] 检查构建工具 (uv)...${NC}"

# 尝试检查 uv，如果失败则安装
if ! check_uv; then
    echo -e "${YELLOW}正在安装 uv...${NC}"
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo -e "${GREEN}uv 安装成功${NC}"
        # 尝试加载 cargo 环境以立即使用 uv
        [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

        # 再次检查
        if ! command -v uv &> /dev/null; then
             export PATH="$HOME/.cargo/bin:$PATH"
        fi

        # 验证安装结果
        if command -v uv &> /dev/null; then
             echo -e "${GREEN}uv 已就绪: $(uv --version)${NC}"
        else
             echo -e "${RED}uv 安装后仍无法找到命令，请尝试重新打开终端或手动安装${NC}"
             exit 1
        fi
    else
        echo -e "${RED}uv 安装失败，请手动安装${NC}"
        exit 1
    fi
fi

# 2. 配置文件初始化
echo -e "\n${BLUE}[2/3] 检查配置文件...${NC}"
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}已根据 .env.example 创建 .env 文件${NC}"
        echo -e "${YELLOW}提示: 请记得检查并修改 .env 文件中的配置${NC}"
    else
        echo -e "${YELLOW}未找到 .env.example，生成默认 .env 文件${NC}"
        {
            echo "JUPYTER_HOST=127.0.0.1"
            echo "JUPYTER_PORT=8887"
            echo "JUPYTER_TOKEN=$(openssl rand -hex 16)"
        } > "$PROJECT_ROOT/.env"
    fi
else
    echo -e "${GREEN}.env 配置文件已存在${NC}"
fi

# 3. 依赖安装
echo -e "\n${BLUE}[3/3] 安装/同步依赖...${NC}"
echo -e "${YELLOW}正在同步所有依赖组 (dev, test, llm)...${NC}"

# 切换到项目根目录执行 uv sync
cd "$PROJECT_ROOT" || exit 1

if uv sync --all-groups; then
    echo -e "${GREEN}依赖安装完成${NC}"
else
    echo -e "${RED}依赖安装失败${NC}"
    exit 1
fi

echo -e "\n${BLUE}=== 运行最终环境检查 ===${NC}"
# 调用 check_env.sh 中的主逻辑（通过调用 check_environment_availability 等函数，或者直接调用 main 如果被 export 的话，但这里直接调用函数更灵活）

if check_venv && check_environment_availability; then
    echo -e "\n${GREEN}✨ 项目初始化成功！${NC}"
    echo -e "启动 Jupyter Lab: ${YELLOW}./scripts/start_jupyter.sh${NC}"
else
    echo -e "\n${RED}❌ 初始化看似完成，但最终检查失败。请查看上方错误信息。${NC}"
    exit 1
fi
