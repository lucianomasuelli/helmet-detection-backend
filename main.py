from fastapi import FastAPI, WebSocket
import subprocess
import asyncio

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI para detección de motocicletas y cascos"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Gets the video URL from the client
            video_url = await websocket.receive_text()

            # Start the detector process
            process = subprocess.Popen(["python", "detector.py", video_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            print("Detector iniciado")
            # Send detections to the client
            while True:
                output = process.stdout.readline()
                if output:
                    print("Detección enviada:", output.strip())
                    await websocket.send_text(output.strip())
                elif process.poll() is not None:
                    break

    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        process.terminate()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
