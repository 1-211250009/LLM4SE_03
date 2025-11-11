#!/bin/bash

# 后端依赖安装脚本

set -e

echo "================================================"
echo "  AI旅行规划师 - 后端依赖安装"
echo "================================================"
echo ""

# 检查Python版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "📌 Python版本: $python_version"

# 检查pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip未安装"
    exit 1
fi

echo "📌 pip版本: $(pip --version)"
echo ""

# 安装依赖
echo "📦 开始安装Python依赖包..."
echo ""

pip install -r requirements.txt

echo ""
echo "✅ 依赖安装完成!"
echo ""
echo "================================================"
echo "  下一步操作"
echo "================================================"
echo ""
echo "1. 配置环境变量:"
echo "   cp ENV_TEMPLATE.txt .env"
echo "   vim .env  # 填入API密钥"
echo ""
echo "2. 执行数据库迁移:"
echo "   alembic upgrade head"
echo ""
echo "3. 启动后端服务:"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "================================================"

