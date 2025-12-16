"""
Omni-Agent gRPC Server
"""
import asyncio
from concurrent import futures
from typing import Optional

import grpc

from ...infra import get_logger

logger = get_logger(__name__)


class GrpcServer:
    """gRPC 服务器"""
    
    def __init__(self, port: int = 50051, max_workers: int = 10):
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[grpc.aio.Server] = None
    
    async def start(self):
        """启动 gRPC 服务器"""
        from .generated import omni_agent_pb2_grpc
        from .servicer import OmniAgentServicer
        
        self.server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            options=[
                ('grpc.max_send_message_length', 10 * 1024 * 1024),  # 10MB
                ('grpc.max_receive_message_length', 10 * 1024 * 1024),
            ]
        )
        
        omni_agent_pb2_grpc.add_OmniAgentServiceServicer_to_server(
            OmniAgentServicer(), self.server
        )
        
        self.server.add_insecure_port(f'[::]:{self.port}')
        await self.server.start()
        logger.info(f"gRPC server started on port {self.port}")
    
    async def stop(self):
        """停止 gRPC 服务器"""
        if self.server:
            await self.server.stop(grace=5)
            logger.info("gRPC server stopped")
    
    async def wait_for_termination(self):
        """等待服务器终止"""
        if self.server:
            await self.server.wait_for_termination()


async def serve(port: int = 50051):
    """启动 gRPC 服务（便捷函数）"""
    server = GrpcServer(port=port)
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())
