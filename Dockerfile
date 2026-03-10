# 强制使用 Python 3.9 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 升级 pip 并安装依赖（使用国内源，并确保 pip 是最新）
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制所有项目文件
COPY . .

# 暴露端口（必须和你的 Flask 端口一致）
EXPOSE 5000

# 启动命令（使用 python3 确保调用 Python 3）
CMD ["python3", "app.py"]
