import asyncio
import websockets
import json
import cv2
import numpy as np


async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Conectado al WebSocket")
        # Envía la URL del video al servidor
        await websocket.send("https://www.youtube.com/watch?v=NYYwT_7WFlc&ab_channel=Carspottingmrgold")

        # Recibe frames desde el servidor
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                frame_bytes = data.get("frame", None)

                if frame_bytes:
                    # Decodificar la imagen
                    np_arr = np.frombuffer(bytes.fromhex(frame_bytes), dtype=np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                    if frame is not None:
                        cv2.imshow("Detecciones", frame)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break

                print(f"Motocicletas detectadas: {data.get('motorcycles', 0)}")
                print(f"Cascos detectados: {data.get('helmets', 0)}")
            except websockets.exceptions.ConnectionClosed:
                print("Conexión cerrada con el servidor.")
                break
            except json.JSONDecodeError:
                print("Error al decodificar la respuesta.")

        cv2.destroyAllWindows()


asyncio.run(test_websocket())
