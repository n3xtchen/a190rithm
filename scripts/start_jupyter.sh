#!/bin/bash

# 获取脚本所在目录的上一级目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# 运行环境检查
"$PROJECT_ROOT/scripts/check_env.sh"
if [ $? -ne 0 ]; then
    echo "❌ 环境检查失败，停止启动。"
    exit 1
fi

# 加载 .env 文件
if [ -f "$ENV_FILE" ]; then
  # 使用 grep 和 xargs 导出非注释行
  export $(grep -v '^#' "$ENV_FILE" | xargs)
  echo "✅ 已加载 .env 配置"
else
  echo "⚠️  未找到 .env 文件，使用默认设置"
fi

# 设置变量，提供默认值
HOST="${JUPYTER_HOST:-127.0.0.1}"
PORT="${JUPYTER_PORT:-8887}"
TOKEN="${JUPYTER_TOKEN:-my_token_here}"

# 检查端口占用函数
check_port() {
  local port=$1
  # lsof -i :port 检查端口
  # -t 仅输出 PID
  # -s tcp:LISTEN 仅检查监听状态
  local pid=$(lsof -ti tcp:$port -s tcp:LISTEN)

  if [ -n "$pid" ]; then
    echo "❌ 错误: 端口 $port 已被占用 (PID: $pid)"
    # 显示详细进程信息
    lsof -i tcp:$port -s tcp:LISTEN | tail -n +2 | awk '{print "   Process: " $1 " (PID: " $2 ") User: " $3}'
    return 1
  else
    return 0
  fi
}

# 执行端口检查
if ! check_port "$PORT"; then
  echo ""
  echo "建议操作："
  echo "1. 停止占用端口的进程: kill -9 \$(lsof -ti tcp:$PORT)"
  echo "2. 或者修改 .env 中的 JUPYTER_PORT"
  exit 1
fi

# 启动 Jupyter Lab
echo "🚀 正在启动 Jupyter Lab..."
echo "   地址: http://$HOST:$PORT"
echo "   Token: $TOKEN"

exec uv run --group llm jupyter lab \
  --ip "$HOST" \
  --port "$PORT" \
  --IdentityProvider.token "$TOKEN" \
  --JupyterMCPServerExtensionApp.allowed_jupyter_mcp_tools="notebook_run-all-cells,notebook_get-selected-cell,notebook_append-execute"
