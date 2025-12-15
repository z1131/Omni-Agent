# 通用智能体 (General Agent)

基于 [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) 开发的通用智能体。

## 目录结构
*   `src/`: 源代码
*   `docs/`: 文档
*   `Qwen-Agent/`: Qwen-Agent 源码仓库

## 安装
1.  确保已安装 Python 3.8+。
2.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

## 配置
在使用前，请设置 DashScope API Key：
```bash
export DASHSCOPE_API_KEY="your-api-key"
```

## 运行
### Web UI
启动 Gradio 界面：
```bash
python src/app.py
```

### 命令行测试
运行简单的测试脚本：
```bash
python tests/test_agent.py
```
# Omni-Agent
