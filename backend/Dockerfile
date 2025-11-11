# 使用Python 3.11官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖（包括ffmpeg用于音频转换）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 配置Poetry
RUN poetry config virtualenvs.create false

# 复制Poetry配置文件
COPY pyproject.toml poetry.lock ./

# 更新lock文件并安装Python依赖
RUN poetry lock && poetry install --only=main

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads/audio uploads/avatars

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
