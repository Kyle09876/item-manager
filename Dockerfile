FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
# 直接安装依赖（使用国内清华源加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
