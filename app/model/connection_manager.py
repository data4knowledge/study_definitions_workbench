from fastapi import WebSocket
from d4kms_generic import application_logger

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
      #print(f"SUCCESS:")
      text = f"""
        <div id="alert_ws_div" hx-swap-oob="true">
          <div class="alert alert-dismissible alert-success mt-3">
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            <strong>Success:</strong>&nbsp;{message}
          </div>
        </div> 
      """
      await websocket.send_text(text)

  async def warning(self, message: str, user_id: str):
    websocket = self._get_connection(user_id)
    if websocket:
      text = f"""
        <div id="alert_ws_div" hx-swap-oob="true">
          <div class="alert alert-dismissible alert-warning mt-3">
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            <strong>Warning:</strong>&nbsp;{message}
          </div>
        </div> 
      """
      await websocket.send_text(text)

  async def error(self, message: str, user_id: str):
    websocket = self.active_connections[user_id]
    if websocket:
      text = f"""
        <div id="alert_ws_div" hx-swap-oob="true">
          <div class="alert alert-dismissible alert-danger mt-3">
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            <strong>Error:</strong>&nbsp;{message}
          </div>
        </div> 
      """
      await websocket.send_text(text)

  async def broadcast(self, message: str):
    for user, connection in self.active_connections.items():
      await self.warning(message, user)

  def _get_connection(self, user_id: str) -> WebSocket:
    if user_id in self.active_connections:
      return self.active_connections[user_id]
    else:
      application_logger.error(f"No websocket found for user with id '{user_id}'")
      print (f"Active websockets: {self.active_connections}")
      return None
  
connection_manager = ConnectionManager()