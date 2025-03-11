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
.\venv\Scripts\Activate.ps1

# 激活虚拟环境（Linux/macOS）
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
npm install
```

## 配置文件
1. 复制example.env重命名为.env
2. 修改配置项：
```
# 系统密码（必需配置）
# 请设置一个安全的密码，用于系统登录
SYSTEM_PASSWORD=your_secure_password

# 上传目录
UPLOAD_FOLDER=uploads
```

## 运行步骤
```bash
# 开发环境：实时编译Tailwind CSS
npm run watch:css

# 生产环境：编译CSS
npm run build:css

# 启动应用
python app.py
```

注意：应用启动模式由.env文件中的FLASK_DEBUG环境变量控制：
- 当FLASK_DEBUG=True时，使用Flask开发服务器
- 当FLASK_DEBUG=False或未设置时，使用Waitress服务器

## 常见问题
### 无法上传文件
- 检查uploads目录权限
- 确认文件大小不超过100MB

### 样式未加载
- 执行`npm run build:css`重新编译
- 检查static/css/styles.css是否存在

## 生产部署
1. 确保已设置正确的环境变量：
   - SYSTEM_PASSWORD：系统登录密码
   - UPLOAD_FOLDER：文件上传目录（可选）
   - FLASK_DEBUG：设置为False以使用Waitress服务器

2. 编译前端资源：
   ```bash
   npm run build:css
   ```

3. 启动应用：
   ```bash
   python app.py
   ```
   注意：确保.env文件中设置了FLASK_DEBUG=False，这样应用将使用Waitress服务器运行。

4. 配置Nginx反向代理（推荐）：
   ```nginx
   location / {
       proxy_pass http://localhost:8080;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```
