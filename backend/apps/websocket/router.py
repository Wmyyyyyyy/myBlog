import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.security import decode_token
from apps.websocket.manager import manager

router = APIRouter()

CLOSE_CODE_TOKEN_ERROR = 4001
CLOSE_CODE_BANNED = 4002
CLOSE_CODE_SERVER_ERROR = 4003


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """WebSocket 连接入口"""
    # 1. 验证 token
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=CLOSE_CODE_TOKEN_ERROR)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=CLOSE_CODE_TOKEN_ERROR)
        return

    # 2. 注册连接
    await manager.connect(websocket, int(user_id))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                await manager.heartbeat(websocket, int(user_id))
            # 忽略其他消息类型

    except WebSocketDisconnect:
        await manager.disconnect(websocket, int(user_id))
    except Exception:
        await manager.disconnect(websocket, int(user_id))