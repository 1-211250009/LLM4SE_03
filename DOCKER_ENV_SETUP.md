# Docker 环境变量配置指南

## 📋 快速配置步骤

### 1. 创建 `.env` 文件

在项目根目录创建 `.env` 文件（基于 `ENV_EXAMPLE`）：

```bash
cp ENV_EXAMPLE .env
```

### 2. 生成 JWT 密钥（SECRET_KEY）

JWT 密钥不是从服务获取的，需要自己生成。可以使用以下方法：

**方法1: 使用提供的脚本（推荐）**
```bash
./generate_secret_key.sh
```

**方法2: 使用 Python**
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**方法3: 使用 OpenSSL**
```bash
openssl rand -hex 32
```

**方法4: 在线生成**
访问 https://randomkeygen.com/ 生成随机密钥

### 3. 编辑 `.env` 文件

使用文本编辑器打开 `.env` 文件，填入生成的 SECRET_KEY 和其他 API 密钥：

```bash
# 后端配置
SECRET_KEY=your-generated-secret-key-here  # 使用上面生成的密钥
DEEPSEEK_API_KEY=sk-your-actual-deepseek-key
BAIDU_MAPS_API_KEY=your-actual-baidu-key
BAIDU_MAP_AK=your-actual-baidu-ak
BAIDU_MAP_SK=your-actual-baidu-sk
XFYUN_APP_ID=your-actual-xfyun-app-id
XFYUN_API_KEY=your-actual-xfyun-api-key
XFYUN_API_SECRET=your-actual-xfyun-api-secret

# 前端配置
VITE_API_BASE_URL=http://localhost:8000
VITE_BAIDU_MAPS_API_KEY=your-actual-baidu-key
VITE_XUNFEI_APP_ID=your-actual-xfyun-app-id
VITE_XUNFEI_API_KEY=your-actual-xfyun-api-key
VITE_XUNFEI_API_SECRET=your-actual-xfyun-api-secret
```

### 4. 启动 Docker 容器

```bash
docker-compose up -d --build
```

Docker Compose 会自动从 `.env` 文件读取环境变量并传递给容器。

## 🔑 API 密钥申请地址

### DeepSeek API
- 申请地址: https://platform.deepseek.com/
- 用途: AI 对话和工具调用

### 百度地图 API
- 申请地址: https://lbsyun.baidu.com/
- 用途: 地图显示、POI 搜索、路线规划
- 需要申请: `BAIDU_MAPS_API_KEY`（JavaScript API Key）

### 科大讯飞 API
- 申请地址: https://www.xfyun.cn/
- 用途: 语音识别（ASR）和语音合成（TTS）
- 需要申请: `XFYUN_APP_ID`、`XFYUN_API_KEY`、`XFYUN_API_SECRET`

## ⚠️ 重要提示

1. **`.env` 文件已被 `.gitignore` 忽略**，不会被提交到 git 仓库
2. **不要将真实的 API 密钥提交到代码仓库**
3. **生产环境请使用强密钥**，特别是 `SECRET_KEY`
4. 如果修改了 `.env` 文件，需要重新构建容器：
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## 🔍 验证配置

启动容器后，检查环境变量是否正确传递：

```bash
# 检查后端环境变量
docker-compose exec backend env | grep -E "DEEPSEEK|BAIDU|XFYUN"

# 检查容器日志
docker-compose logs backend | grep -i "api\|key\|error"
```

## 📝 环境变量说明

### 后端环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `SECRET_KEY` | JWT 签名密钥（需要自己生成，至少32字符） | 是 | - |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 | - |
| `BAIDU_MAPS_API_KEY` | 百度地图 API Key | 是 | - |
| `BAIDU_MAP_AK` | 百度地图 Access Key | 是 | - |
| `BAIDU_MAP_SK` | 百度地图 Secret Key | 是 | - |
| `XFYUN_APP_ID` | 科大讯飞应用 ID | 是 | - |
| `XFYUN_API_KEY` | 科大讯飞 API Key | 是 | - |
| `XFYUN_API_SECRET` | 科大讯飞 API Secret | 是 | - |

### 前端环境变量（构建时）

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 地址 | 是 | `http://localhost:8000` |
| `VITE_BAIDU_MAPS_API_KEY` | 百度地图 API Key | 是 | - |
| `VITE_XUNFEI_APP_ID` | 科大讯飞应用 ID | 是 | - |
| `VITE_XUNFEI_API_KEY` | 科大讯飞 API Key | 是 | - |
| `VITE_XUNFEI_API_SECRET` | 科大讯飞 API Secret | 是 | - |

## 🐛 故障排查

### 问题：API 调用失败

1. **检查环境变量是否正确传递**：
   ```bash
   docker-compose exec backend env | grep API_KEY
   ```

2. **检查容器日志**：
   ```bash
   docker-compose logs backend | tail -50
   ```

3. **重新构建容器**（如果修改了 `.env`）：
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### 问题：前端无法访问后端

检查 `VITE_API_BASE_URL` 是否正确：
- 开发环境: `http://localhost:8000`
- Docker 环境: `http://localhost:8000`（前端通过浏览器访问，使用宿主机地址）

### 问题：语音识别不工作

1. 确保所有科大讯飞相关的环境变量都已配置
2. 检查前端构建时是否正确传入了环境变量
3. 查看浏览器控制台是否有错误信息

---

**最后更新**: 2024年12月

