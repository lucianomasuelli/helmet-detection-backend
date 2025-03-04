from fastapi import FastAPI, WebSocket
import asyncio
import websockets
import subprocess

app = FastAPI()

# Iniciar detector.py como subproceso
detector_process = subprocess.Popen(["python", "detector.py"])


@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI para detección de motocicletas y cascos"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Recibe la URL del video desde el cliente
            video_url = await websocket.receive_text()

            # Conectar con detector.py mediante WebSockets
            async with websockets.connect("ws://localhost:8765") as detector_ws:
                await detector_ws.send(video_url)

                # Recibir y reenviar detecciones
                while True:
                    detection_data = await detector_ws.recv()
                    print("Detección recibida y enviada al frontend:", detection_data)
                    await websocket.send_text(detection_data)

    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        print("Conexión cerrada")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
