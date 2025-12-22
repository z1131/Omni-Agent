# AI 开发指南

## 必须遵守

### 代码规范

1. **异步优先**：IO 操作使用 `async/await`
2. **类型注解**：所有函数必须有类型注解
3. **结构化日志**：使用 `get_logger()` 而非 `print()`
4. **错误处理**：不吞异常，记录后抛出或处理

```python
# ✅ 正确
async def process(data: bytes) -> str:
    logger = get_logger(__name__)
    try:
        result = await do_something(data)
        logger.info("处理完成", size=len(data))
        return result
    except Exception as e:
        logger.error("处理失败", exc=e)
        raise

# ❌ 错误
def process(data):
    try:
        return do_something(data)
    except:
        pass
```

### 架构规范

1. **单向依赖**：上层依赖下层，不可反向
   - `server` → `orchestrator` → `perception/reasoning/action` → `infra`
2. **Registry 模式**：服务通过 Registry 获取，不直接实例化
3. **配置外置**：通过 Nacos 或环境变量配置，不硬编码

### API 规范

1. **双协议**：新接口同时实现 HTTP 和 gRPC
2. **trace_id**：所有请求必须传递或生成 trace_id
3. **统一响应**：HTTP 使用 `ApiResponse` 包装

```python
from src.server.http.response import ApiResponse

@router.post("/example")
async def example():
    return ApiResponse.success(data={"key": "value"})
```

## 建议遵守

### 命名规范

| 类型 | 规范 | 示例 |
|-----|-----|-----|
| 文件 | snake_case | `session_manager.py` |
| 类 | PascalCase | `SessionManager` |
| 函数/变量 | snake_case | `get_session()` |
| 常量 | UPPER_SNAKE | `MAX_SESSIONS` |
| Proto | PascalCase | `StreamChatRequest` |

### 目录规范

- 新增感知能力：`src/perception/xxx/`
- 新增 LLM 服务：`src/reasoning/llm/xxx.py`
- 新增工具：`src/action/builtins/xxx.py`
- 新增 HTTP 路由：`src/server/http/routes/xxx.py`

### 测试规范

```python
# tests/test_xxx.py
import pytest

@pytest.mark.asyncio
async def test_example():
    result = await some_async_function()
    assert result is not None
```

## 代码示例

### 新增 LLM 服务

```python
# src/reasoning/llm/custom.py
from .base import BaseLlmService, LlmConfig, Message, LlmResponse
from .registry import LlmRegistry

class CustomLlmService(BaseLlmService):
    async def chat(self, messages: List[Message], config: LlmConfig) -> LlmResponse:
        # 实现
        pass
    
    async def chat_stream(self, messages: List[Message], config: LlmConfig):
        # 实现流式
        yield LlmChunk(delta="...")

# 注册
LlmRegistry.register("custom", CustomLlmService)
```

### 新增 HTTP 路由

```python
# src/server/http/routes/example.py
from fastapi import APIRouter
from ..response import ApiResponse

router = APIRouter(prefix="/v1/example", tags=["Example"])

@router.get("/")
async def list_items():
    return ApiResponse.success(data=[])

# 在 routes/__init__.py 中注册
```

### 新增 gRPC 方法

1. 修改 `proto/xxx.proto`
2. 重新生成代码
3. 在 `src/server/grpc/servicer.py` 实现方法
