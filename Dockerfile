FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装额外依赖（用于生产）
RUN pip install --no-cache-dir \
    dashscope \
    websockets \
    python-multipart \
    pydantic-settings

# 复制 proto 文件并重新生成 gRPC 代码（确保与 protobuf 运行时版本匹配）
COPY proto/ ./proto/
RUN mkdir -p src/server/grpc/generated && \
    python -m grpc_tools.protoc \
    -I proto \
    --python_out=src/server/grpc/generated \
    --grpc_python_out=src/server/grpc/generated \
    proto/*.proto

# 复制源代码（覆盖生成的文件外的其他代码）
COPY src/ ./src/

# 暴露端口
# 8000: HTTP API (FastAPI)
# 50051: gRPC API (业务服务调用)
EXPOSE 8000 50051

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
