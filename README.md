# 文件管理系统初始化指南

## 环境要求
- Python 3.8+
- Node.js 16+
- Windows/Linux/macOS

## 依赖安装
```bash
# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
npm install
```

## 配置文件
1. 复制example.env重命名为.env
2. 修改配置项：
```
# 系统密码
SYSTEM_PASSWORD=your_password

# 密码模式（env:仅环境变量 fixed:固定密码 both:两者兼用）
PASSWORD_MODE=both

# 上传目录
UPLOAD_FOLDER=uploads
```

## 运行步骤
```bash
# 开发模式
flask run --port 8080

# 生产模式（使用Waitress）
waitress-serve --port=8080 --call app:create_app

# 实时编译Tailwind CSS
npx tailwindcss -i ./static/css/main.css -o ./static/css/styles.css --watch

# 生产环境编译CSS
npm run build:css
```

## 常见问题
### 无法上传文件
- 检查uploads目录权限
- 确认文件大小不超过100MB

### 样式未加载
- 执行`npm run build:css`重新编译
- 检查static/css/styles.css是否存在

## 生产部署
推荐使用Nginx反向代理，配置示例：
```nginx
location / {
    proxy_pass http://localhost:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```
