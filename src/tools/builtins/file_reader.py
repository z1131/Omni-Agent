"""
File Reader Tool - 文件读取工具

允许 Agent 读取工作区内的文件内容
"""

import os
import json
from typing import Union
from qwen_agent.tools.base import BaseTool, register_tool

# 工作区路径
WORKSPACE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../workspace")
)


@register_tool('file_reader')
class FileReader(BaseTool):
    """读取工作区文件内容的工具"""
    
    name = 'file_reader'
    name_for_human = 'File Reader'
    description = '读取工作区内文件的内容。只能读取 workspace 目录下的文件。'
    parameters = [{
        'name': 'path',
        'type': 'string',
        'description': '要读取的文件路径（相对于 workspace 目录）',
        'required': True
    }]
    
    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        读取文件内容
        
        Args:
            params: 包含 path 参数的 JSON 字符串或字典
        
        Returns:
            文件内容或错误信息
        """
        # 解析参数
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                # 如果不是 JSON，假设直接传入的是路径
                params = {'path': params}
        
        file_path = params.get('path', '')
        
        # 安全检查：确保路径在 workspace 内
        full_path = os.path.normpath(os.path.join(WORKSPACE_DIR, file_path))
        if not full_path.startswith(WORKSPACE_DIR):
            return f"Error: Access denied. Can only read files within workspace directory."
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            return f"Error: File not found: {file_path}"
        
        if not os.path.isfile(full_path):
            return f"Error: Path is not a file: {file_path}"
        
        # 读取文件
        try:
            # 尝试以文本方式读取
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 限制返回内容长度
            max_length = 10000
            if len(content) > max_length:
                content = content[:max_length] + f"\n\n... (truncated, total {len(content)} chars)"
            
            return f"File: {file_path}\n\n{content}"
            
        except UnicodeDecodeError:
            return f"Error: Cannot read file as text (might be binary): {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
