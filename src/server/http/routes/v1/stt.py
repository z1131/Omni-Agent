"""
STT (语音识别) API
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Header, Request, UploadFile, File
from pydantic import BaseModel

from ...response import success, error, session_not_found, ErrorCode
from .....orchestrator import get_session_manager
from .....perception.stt import SttRegistry, SttConfig
from .....infra import get_logger, log_context, generate_trace_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("/stt/recognize")
async def recognize_speech(
    request: Request,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID"),
    x_audio_format: str = Header("pcm", alias="X-Audio-Format"),
    x_sample_rate: int = Header(16000, alias="X-Sample-Rate")
):
    """单次语音识别
    
    请求体为二进制音频数据 (PCM 16bit)
    """
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=x_session_id):
        try:
            # 读取音频数据
            audio_data = await request.body()
            
            if not audio_data:
                return error(
                    ErrorCode.INVALID_PARAM,
                    "Empty audio data",
                    trace_id=trace_id
                ).to_json_response()
            
            # 验证会话
            session_manager = get_session_manager()
            session = session_manager.get_active(x_session_id)
            if not session:
                return session_not_found(x_session_id, trace_id).to_json_response()
            
            # 创建 STT 服务
            stt_service = SttRegistry.get_service(session.config.stt.provider)
            stt_config = SttConfig(
                model=session.config.stt.model,
                language=session.config.stt.language,
                sample_rate=x_sample_rate,
                enable_punctuation=session.config.stt.enable_punctuation,
            )
            
            # 使用 Future 收集结果
            result_future: asyncio.Future = asyncio.Future()
            
            def on_final(r):
                if not result_future.done():
                    result_future.set_result(r)
            
            def on_error(e):
                if not result_future.done():
                    result_future.set_exception(e)
            
            stt_service.on_final(on_final)
            stt_service.on_error(on_error)
            
            # 调用识别
            await stt_service.start_session(x_session_id, stt_config)
            await stt_service.send_audio(audio_data)
            await stt_service.stop_session()
            
            result = await asyncio.wait_for(result_future, timeout=10.0)
            session.stats.stt_requests += 1
            
            return success(
                data={
                    "text": result.text,
                    "confidence": result.confidence,
                    "duration_ms": result.end_time_ms - result.start_time_ms
                },
                trace_id=trace_id
            ).to_json_response()
            
        except ValueError as e:
            if "not found" in str(e).lower():
                return session_not_found(x_session_id, trace_id).to_json_response()
            return error(
                ErrorCode.INVALID_PARAM,
                str(e),
                trace_id=trace_id
            ).to_json_response()
        except TimeoutError:
            return error(
                ErrorCode.TIMEOUT,
                "STT recognition timeout",
                trace_id=trace_id
            ).to_json_response()
        except Exception as e:
            logger.error("STT error", exc=e)
            return error(
                ErrorCode.STT_ERROR,
                str(e),
                trace_id=trace_id
            ).to_json_response()


@router.post("/stt/recognize/file")
async def recognize_speech_file(
    file: UploadFile = File(...),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """从文件识别语音
    
    支持上传音频文件
    """
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=x_session_id):
        try:
            # 读取文件
            audio_data = await file.read()
            
            if not audio_data:
                return error(
                    ErrorCode.INVALID_PARAM,
                    "Empty audio file",
                    trace_id=trace_id
                ).to_json_response()
            
            # 验证会话
            session_manager = get_session_manager()
            session = session_manager.get_active(x_session_id)
            if not session:
                return session_not_found(x_session_id, trace_id).to_json_response()
            
            # 创建 STT 服务
            stt_service = SttRegistry.get_service(session.config.stt.provider)
            stt_config = SttConfig(
                model=session.config.stt.model,
                language=session.config.stt.language,
                sample_rate=session.config.stt.sample_rate,
                enable_punctuation=session.config.stt.enable_punctuation,
            )
            
            # 使用 Future 收集结果
            result_future: asyncio.Future = asyncio.Future()
            
            def on_final(r):
                if not result_future.done():
                    result_future.set_result(r)
            
            def on_error(e):
                if not result_future.done():
                    result_future.set_exception(e)
            
            stt_service.on_final(on_final)
            stt_service.on_error(on_error)
            
            # 调用识别
            await stt_service.start_session(x_session_id, stt_config)
            await stt_service.send_audio(audio_data)
            await stt_service.stop_session()
            
            result = await asyncio.wait_for(result_future, timeout=10.0)
            session.stats.stt_requests += 1
            
            return success(
                data={
                    "text": result.text,
                    "confidence": result.confidence,
                    "duration_ms": result.end_time_ms - result.start_time_ms,
                    "filename": file.filename
                },
                trace_id=trace_id
            ).to_json_response()
            
        except ValueError as e:
            if "not found" in str(e).lower():
                return session_not_found(x_session_id, trace_id).to_json_response()
            return error(
                ErrorCode.INVALID_PARAM,
                str(e),
                trace_id=trace_id
            ).to_json_response()
        except TimeoutError:
            return error(
                ErrorCode.TIMEOUT,
                "STT recognition timeout",
                trace_id=trace_id
            ).to_json_response()
        except Exception as e:
            logger.error("STT file error", exc=e)
            return error(
                ErrorCode.STT_ERROR,
                str(e),
                trace_id=trace_id
            ).to_json_response()
