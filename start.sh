#!/bin/bash

# AI旅行规划师 - 快速启动脚本
# 使用方式: ./start.sh [dev|prod|stop]

set -e

COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'

echo_info() {
    echo -e "${COLOR_BLUE}ℹ️  $1${COLOR_RESET}"
}

echo_success() {
    echo -e "${COLOR_GREEN}✅ $1${COLOR_RESET}"
}

echo_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $1${COLOR_RESET}"
}

echo_error() {
    echo -e "${COLOR_RED}❌ $1${COLOR_RESET}"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║      AI旅行规划师 - 快速启动脚本               ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
}

check_dependencies() {
    echo_info "检查依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    echo_success "所有依赖检查通过"
}

check_env_files() {
    echo_info "检查环境变量配置..."
    
    # 检查后端.env
    if [ ! -f "backend/.env" ]; then
        echo_warning "后端.env文件不存在，从模板创建..."
        cp backend/ENV_TEMPLATE.txt backend/.env
        echo_warning "请编辑 backend/.env 文件，填入必需的API密钥："
        echo "  - DEEPSEEK_API_KEY"
        echo "  - BAIDU_MAP_AK"
        echo ""
        read -p "按Enter继续..."
    fi
    
    # 检查前端.env
    if [ ! -f "frontend/.env" ]; then
        echo_warning "前端.env文件不存在，从模板创建..."
        cp frontend/ENV_TEMPLATE.txt frontend/.env
        echo_warning "请编辑 frontend/.env 文件，填入必需的API密钥："
        echo "  - VITE_BAIDU_MAPS_API_KEY"
        echo ""
        read -p "按Enter继续..."
    fi
    
    echo_success "环境变量配置检查完成"
}

start_dev() {
    print_header
    echo_info "启动开发环境..."
    echo ""
    
    check_dependencies
    check_env_files
    
    echo_info "启动数据库和Redis..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    echo_success "数据库和Redis已启动"
    echo ""
    echo_info "等待数据库就绪..."
    sleep 5
    
    echo ""
    echo_success "开发环境已启动！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 下一步操作："
    echo ""
    echo "  1️⃣  启动后端（新终端）："
    echo "     cd backend"
    echo "     pip install -r requirements.txt"
    echo "     alembic upgrade head"
    echo "     uvicorn app.main:app --reload --port 8000"
    echo ""
    echo "  2️⃣  启动前端（新终端）："
    echo "     cd frontend"
    echo "     npm install"
    echo "     npm run dev"
    echo ""
    echo "  3️⃣  访问应用："
    echo "     前端: http://localhost:5173"
    echo "     后端: http://localhost:8000/docs"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

start_prod() {
    print_header
    echo_info "启动生产环境..."
    echo ""
    
    check_dependencies
    check_env_files
    
    echo_info "构建并启动所有服务..."
    docker-compose up -d --build
    
    echo ""
    echo_success "生产环境已启动！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 访问应用："
    echo "   前端: http://localhost"
    echo "   后端: http://localhost:8000"
    echo "   API文档: http://localhost:8000/docs"
    echo ""
    echo "📊 查看日志："
    echo "   docker-compose logs -f"
    echo ""
    echo "⏹️  停止服务："
    echo "   docker-compose down"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

stop_services() {
    print_header
    echo_info "停止所有服务..."
    
    docker-compose down
    docker-compose -f docker-compose.dev.yml down
    
    echo_success "所有服务已停止"
}

show_status() {
    print_header
    echo_info "服务状态："
    echo ""
    
    echo "📦 Docker服务："
    docker-compose ps
    
    echo ""
    echo "📊 Docker容器："
    docker ps | grep travel-planner || echo "  没有运行中的容器"
}

show_help() {
    print_header
    echo "使用方式: ./start.sh [command]"
    echo ""
    echo "命令列表:"
    echo "  dev     - 启动开发环境（仅启动数据库，需手动启动前后端）"
    echo "  prod    - 启动生产环境（Docker全套服务）"
    echo "  stop    - 停止所有服务"
    echo "  status  - 查看服务状态"
    echo "  help    - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./start.sh dev    # 开发环境"
    echo "  ./start.sh prod   # 生产环境"
    echo "  ./start.sh stop   # 停止服务"
}

# 主逻辑
case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo_warning "未知命令: $1"
        show_help
        exit 1
        ;;
esac

