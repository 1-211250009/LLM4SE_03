# 前端环境变量配置指南

## 配置步骤

### 1. 复制环境变量模板
```bash
cd frontend
cp ENV_TEMPLATE.txt .env.local
```

### 2. 编辑环境变量文件
打开 `frontend/.env.local` 文件，填入真实的API Key：

```bash
# 百度地图API配置
VITE_BAIDU_MAPS_API_KEY=你的真实百度地图API_Key

# 其他前端API配置
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=AI旅行规划师
```

### 3. 获取百度地图API Key

1. 访问 [百度地图开放平台](https://lbsyun.baidu.com/)
2. 注册/登录账号
3. 进入控制台，创建应用
4. 选择应用类型：浏览器端
5. 配置域名白名单：
   - 开发环境：`localhost:5173`, `localhost:3000`
   - 生产环境：你的域名
6. 获取API Key

### 4. 重启开发服务器
```bash
npm run dev
```

## 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_BAIDU_MAPS_API_KEY` | 百度地图API Key | `your_baidu_maps_api_key_here` |
| `VITE_API_BASE_URL` | 后端API地址 | `http://localhost:8000` |
| `VITE_APP_TITLE` | 应用标题 | `AI旅行规划师` |

## 注意事项

1. 环境变量文件 `.env.local` 不要提交到Git
2. 确保API Key的域名白名单配置正确
3. 开发环境使用 `localhost`，生产环境使用实际域名
4. 重启开发服务器后环境变量才会生效

## 故障排除

### 问题：APP不存在，AK有误
**原因：** API Key不正确或域名未配置
**解决：**
1. 检查API Key是否正确
2. 检查域名白名单配置
3. 确保使用正确的应用类型（浏览器端）

### 问题：地图不显示
**原因：** API Key未配置或网络问题
**解决：**
1. 检查环境变量是否正确设置
2. 检查网络连接
3. 查看浏览器控制台错误信息
