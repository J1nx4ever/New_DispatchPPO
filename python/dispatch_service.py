from __future__ import annotations

from concurrent import futures
from typing import Optional

import grpc

from .dispatch_bridge import DispatchCallbackBridge, ProtocolError
from .generated import dispatch_pb2_grpc


class DispatchService(dispatch_pb2_grpc.DispatchServiceServicer):
    def __init__(self, bridge: DispatchCallbackBridge) -> None:
        self.bridge = bridge

    def GetNextDestination(self, request, context):
        try:
            timeout: Optional[float] = context.time_remaining()
            return self.bridge.submit_callback(request, timeout=timeout)
        except ProtocolError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except TimeoutError as exc:
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, str(exc))
        except RuntimeError as exc:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))


def create_server(
    bridge: DispatchCallbackBridge,
    host: str = "127.0.0.1",
    port: int = 50051,
    max_workers: int = 8,
) -> grpc.Server:
    if max_workers < 2:
        raise ValueError("max_workers must be >= 2 for blocking callbacks")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    dispatch_pb2_grpc.add_DispatchServiceServicer_to_server(
        DispatchService(bridge), server
    )
    if server.add_insecure_port(f"{host}:{port}") == 0:
        raise RuntimeError(f"failed to bind gRPC server to {host}:{port}")
    return server
