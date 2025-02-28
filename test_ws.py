import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Conectado al WebSocket")
        # Sends url to the server
        await websocket.send("https://www.youtube.com/watch?v=NYYwT_7WFlc&ab_channel=Carspottingmrgold")

        # Recibe detections from the server
        while True:
            response = await websocket.recv()
            print("Detección recibida:", response)

asyncio.run(test_websocket())
