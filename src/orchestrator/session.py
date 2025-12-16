"""
Session 定义

Session 是 Task 的容器，用于多轮对话场景（可选）
"""

import uuid
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List

from .task import Task, TaskContext, TaskStatus
from .events import ModalityType
from ..infra import get_logger, get_metrics, generate_trace_id

logger = get_logger(__name__)
metrics = get_metrics()


class SessionStatus(Enum):
    """会话状态"""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class SttConfig:
    """STT 配置"""
    provider: str = "aliyun"
    model: str = "paraformer-realtime-v2"
    language: str = "zh-CN"
    sample_rate: int = 16000
    enable_punctuation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "language": self.language,
            "sample_rate": self.sample_rate,
            "enable_punctuation": self.enable_punctuation,
        }


@dataclass
class LlmConfig:
    """LLM 配置"""
    provider: str = "qwen"
    model: str = "qwen-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.system_message:
            result["system_message"] = self.system_message
        return result


@dataclass
class SessionConfig:
    """会话配置"""
    stt: SttConfig = field(default_factory=SttConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    timeout_seconds: int = 3600  # 默认1小时超时
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        stt_data = data.get('stt', {})
        llm_data = data.get('llm', {})
        
        return cls(
            stt=SttConfig(
                provider=stt_data.get('provider', 'aliyun'),
                model=stt_data.get('model', 'paraformer-realtime-v2'),
                language=stt_data.get('language', 'zh-CN'),
                sample_rate=stt_data.get('sample_rate', 16000),
                enable_punctuation=stt_data.get('enable_punctuation', True),
            ),
            llm=LlmConfig(
                provider=llm_data.get('provider', 'qwen'),
                model=llm_data.get('model', 'qwen-turbo'),
                temperature=llm_data.get('temperature', 0.7),
                max_tokens=llm_data.get('max_tokens', 2048),
                system_message=llm_data.get('system_message'),
            ),
            timeout_seconds=data.get('timeout_seconds', 3600),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stt": self.stt.to_dict(),
            "llm": self.llm.to_dict(),
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class SessionStats:
    """会话统计"""
    tasks_count: int = 0
    stt_requests: int = 0
    llm_requests: int = 0
    total_tokens: int = 0
    errors_count: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "tasks_count": self.tasks_count,
            "stt_requests": self.stt_requests,
            "llm_requests": self.llm_requests,
            "total_tokens": self.total_tokens,
            "errors_count": self.errors_count,
        }


@dataclass
class Session:
    """会话 - Task 的容器，用于多轮对话"""
    
    session_id: str
    trace_id: str
    client_id: str
    config: SessionConfig
    status: SessionStatus
    
    # 任务历史
    tasks: List[Task] = field(default_factory=list)
    
    # 统计
    stats: SessionStats = field(default_factory=SessionStats)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=self.config.timeout_seconds)
    
    @property
    def context(self) -> TaskContext:
        """从历史任务聚合上下文"""
        messages = []
        for task in self.tasks:
            if task.result:
                messages.extend(task.result.messages)
        return TaskContext(messages=messages)
    
    def create_task(
        self, 
        instruction: str, 
        input_modalities: Optional[List[ModalityType]] = None,
        **kwargs
    ) -> Task:
        """创建任务（自动继承上下文）"""
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            instruction=instruction,
            input_modalities=input_modalities or [],
            context=self.context,
            **kwargs
        )
        self.tasks.append(task)
        self.stats.tasks_count += 1
        self.touch()
        return task
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_active(self) -> bool:
        """检查是否活跃"""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()
    
    def touch(self) -> None:
        """更新活跃时间"""
        self.updated_at = datetime.now(timezone.utc)
    
    def close(self) -> None:
        """关闭会话"""
        self.status = SessionStatus.CLOSED
        self.touch()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "client_id": self.client_id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "tasks_count": len(self.tasks),
            "stats": self.stats.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class SessionManager:
    """会话管理器"""
    
    def __init__(
        self,
        cleanup_interval: int = 60,
        max_sessions: int = 1000
    ):
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._max_sessions = max_sessions
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """启动会话管理器"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("SessionManager started")
    
    async def stop(self) -> None:
        """停止会话管理器"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("SessionManager stopped")
    
    def create(
        self,
        client_id: str,
        config: Optional[SessionConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """创建会话"""
        with self._lock:
            if len(self._sessions) >= self._max_sessions:
                self._cleanup_expired()
                if len(self._sessions) >= self._max_sessions:
                    raise RuntimeError(f"Max sessions limit reached: {self._max_sessions}")
            
            config = config or SessionConfig()
            
            session = Session(
                session_id=f"sess_{uuid.uuid4().hex[:16]}",
                trace_id=generate_trace_id(),
                client_id=client_id,
                config=config,
                status=SessionStatus.ACTIVE,
                metadata=metadata or {},
            )
            
            self._sessions[session.session_id] = session
            
            metrics.track(
                "session", "session_created",
                dimensions={"client_id": client_id},
            )
            
            logger.info("Session created", session_id=session.session_id, client_id=client_id)
            
            return session
    
    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired():
                session.status = SessionStatus.EXPIRED
            return session
    
    def get_active(self, session_id: str) -> Optional[Session]:
        """获取活跃会话"""
        session = self.get(session_id)
        if session and session.is_active():
            return session
        return None
    
    def close(self, session_id: str) -> Optional[Session]:
        """关闭会话"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            
            session.close()
            
            duration_ms = int(
                (session.updated_at - session.created_at).total_seconds() * 1000
            )
            
            metrics.track(
                "session", "session_closed",
                dimensions={"client_id": session.client_id},
                duration_ms=duration_ms,
                metrics={"tasks_count": session.stats.tasks_count}
            )
            
            logger.info("Session closed", session_id=session_id, duration_ms=duration_ms)
            
            return session
    
    def delete(self, session_id: str) -> bool:
        """删除会话"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def list(
        self,
        client_id: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> List[Session]:
        """列出会话"""
        with self._lock:
            sessions = list(self._sessions.values())
            
            if client_id:
                sessions = [s for s in sessions if s.client_id == client_id]
            if status:
                sessions = [s for s in sessions if s.status == status]
            
            return sessions
    
    def count(self) -> int:
        """获取会话数量"""
        with self._lock:
            return len(self._sessions)
    
    def _cleanup_expired(self) -> int:
        """清理过期会话"""
        expired_ids = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired() or session.status == SessionStatus.CLOSED:
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            del self._sessions[session_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
        
        return len(expired_ids)
    
    async def _cleanup_loop(self) -> None:
        """定期清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                with self._lock:
                    self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup error", exc=e)


# 全局单例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
