from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import json
import sqlite3
import os

# Crear la aplicación FastAPI
app = FastAPI(title="Robot Sensor Dashboard")

# Configurar directorios para templates y archivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelo para los datos de los sensores
class SensorData(BaseModel):
    device_id: str
    gas: int
    gas_alert: bool
    temperature: float
    humidity: float

# Clase para gestionar WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.esp8266_connection = None
        self.last_sensor_data = {}
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('sensors.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp DATETIME,
            gas INTEGER,
            gas_alert BOOLEAN,
            temperature REAL,
            humidity REAL
        )
        ''')
        conn.commit()
        conn.close()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id == "esp8266":
            self.esp8266_connection = websocket
            print("ESP8266 conectado")
        else:
            self.active_connections.append(websocket)
            print(f"Dashboard cliente conectado. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id == "esp8266" and self.esp8266_connection == websocket:
            self.esp8266_connection = None
            print("ESP8266 desconectado")
        else:
            self.active_connections.remove(websocket)
            print(f"Dashboard cliente desconectado. Restantes: {len(self.active_connections)}")
    
    async def send_command_to_esp8266(self, command: str):
        if self.esp8266_connection:
            await self.esp8266_connection.send_text(json.dumps({"action": command}))
            print(f"Comando enviado al ESP8266: {command}")
            return True
        print("No se pudo enviar comando: ESP8266 no conectado")
        return False
    
    async def broadcast_sensor_data(self, data: dict):
        # Guardar en la base de datos
        conn = sqlite3.connect('sensors.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_readings (device_id, timestamp, gas, gas_alert, temperature, humidity) VALUES (?, ?, ?, ?, ?, ?)",
            (data["device_id"], datetime.now().isoformat(), data["gas"], data["gas_alert"], data["temperature"], data["humidity"])
        )
        conn.commit()
        conn.close()
        
        # Actualizar datos más recientes
        data["timestamp"] = datetime.now().isoformat()
        self.last_sensor_data = data
        
        # Enviar a todos los clientes conectados
        for connection in self.active_connections:
            await connection.send_text(json.dumps(data))
            
    def get_historic_data(self):
        """Obtener datos históricos de las últimas 24 horas para gráficos"""
        conn = sqlite3.connect('sensors.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, gas, temperature, humidity FROM sensor_readings WHERE timestamp > datetime('now', '-1 day') ORDER BY timestamp"
        )
        history = cursor.fetchall()
        conn.close()
        
        # Preparar datos para gráficos
        timestamps = [row[0] for row in history]
        gas_data = [row[1] for row in history]
        temp_data = [row[2] for row in history]
        humidity_data = [row[3] for row in history]
        
        return {
            "timestamps": timestamps,
            "gas_data": gas_data,
            "temp_data": temp_data,
            "humidity_data": humidity_data
        }

# Instancia del gestor de conexiones
manager = ConnectionManager()

# WebSocket para ESP8266
@app.websocket("/ws/esp8266")
async def websocket_esp8266(websocket: WebSocket):
    await manager.connect(websocket, "esp8266")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                sensor_data = json.loads(data)
                await manager.broadcast_sensor_data(sensor_data)
            except json.JSONDecodeError:
                print(f"Error decodificando JSON del ESP8266: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, "esp8266")

# WebSocket para clientes web
@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect(websocket, "dashboard")
    # Enviar los últimos datos inmediatamente después de conexión
    if manager.last_sensor_data:
        await websocket.send_text(json.dumps(manager.last_sensor_data))
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                # Enviar comando al ESP8266
                success = await manager.send_command_to_esp8266(command["action"])
                # Confirmar al cliente
                await websocket.send_text(json.dumps({"status": "sent" if success else "failed"}))
            except json.JSONDecodeError:
                print(f"Error decodificando JSON del cliente: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")

# Ruta para la página principal
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Obtener datos históricos
    historic_data = manager.get_historic_data()
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "readings": manager.last_sensor_data,
            "timestamps": historic_data["timestamps"],
            "gas_data": historic_data["gas_data"],
            "temp_data": historic_data["temp_data"],
            "humidity_data": historic_data["humidity_data"]
        }
    )

# Si este archivo se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)