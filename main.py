from fastapi import FastAPI, WebSocket
import subprocess

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI para detección de motocicletas y cascos"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Iniciar el script de detección en otro proceso
    process = subprocess.Popen(["python", "detector.py"])

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Mensaje recibido: {data}")
    except:
        process.terminate()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
