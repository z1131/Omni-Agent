from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.core.agent import OmniAgent
from src.tools.manager import get_tool_manager, init_tool_manager
from src.tools.mcp_client import get_mcp_client, MCPServerConfig
import os
import json

app = FastAPI(title="Omni-Agent API", version="0.1.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Tool Manager
tool_manager = init_tool_manager()

# Initialize Agent with tools from manager
# We initialize it globally for now. In a real app, might manage sessions.
# Ensure API key is present
if not os.getenv("DASHSCOPE_API_KEY"):
    print("WARNING: DASHSCOPE_API_KEY not found in environment variables.")

def create_agent():
    """创建 Agent 实例，使用当前启用的工具"""
    enabled_tools = tool_manager.get_enabled_tools()
    return OmniAgent(
        name="OmniBot",
        description="A general purpose AI assistant.",
        llm={'model': 'qwen-turbo'},
        function_list=enabled_tools if enabled_tools else None
    )

# 初始 Agent 实例
agent = create_agent()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@app.get("/")
def read_root():
    return {"message": "Hello Omni-Agent"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    """
    Simple chat endpoint.
    Currently returns the full response at once (non-streaming).
    """
    try:
        # Convert Pydantic models to dicts for Qwen-Agent
        msgs = [m.model_dump() for m in request.messages]
        
        # Run the agent
        # agent.run returns an iterator of responses (streaming)
        # For this simple test, we'll consume the iterator and return the last full response
        response_iter = agent.run(msgs)
        last_response = []
        for response in response_iter:
            last_response = response
            
        # Extract the assistant's reply from the last message in the history
        if last_response:
            return {"response": last_response[-1]['content']}
        else:
            return {"response": "No response from agent."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    Returns response incrementally as the agent generates it.
    """
    def generate():
        try:
            # Convert Pydantic models to dicts for Qwen-Agent
            msgs = [m.model_dump() for m in request.messages]
            
            # Run the agent with streaming
            response_iter = agent.run(msgs)
            
            last_content = ""
            for response in response_iter:
                if response and len(response) > 0:
                    # Get the latest message content
                    current_content = response[-1].get('content', '')
                    
                    # Calculate the delta (new content since last yield)
                    if current_content and len(current_content) > len(last_content):
                        delta = current_content[len(last_content):]
                        last_content = current_content
                        
                        # Send as SSE format
                        data = json.dumps({"delta": delta, "content": current_content})
                        yield f"data: {data}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True, 'content': last_content})}\n\n"
            
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.get("/tools")
def get_tools():
    """
    Get the list of available tools with their status.
    """
    tools = tool_manager.to_api_response()
    return {"tools": tools}


@app.get("/tools/{tool_id}")
def get_tool(tool_id: str):
    """
    Get a specific tool's information.
    """
    tool = tool_manager.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return {"tool": tool.to_dict()}


class ToolToggleRequest(BaseModel):
    enabled: bool


@app.post("/tools/{tool_id}/toggle")
def toggle_tool(tool_id: str, request: Optional[ToolToggleRequest] = None):
    """
    Toggle a tool's enabled/disabled status.
    If request body is provided, set to the specified state.
    Otherwise, toggle the current state.
    """
    global agent
    
    tool = tool_manager.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    
    if request is not None:
        # Set to specified state
        if request.enabled:
            tool_manager.enable_tool(tool_id)
        else:
            tool_manager.disable_tool(tool_id)
        new_state = request.enabled
    else:
        # Toggle
        new_state = tool_manager.toggle_tool(tool_id)
    
    # Recreate agent with updated tools
    agent = create_agent()
    
    return {
        "status": "success",
        "tool_id": tool_id,
        "enabled": new_state,
        "message": f"Tool '{tool_id}' {'enabled' if new_state else 'disabled'}"
    }


# Legacy endpoint for backward compatibility
class ToolInstallRequest(BaseModel):
    tool_id: str
    install: bool


@app.post("/tools/install")
def install_tool(request: ToolInstallRequest):
    """
    Legacy endpoint: Enable/disable a tool.
    Use POST /tools/{tool_id}/toggle instead.
    """
    global agent
    
    if request.install:
        success = tool_manager.enable_tool(request.tool_id)
    else:
        success = tool_manager.disable_tool(request.tool_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_id}' not found")
    
    # Recreate agent with updated tools
    agent = create_agent()
    
    action = "enabled" if request.install else "disabled"
    return {
        "status": "success",
        "message": f"Tool {request.tool_id} {action}",
        "tool_id": request.tool_id,
        "installed": request.install
    }


# Workspace File Operations
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../workspace"))
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

class FileContent(BaseModel):
    content: str

@app.get("/files")
def list_files():
    """List files in the workspace directory."""
    try:
        files = []
        for f in os.listdir(WORKSPACE_DIR):
            if os.path.isfile(os.path.join(WORKSPACE_DIR, f)):
                files.append(f)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
def read_file(filename: str):
    """Read content of a specific file."""
    filepath = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{filename}")
def save_file(filename: str, file: FileContent):
    """Save content to a specific file."""
    filepath = os.path.join(WORKSPACE_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(file.content)
        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MCP 相关接口 ====================

mcp_client = get_mcp_client()


class MCPServerRequest(BaseModel):
    """MCP Server 配置请求"""
    id: str
    name: str
    description: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    enabled: bool = False


@app.get("/mcp/servers")
def get_mcp_servers():
    """获取所有 MCP Server 列表"""
    servers = mcp_client.get_all_servers()
    return {
        "servers": [s.to_dict() for s in servers]
    }


@app.get("/mcp/servers/{server_id}")
def get_mcp_server(server_id: str):
    """获取指定 MCP Server 信息"""
    server = mcp_client.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")
    return {"server": server.to_dict()}


@app.post("/mcp/servers")
def add_mcp_server(request: MCPServerRequest):
    """添加新的 MCP Server"""
    global agent
    
    config = MCPServerConfig(
        id=request.id,
        name=request.name,
        description=request.description,
        command=request.command,
        args=request.args,
        env=request.env,
        enabled=request.enabled
    )
    
    server_id = mcp_client.register_server(config)
    
    # 如果启用了，重新创建 agent
    if request.enabled:
        agent = create_agent()
    
    return {
        "status": "success",
        "server_id": server_id,
        "message": f"MCP Server '{request.name}' 添加成功"
    }


@app.put("/mcp/servers/{server_id}")
def update_mcp_server(server_id: str, request: MCPServerRequest):
    """更新 MCP Server 配置"""
    global agent
    
    existing = mcp_client.get_server(server_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")
    
    # 删除旧的，添加新的
    mcp_client.unregister_server(server_id)
    
    config = MCPServerConfig(
        id=request.id,
        name=request.name,
        description=request.description,
        command=request.command,
        args=request.args,
        env=request.env,
        enabled=request.enabled
    )
    
    mcp_client.register_server(config)
    
    # 重新创建 agent
    agent = create_agent()
    
    return {
        "status": "success",
        "message": f"MCP Server '{request.name}' 更新成功"
    }


@app.delete("/mcp/servers/{server_id}")
def delete_mcp_server(server_id: str):
    """删除 MCP Server"""
    global agent
    
    if not mcp_client.unregister_server(server_id):
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")
    
    # 重新创建 agent
    agent = create_agent()
    
    return {
        "status": "success",
        "message": f"MCP Server '{server_id}' 已删除"
    }


@app.post("/mcp/servers/{server_id}/toggle")
def toggle_mcp_server(server_id: str, request: Optional[ToolToggleRequest] = None):
    """切换 MCP Server 启用状态"""
    global agent
    
    server = mcp_client.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")
    
    if request is not None:
        if request.enabled:
            mcp_client.enable_server(server_id)
        else:
            mcp_client.disable_server(server_id)
        new_state = request.enabled
    else:
        new_state = mcp_client.toggle_server(server_id)
    
    # 重新创建 agent
    agent = create_agent()
    
    return {
        "status": "success",
        "server_id": server_id,
        "enabled": new_state,
        "message": f"MCP Server '{server_id}' {'已启用' if new_state else '已禁用'}"
    }


@app.get("/mcp/servers/{server_id}/validate")
def validate_mcp_server(server_id: str):
    """验证 MCP Server 配置是否有效"""
    result = mcp_client.validate_server(server_id)
    return result



