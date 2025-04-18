from fastapi import WebSocket
from d4k_ms_base.logger import application_logger


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            self.active_connections.pop(user_id)

    async def success(self, message: str, user_id: str):
        websocket = self._get_connection(user_id)
        if websocket:
            await websocket.send_text(self._to_html("Success:", "success", message))

    async def warning(self, message: str, user_id: str):
        websocket = self._get_connection(user_id)
        if websocket:
            await websocket.send_text(self._to_html("Warning:", "warning", message))

    async def error(self, message: str, user_id: str):
        websocket = self.active_connections[user_id]
        if websocket:
            await websocket.send_text(self._to_html("Error:", "danger", message))

    async def broadcast(self, message: str):
        for user, connection in self.active_connections.items():
            await self.warning(message, user)

    def _get_connection(self, user_id: str) -> WebSocket:
        if user_id in self.active_connections:
            return self.active_connections[user_id]
        else:
            application_logger.error(
                f"No websocket found for user with id '{user_id}'\nActive websockets: {self.active_connections}"
            )
            return None

    def _to_html(self, prefix: str, status: str, message: str):
        return f"""
      <div id="alert_ws_div" hx-swap-oob="true">
        <div class="alert alert-dismissible alert-{status} mt-3">
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          <strong>{prefix}</strong>&nbsp;{message}
        </div>
      </div> 
    """


connection_manager = ConnectionManager()
