# Omni-Agent 文档

## 快速导航

### 概览
- [项目概览](项目概览.md) - 项目介绍、技术栈、架构图

### 业务领域
- [会话与任务](领域/会话与任务.md) - Session/Task 核心概念
- [多模态感知](领域/多模态感知.md) - 感知事件、模态类型

### 技术模块
- [编排引擎](技术/编排引擎.md) - Orchestrator 使用方式
- [感知层](技术/感知层.md) - STT 等感知能力
- [推理层](技术/推理层.md) - LLM 服务、OmniAgent
- [执行层](技术/执行层.md) - 工具管理、MCP
- [服务层](技术/服务层.md) - HTTP/gRPC 接口
- [基础设施](技术/基础设施.md) - 日志、Nacos、指标

### 开发与运维
- [AI开发指南](AI开发指南.md) - 代码规范、开发原则
- [部署方案](部署方案.md) - 环境配置、Docker 部署

### 决策记录
- `决策/` - 架构决策记录（按需添加）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 设置 API Key
export DASHSCOPE_API_KEY="your-key"

# 启动服务
python -m uvicorn src.main:app --reload --port 8000

# 访问
# HTTP API: http://localhost:8000/docs
# gRPC: localhost:50051
```

## 文档约定

- 每个文档不超过 200 行
- 能用代码示例就不用描述
- 只写「必须知道」的内容
- 文件名用中文（README.md 除外）
