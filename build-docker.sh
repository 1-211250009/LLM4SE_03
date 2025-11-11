#!/bin/bash

# Docker 镜像构建和推送脚本
# 使用方法: ./build-docker.sh [build|push|all] [backend|frontend|all]

set -e

# 配置
REGISTRY="registry.cn-hangzhou.aliyuncs.com"
NAMESPACE="${DOCKER_NAMESPACE:-your-namespace}"
BACKEND_IMAGE="llm4se03-backend"
FRONTEND_IMAGE="llm4se03-frontend"
VERSION="${VERSION:-latest}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 构建后端镜像
build_backend() {
    info "构建后端镜像..."
    cd backend
    docker build -t ${REGISTRY}/${NAMESPACE}/${BACKEND_IMAGE}:${VERSION} \
        -t ${REGISTRY}/${NAMESPACE}/${BACKEND_IMAGE}:latest \
        .
    cd ..
    info "后端镜像构建完成"
}

# 构建前端镜像
build_frontend() {
    info "构建前端镜像..."
    cd frontend
    docker build -t ${REGISTRY}/${NAMESPACE}/${FRONTEND_IMAGE}:${VERSION} \
        -t ${REGISTRY}/${NAMESPACE}/${FRONTEND_IMAGE}:latest \
        .
    cd ..
    info "前端镜像构建完成"
}

# 推送后端镜像
push_backend() {
    info "推送后端镜像..."
    docker push ${REGISTRY}/${NAMESPACE}/${BACKEND_IMAGE}:${VERSION}
    docker push ${REGISTRY}/${NAMESPACE}/${BACKEND_IMAGE}:latest
    info "后端镜像推送完成"
}

# 推送前端镜像
push_frontend() {
    info "推送前端镜像..."
    docker push ${REGISTRY}/${NAMESPACE}/${FRONTEND_IMAGE}:${VERSION}
    docker push ${REGISTRY}/${NAMESPACE}/${FRONTEND_IMAGE}:latest
    info "前端镜像推送完成"
}

# 登录到阿里云容器镜像仓库
login() {
    if [ -z "$ALIYUN_DOCKER_USERNAME" ] || [ -z "$ALIYUN_DOCKER_PASSWORD" ]; then
        error "请设置环境变量 ALIYUN_DOCKER_USERNAME 和 ALIYUN_DOCKER_PASSWORD"
        exit 1
    fi
    
    info "登录到阿里云容器镜像仓库..."
    echo "$ALIYUN_DOCKER_PASSWORD" | docker login ${REGISTRY} -u "$ALIYUN_DOCKER_USERNAME" --password-stdin
    info "登录成功"
}

# 主函数
main() {
    ACTION=${1:-all}
    TARGET=${2:-all}
    
    info "开始执行 Docker 操作..."
    info "操作: ${ACTION}, 目标: ${TARGET}"
    info "镜像仓库: ${REGISTRY}/${NAMESPACE}"
    info "版本: ${VERSION}"
    
    if [ "$ACTION" = "push" ] || [ "$ACTION" = "all" ]; then
        login
    fi
    
    case $TARGET in
        backend)
            if [ "$ACTION" = "build" ] || [ "$ACTION" = "all" ]; then
                build_backend
            fi
            if [ "$ACTION" = "push" ] || [ "$ACTION" = "all" ]; then
                push_backend
            fi
            ;;
        frontend)
            if [ "$ACTION" = "build" ] || [ "$ACTION" = "all" ]; then
                build_frontend
            fi
            if [ "$ACTION" = "push" ] || [ "$ACTION" = "all" ]; then
                push_frontend
            fi
            ;;
        all)
            if [ "$ACTION" = "build" ] || [ "$ACTION" = "all" ]; then
                build_backend
                build_frontend
            fi
            if [ "$ACTION" = "push" ] || [ "$ACTION" = "all" ]; then
                push_backend
                push_frontend
            fi
            ;;
        *)
            error "无效的目标: $TARGET"
            echo "使用方法: $0 [build|push|all] [backend|frontend|all]"
            exit 1
            ;;
    esac
    
    info "操作完成！"
    info "镜像地址:"
    info "  后端: ${REGISTRY}/${NAMESPACE}/${BACKEND_IMAGE}:${VERSION}"
    info "  前端: ${REGISTRY}/${NAMESPACE}/${FRONTEND_IMAGE}:${VERSION}"
}

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    error "Docker 未安装，请先安装 Docker"
    exit 1
fi

# 运行主函数
main "$@"

