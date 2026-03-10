# 物品借用归还管理系统

一个简洁实用的团队物品借用管理系统，支持借用/归还记录追踪。

## 功能特点

### 普通用户
- 首次登录自动创建账号，需填写真实姓名
- 借用物品：选择物品、填写数量，自动记录借用人及时间
- 归还物品：查看已借物品，一键归还
- 查看个人借用记录

### 管理员
- 账号密码登录（账号：user，密码：12345）
- 物品管理：添加、编辑、删除物品
- 快速调整库存数量
- 拖拽卡片调整显示顺序
- 按名称排序物品
- 查看所有用户的借用/归还记录
- 编辑/删除记录

## 技术栈

- **后端**: Python Flask
- **数据库**: SQLite
- **前端**: HTML + CSS + JavaScript

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 访问
http://localhost:5000
```

## 部署到云平台

### Render.com（推荐）

1. Fork 本仓库到你的 GitHub
2. 访问 https://render.com 并登录
3. 点击 "New" → "Web Service"
4. 连接 GitHub 仓库
5. 配置：
   - Name: item-manager
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
6. 点击 "Create Web Service"
7. 等待部署完成，获得在线访问链接

### Railway.app

1. Fork 本仓库到你的 GitHub
2. 访问 https://railway.app 并登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择本仓库
5. Railway 自动检测并部署
6. 在 Settings 中添加域名

## 默认账号

- 管理员账号：`user`
- 管理员密码：`12345`

## 项目结构

```
item_manager/
├── app.py              # Flask主应用
├── templates/          # HTML模板
│   ├── login.html      # 登录页
│   ├── user.html       # 用户页
│   └── admin.html      # 管理员页
├── requirements.txt    # Python依赖
└── README.md           # 说明文档
```

## 注意事项

- 首次运行会自动创建 SQLite 数据库和默认数据
- 生产环境建议设置环境变量 `SECRET_KEY`
- 数据库文件 `item_manager.db` 在项目根目录生成
