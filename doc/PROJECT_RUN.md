# 项目运行指南

## 🚀 快速启动

### 后端服务 (FastAPI)

1. **进入后端目录**
   ```bash
   cd backend
   ```

2. **安装依赖**
   ```bash
   # 使用 Poetry (推荐)
   poetry install
   
   # 或使用 pip
   pip install -r requirements.txt
   ```

3. **启动后端服务**
   ```bash
   # 使用 Poetry
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # 或直接使用 uvicorn
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **访问后端API**
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

### 前端服务 (React + Vite)

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动前端服务**
   ```bash
   npm run dev
   ```

4. **访问前端应用**
   - 应用地址: http://localhost:5173
   - 自动热重载，修改代码后自动刷新

## 🔧 开发环境配置

### 环境变量设置

1. **后端环境变量**
   ```bash
   # 复制环境变量模板
   cp backend/ENV_TEMPLATE.txt backend/.env
   
   # 编辑环境变量文件
   vim backend/.env
   ```

2. **前端环境变量**
   ```bash
   # 创建前端环境变量文件
   touch frontend/.env.local
   
   # 添加API基础URL
   echo "VITE_API_BASE_URL=http://localhost:8000" >> frontend/.env.local
   ```

### 数据库设置

1. **运行数据库迁移**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **创建超级用户**
   ```bash
   # 使用Python脚本创建管理员用户
   python -c "
   from app.core.database import get_db
   from app.models.user import User
   from app.core.security import get_password_hash
   from sqlalchemy.orm import Session
   
   db = next(get_db())
   admin_user = User(
       username='admin',
       email='admin@example.com',
       hashed_password=get_password_hash('admin123'),
       is_active=True,
       is_superuser=True
   )
   db.add(admin_user)
   db.commit()
   print('管理员用户创建成功: admin/admin123')
   "
   ```

## 🐳 Docker 运行

### 快速启动 (推荐)

1. **启动所有服务**
   ```bash
   # 使用生产配置
   docker-compose up -d
   
   # 或使用开发配置
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **查看服务状态**
   ```bash
   docker-compose ps
   ```

3. **查看服务日志**
   ```bash
   # 查看所有服务日志
   docker-compose logs -f
   
   # 查看特定服务日志
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

4. **停止服务**
   ```bash
   docker-compose down
   ```

### 服务访问地址

- **前端应用**: http://localhost (端口80)
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432
- **Redis**: localhost:6379

### 单独构建和运行

1. **构建后端镜像**
   ```bash
   cd backend
   docker build -t travel-planner-backend .
   ```

2. **构建前端镜像**
   ```bash
   cd frontend
   docker build -t travel-planner-frontend .
   ```

3. **运行单个服务**
   ```bash
   # 运行后端
   docker run -p 8000:8000 travel-planner-backend
   
   # 运行前端
   docker run -p 80:80 travel-planner-frontend
   ```

### Docker 开发模式

1. **开发环境启动**
   ```bash
   # 启动数据库和缓存
   docker-compose -f docker-compose.dev.yml up -d postgres redis
   
   # 本地运行后端
   cd backend && poetry run uvicorn app.main:app --reload
   
   # 本地运行前端
   cd frontend && npm run dev
   ```

2. **热重载开发**
   ```bash
   # 使用开发配置，支持代码热重载
   docker-compose -f docker-compose.dev.yml up
   ```

## 📋 常用命令

### 后端命令
```bash
# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

### 前端命令
```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

## 🔍 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000  # 后端端口
   lsof -i :5173  # 前端端口
   
   # 杀死进程
   kill -9 <PID>
   ```

2. **依赖安装失败**
   ```bash
   # 清理缓存
   npm cache clean --force
   pip cache purge
   
   # 重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **数据库连接问题**
   ```bash
   # 检查数据库服务
   docker ps | grep postgres
   
   # 重启数据库
   docker-compose restart db
   ```

## 📚 项目结构

```
LLM4SE_03/
├── backend/                 # 后端服务
│   ├── app/                # 应用代码
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试代码
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端应用
│   ├── src/                # 源代码
│   ├── public/             # 静态资源
│   └── package.json        # Node.js依赖
├── doc/                    # 项目文档
└── docker-compose.dev.yml  # Docker配置
```

## 🎯 开发流程

1. **启动后端服务** → 确保API可用
2. **启动前端服务** → 确保UI正常显示
3. **进行开发** → 修改代码，自动热重载
4. **测试功能** → 使用浏览器测试
5. **提交代码** → 使用Git提交更改

## 📞 技术支持

如果遇到问题，请检查：
- 端口是否被占用
- 依赖是否正确安装
- 环境变量是否正确配置
- 数据库服务是否正常运行
