# 快速运行指南 ⚡

> 最快的方式启动项目 - 3分钟搞定！

## 🚀 最简单方式（推荐）

### 步骤1：配置API密钥（只需一次）

```bash
# 进入项目目录
cd LLM4SE_03

# 创建后端配置
cp backend/ENV_TEMPLATE.txt backend/.env
vim backend/.env
```

**在 backend/.env 中填入**（最少配置）：
```bash
# 数据库（使用Docker时保持默认）
DATABASE_URL=postgresql://admin:password@localhost:5432/travel_planner

# Redis
REDIS_URL=redis://localhost:6379

# JWT密钥（随便写一个长字符串）
SECRET_KEY=change-this-to-a-random-secret-key-at-least-32-characters-long

# DeepSeek API（必需！）
DEEPSEEK_API_KEY=sk-你的密钥

# 百度地图（必需！）
BAIDU_MAP_AK=你的百度地图密钥
```

```bash
# 创建前端配置
cp frontend/ENV_TEMPLATE.txt frontend/.env
vim frontend/.env
```

**在 frontend/.env 中填入**：
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_BAIDU_MAPS_API_KEY=你的百度地图密钥
VITE_ENABLE_VOICE=false
```

### 步骤2：使用启动脚本

```bash
./start.sh dev
```

### 步骤3：启动后端（新终端）

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 步骤4：启动前端（新终端）

```bash
cd frontend
npm install
npm run dev
```

### 步骤5：访问应用

打开浏览器访问：http://localhost:5173

---

## 🎯 一键生产部署（Docker）

如果您只是想快速体验，不需要开发：

```bash
# 1. 配置环境变量（见上面步骤1）

# 2. 一键启动
./start.sh prod

# 3. 访问
# 前端: http://localhost
# 后端: http://localhost:8000/docs
```

---

## 🔑 API密钥获取

### DeepSeek API（免费额度）
1. 访问：https://platform.deepseek.com/
2. 注册账号
3. 创建API Key
4. 复制密钥（格式：sk-xxxxx）

### 百度地图API（免费配额）
1. 访问：https://lbsyun.baidu.com/
2. 注册百度账号
3. 进入控制台 → 应用管理 → 创建应用
4. 选择"浏览器端"
5. 复制AK（应用Key）

### 科大讯飞（可选）
如果需要语音功能：
1. 访问：https://www.xfyun.cn/
2. 注册账号
3. 创建应用，开通"语音听写"和"在线语音合成"
4. 获取 APPID、APIKey、APISecret
5. 在前端.env中设置 `VITE_ENABLE_VOICE=true`

---

## ⚠️ 常见启动问题

### 问题1：端口被占用

```bash
# 查看占用端口的进程
lsof -i :8000  # 后端
lsof -i :5173  # 前端
lsof -i :5432  # 数据库

# 杀死进程
kill -9 <PID>
```

### 问题2：数据库连接失败

```bash
# 检查数据库是否启动
docker-compose -f docker-compose.dev.yml ps

# 重启数据库
docker-compose -f docker-compose.dev.yml restart postgres

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs postgres
```

### 问题3：ImportError: cannot import name 'Budget'

✅ **已修复**！如果还遇到，运行：
```bash
cd backend
python -c "from app.models.trip import Trip, Itinerary, ItineraryItem, Expense; print('导入成功')"
```

### 问题4：前端页面空白

1. 检查后端是否启动：访问 http://localhost:8000/health
2. 检查浏览器控制台是否有错误
3. 确认`.env`中的`VITE_API_BASE_URL`正确

### 问题5：地图不显示

1. 检查百度地图API密钥是否配置
2. 打开浏览器控制台，查看是否有地图加载错误
3. 确认API密钥有效且配额充足

---

## ✅ 启动成功检查

运行以下命令验证：

```bash
# 后端健康检查
curl http://localhost:8000/health
# 预期输出: {"status":"healthy"}

# 前端是否启动
curl http://localhost:5173
# 预期输出: HTML内容
```

---

## 📚 更多帮助

- **详细运行指南**: [HOW_TO_RUN.md](HOW_TO_RUN.md)
- **语音配置指南**: [doc/VOICE_SETUP_GUIDE.md](doc/VOICE_SETUP_GUIDE.md)
- **重构说明**: [doc/REFACTORING_SUMMARY.md](doc/REFACTORING_SUMMARY.md)
- **完整文档**: [doc/](doc/)

---

## 🎉 快速测试

启动成功后，尝试以下操作：

1. **注册账号** → http://localhost:5173/register
2. **登录系统**
3. **导航到"行程规划"**
4. **点击AI助手图标**（右下角）
5. **输入**: "我想去北京玩3天，预算5000元"
6. **查看AI生成的行程规划**

---

**祝您使用愉快！** 🎊

有问题？查看 [HOW_TO_RUN.md](HOW_TO_RUN.md) 或提交Issue。

