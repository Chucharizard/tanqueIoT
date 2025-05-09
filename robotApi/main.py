from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
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

# Base de datos SQLite para almacenar los datos históricos
def init_db():
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

# Almacenar los últimos datos recibidos (para acceso rápido)
last_readings = {}

@app.on_event("startup")
async def startup_event():
    init_db()

# Ruta para recibir datos del ESP8266
@app.post("/api/sensors")
async def receive_sensor_data(data: SensorData):
    # Actualizar los últimos datos
    last_readings[data.device_id] = {
        "timestamp": datetime.now(),
        "gas": data.gas,
        "gas_alert": data.gas_alert,
        "temperature": data.temperature,
        "humidity": data.humidity
    }
    
    # Guardar en la base de datos
    conn = sqlite3.connect('sensors.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sensor_readings (device_id, timestamp, gas, gas_alert, temperature, humidity) VALUES (?, ?, ?, ?, ?, ?)",
        (data.device_id, datetime.now(), data.gas, data.gas_alert, data.temperature, data.humidity)
    )
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Data received"}

# Ruta para la página principal
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Obtener últimas 24 horas de datos para gráficos
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
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "readings": last_readings,
            "timestamps": timestamps,
            "gas_data": gas_data,
            "temp_data": temp_data,
            "humidity_data": humidity_data
        }
    )

# Si este archivo se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)