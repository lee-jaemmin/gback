import asyncio
from time import perf_counter

from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, company_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(company_id, []).append(websocket)
        print(
            f"[WS connect] company_id={company_id} "
            f"count={len(self.active_connections[company_id])}"
        )
        # setdefault: company_id 없으면 만들어서 리스트 꺼내줌. 있으면 기존 리스트 꺼내줌
        # 리스트: 웹소켓 리스트: 유저들의 웹소켓 리스트 (통로)
    
    def disconnect(self, company_id: str, websocket: WebSocket):
        connections = self.active_connections.get(company_id, [])
        # company_id있으면 그 리스트 반환
        # 없으면 빈 리스트 반환

        if websocket in connections:
            connections.remove(websocket)
        
        if not connections:
            self.active_connections.pop(company_id, None)
        # key인 company_id 삭제 후 그 value 반환
        # key 없으면 None 반환
        print(f"[WS disconnect] company_id={company_id} count={len(connections)}")

    async def broadcast(self, company_id: str, message: dict):
        started_at = perf_counter()
        connections = self.active_connections.get(company_id, [])

        async def send(connection: WebSocket):
            try:
                await asyncio.wait_for(connection.send_json(message), timeout=2)
                return None
            except Exception:
                return connection

        results = await asyncio.gather(
            *(send(connection) for connection in list(connections))
        )
        stale_connections = [
            connection for connection in results if connection is not None
        ]

        for connection in stale_connections:
            self.disconnect(company_id, connection)

        elapsed_ms = (perf_counter() - started_at) * 1000
        print(
            f"[WS broadcast] company_id={company_id} "
            f"type={message.get('type')} "
            f"connections={len(connections)} "
            f"failed={len(stale_connections)} "
            f"elapsed_ms={elapsed_ms:.1f}"
        )

manager = ConnectionManager()
