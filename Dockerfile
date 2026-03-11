# 使用 Python 3.9 作为基础镜像（slim 版本更小巧）
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 升级 pip 并安装依赖（使用国内清华源加速）
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制所有项目文件
COPY . .

# 暴露端口（必须与 Flask 监听端口一致）
EXPOSE 5000

# 启动 Flask 应用
CMD ["python", "app.py"]
