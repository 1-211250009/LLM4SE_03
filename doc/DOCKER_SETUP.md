# Docker配置指南

## 🚀 快速配置Docker镜像加速器

### macOS（Docker Desktop）

1. **打开Docker Desktop**

2. **进入设置**
   - 点击右上角的齿轮图标⚙️

3. **配置镜像加速器**
   - 左侧菜单选择 **Docker Engine**
   - 在右侧JSON编辑器中，找到或添加 `registry-mirrors` 配置：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
```

4. **应用并重启**
   - 点击右下角 **Apply & Restart** 按钮
   - 等待Docker重启（约10-20秒）

5. **验证配置**
   ```bash
   docker info | grep -A 5 "Registry Mirrors"
   ```

---

## 📦 然后启动服务

配置完成后，在终端运行：

```bash
# 确保在项目根目录
cd /Users/yanhaoxiang/Workspace/LLM4SE_03

# 启动PostgreSQL和Redis
docker-compose -f docker-compose.dev.yml up -d

# 查看容器状态
docker ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs
```

---

## ✅ 预期结果

启动成功后，`docker ps` 应该显示：

```
CONTAINER ID   IMAGE                  STATUS         PORTS                    NAMES
xxxxxxxxxxxx   postgres:15-alpine     Up 10 seconds  0.0.0.0:5432->5432/tcp   travel-planner-postgres
xxxxxxxxxxxx   redis:7-alpine         Up 10 seconds  0.0.0.0:6379->6379/tcp   travel-planner-redis
```

---

## 🔍 常见问题

### Q: Docker Desktop没有启动？

打开Launchpad，找到并启动 **Docker** 应用。

### Q: 还是提示需要登录？

如果配置镜像加速器后还是不行，可以手动登录Docker Hub：

```bash
# 在终端运行
docker login

# 输入你的Docker Hub用户名和密码
# 如果没有账号，访问 https://hub.docker.com/ 注册
```

### Q: 镜像下载很慢？

第一次下载镜像可能需要几分钟，请耐心等待。可以查看进度：

```bash
docker-compose -f docker-compose.dev.yml up -d --verbose
```

---

**配置好Docker Desktop后告诉我，我们继续启动数据库服务！** 🚀

