import asyncio
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
      await websocket.send_text(self._to_html('Success:', 'success', message))

  async def warning(self, message: str, user_id: str):
    websocket = self._get_connection(user_id)
    if websocket:
      await websocket.send_text(self._to_html('Warning:', 'warning', message))

  async def error(self, message: str, user_id: str):
    websocket = self.active_connections[user_id]
    if websocket:
      await websocket.send_text(self._to_html('Error:', 'danger', message))

  async def broadcast(self, message: str):
    for user, connection in self.active_connections.items():
      await self.warning(message, user)

  # def success_sync(self, message: str, user_id: str):
  #   websocket = self._get_connection(user_id)
  #   if websocket:
  #     text = self._to_html('Success:', 'success', message)
  #     self._sync_send_text(websocket, text)

  # def error_sync(self, message: str, user_id: str):
  #   websocket = self._get_connection(user_id)
  #   if websocket:
  #     text = self._to_html('Error:', 'danger', message)
  #     self._sync_send_text(websocket, text)

  # def _sync_send_text(self, websocket: WebSocket, message: str):
  #   #notice: socket send is originally async. We have to change it to syncronous code - 
  #   loop = asyncio.new_event_loop()
  #   asyncio.set_event_loop(loop)
  #   websocket.send_text
  #   loop.run_until_complete(websocket.send_text(message))

  def _get_connection(self, user_id: str) -> WebSocket:
    if user_id in self.active_connections:
      return self.active_connections[user_id]
    else:
      application_logger.error(f"No websocket found for user with id '{user_id}'\nActive websockets: {self.active_connections}")
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