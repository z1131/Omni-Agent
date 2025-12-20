# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omni-Agent 是一个通用智能体内核，基于 Qwen-Agent 开发，为 DeepKnow 微服务体系提供 AI 能力层。它作为业务服务（如 GoodTalk）的 AI 后端，通过 gRPC 和 HTTP 双协议对外提供服务。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Server Layer                          │
│  ┌─────────────────────┐   ┌─────────────────────────────┐  │
│  │  HTTP (FastAPI)     │   │  gRPC (grpcio)              │  │
│  │  Port: 8000         │   │  Port: 50051                │  │
│  │  /v1/sessions/*     │   │  OmniAgentService           │  │
│  │  /v1/chat/*         │   │  - Process (multimodal)     │  │
│  │  /v1/stt/*          │   │  - StreamChat               │  │
│  └─────────────────────┘   │  - StreamSTT                │  │
│                            └─────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                     Orchestrator Layer                       │
│  Session → Task → Orchestrator Engine                        │
│  负责 Task/Session 管理、多模态输入归一化、能力调度             │
└───────────────────────────────┬─────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Perception   │       │   Reasoning   │       │    Action     │
│  (感知层)      │       │   (推理层)     │       │   (执行层)    │
│  - STT        │       │  - LLM        │       │  - MCP Client │
│  - Aliyun STT │       │  - OmniAgent  │       │  - Tools      │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Key Components

- **OmniAgent** (`src/reasoning/agent.py`): 继承自 `qwen_agent.agents.Assistant`，核心智能体类
- **Orchestrator** (`src/orchestrator/`): 编排层，管理 Session/Task 生命周期
- **gRPC Server** (`src/server/grpc/`): 为 Java 业务服务提供 gRPC 接口
- **HTTP Server** (`src/main.py`): FastAPI 应用，提供 REST API

## Common Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（HTTP + gRPC）
python -m uvicorn src.main:app --reload --port 8000

# 仅启动 gRPC 服务
python -m src.server.grpc.server

# 运行测试
python tests/test_agent.py

# 生成 gRPC 代码（从 proto 文件）
python -m grpc_tools.protoc -I./proto --python_out=./src/server/grpc/generated --grpc_python_out=./src/server/grpc/generated ./proto/*.proto

# Docker 构建
docker build -t omni-agent .

# Docker 本地运行
docker compose -f deploy/docker-compose.yml up
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DASHSCOPE_API_KEY` | Yes | - | DashScope API Key for Qwen models |
| `GRPC_ENABLED` | No | `true` | Enable gRPC server |
| `GRPC_PORT` | No | `50051` | gRPC server port |
| `HOST` | No | `0.0.0.0` | HTTP server host |
| `PORT` | No | `8000` | HTTP server port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `LOG_FORMAT` | No | `text` | Log format: text or json |

## Proto Files

gRPC 接口定义在 `proto/` 目录：
- `omni_agent.proto`: 主服务定义
- `stt.proto`: 语音转文字
- `llm.proto`: LLM 对话
- `multimodal.proto`: 多模态处理

修改 proto 后需重新生成 Python 代码到 `src/server/grpc/generated/`。

## Deployment

服务通过 GitHub Actions 自动部署到阿里云 ECS：
- 镜像推送到 ACR (阿里云容器镜像服务)
- 滚动部署到 ECS-1 和 ECS-2
- 生产配置文件: `docker-compose.prod.yml`
- 服务器环境变量: `/root/omni-agent/.env`
