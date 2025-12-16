"""
Omni-Agent 编排层

编排层是 Omni-Agent 的核心，负责：
- Task/Session 管理
- 多模态输入归一化
- 能力调度（感知→推理→执行）
- 触发决策
"""

from .task import Task, TaskStatus, TaskResult, TaskContext
from .session import Session, SessionConfig, SessionStatus, SessionManager, get_session_manager
from .engine import Orchestrator
from .events import PerceptionEvent, ModalityType, EventStage

__all__ = [
    # Task
    'Task',
    'TaskStatus',
    'TaskResult',
    'TaskContext',
    # Session
    'Session',
    'SessionConfig',
    'SessionStatus',
    'SessionManager',
    'get_session_manager',
    # Engine
    'Orchestrator',
    # Events
    'PerceptionEvent',
    'ModalityType',
    'EventStage',
]
