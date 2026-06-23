from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, company_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(company_id, []).append(websocket)
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

    async def broadcast(self, company_id: str, message: dict):
        connections = self.active_connections.get(company_id, [])

        for connection in connections:
            await connection.send_json(message)

manager = ConnectionManager()
