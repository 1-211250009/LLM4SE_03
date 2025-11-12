# 多阶段构建 - 构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 定义构建参数（从 docker-compose 传入）
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_BAIDU_MAPS_API_KEY
ARG VITE_XUNFEI_APP_ID
ARG VITE_XUNFEI_API_KEY
ARG VITE_XUNFEI_API_SECRET

# 将构建参数设置为环境变量（Vite 在构建时需要）
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BAIDU_MAPS_API_KEY=$VITE_BAIDU_MAPS_API_KEY
ENV VITE_XUNFEI_APP_ID=$VITE_XUNFEI_APP_ID
ENV VITE_XUNFEI_API_KEY=$VITE_XUNFEI_API_KEY
ENV VITE_XUNFEI_API_SECRET=$VITE_XUNFEI_API_SECRET

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装所有依赖（包括开发依赖，构建需要）
RUN npm ci

# 复制源代码
COPY . .

# 清理并重新安装依赖以解决ARM64 rollup问题
RUN rm -rf node_modules package-lock.json && npm install

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建的文件到nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
