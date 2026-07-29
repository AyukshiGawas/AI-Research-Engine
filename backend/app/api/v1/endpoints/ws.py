from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
