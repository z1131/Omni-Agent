"""
Task 定义

Task 是 Agent 执行的原子单位，可以独立存在，不依赖 Session
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from .events import PerceptionEvent, ModalityType


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 等待开始
    PERCEIVING = "perceiving"   # 感知中
    THINKING = "thinking"       # 思考中
    ACTING = "acting"           # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class StepType(Enum):
    """步骤类型"""
    PERCEPTION = "perception"
    REASONING = "reasoning"
    ACTION = "action"
    OUTPUT = "output"


@dataclass
class ExecutionStep:
    """执行步骤"""
    
    step_id: int
    step_type: StepType
    
    # 输入
    trigger: str = ""
    input_events: List[str] = field(default_factory=list)
    
    # 思考
    thought: Optional[str] = None
    planned_action: Optional[str] = None
    
    # 执行
    action: Optional[str] = None
    action_input: Optional[str] = None
    action_output: Optional[str] = None
    observation: Optional[str] = None
    
    # 时间
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> int:
        if self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "trigger": self.trigger,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "duration_ms": self.duration_ms,
        }


@dataclass
class TaskContext:
    """任务上下文（可选，来自 Session 或外部传入）"""
    
    messages: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })


@dataclass
class TaskResult:
    """任务结果"""
    
    content: str
    format: str = "text"        # text/markdown/json
    messages: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "format": self.format,
            "messages": self.messages,
            "metadata": self.metadata,
        }


@dataclass
class Task:
    """任务 - Agent 执行的基本单位"""
    
    # 标识
    task_id: str
    
    # 输入
    instruction: str                                    # 用户指令（核心）
    input_modalities: List[ModalityType] = field(default_factory=list)
    
    # 上下文（可选，来自 Session 或外部传入）
    context: Optional[TaskContext] = None
    
    # 执行状态
    status: TaskStatus = TaskStatus.PENDING
    perception_buffer: List[PerceptionEvent] = field(default_factory=list)
    steps: List[ExecutionStep] = field(default_factory=list)
    
    # 输出
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_status(self, status: TaskStatus):
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def add_perception(self, event: PerceptionEvent):
        """添加感知事件"""
        self.perception_buffer.append(event)
        self.updated_at = datetime.now()
    
    def add_step(self, step: ExecutionStep):
        """添加执行步骤"""
        self.steps.append(step)
        self.updated_at = datetime.now()
    
    def complete(self, result: TaskResult):
        """完成任务"""
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def fail(self, error: str):
        """任务失败"""
        self.error = error
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取完整的消息列表（上下文 + 当前感知）"""
        messages = []
        
        # 继承上下文
        if self.context:
            messages.extend(self.context.messages)
        
        # 添加当前感知内容
        perception_content = self._format_perception()
        if perception_content:
            messages.append({"role": "user", "content": perception_content})
        
        return messages
    
    def _format_perception(self) -> str:
        """格式化感知缓冲区为文本"""
        parts = []
        for event in self.perception_buffer:
            if event.modality == ModalityType.AUDIO:
                parts.append(f"[语音识别] {event.content}")
            elif event.modality == ModalityType.IMAGE:
                parts.append(f"[图像识别] {event.content}")
            else:
                parts.append(event.content)
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "instruction": self.instruction,
            "status": self.status.value,
            "steps_count": len(self.steps),
            "result": self.result.to_dict() if self.result else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
